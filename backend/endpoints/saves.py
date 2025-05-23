from datetime import datetime, timezone

from decorators.auth import protected_route
from endpoints.responses import MessageResponse
from endpoints.responses.assets import SaveSchema, UploadedSavesResponse
from exceptions.endpoint_exceptions import RomNotFoundInDatabaseException
from fastapi import File, HTTPException, Request, UploadFile, status
from handler.auth.constants import Scope
from handler.database import db_rom_handler, db_save_handler, db_screenshot_handler
from handler.filesystem import fs_asset_handler
from handler.scan_handler import scan_save
from logger.logger import log
from utils.router import APIRouter

router = APIRouter(
    prefix="/saves",
    tags=["saves"],
)


@protected_route(router.post, "", [Scope.ASSETS_WRITE])
def add_saves(
    request: Request,
    rom_id: int,
    saves: list[UploadFile] = File(...),  # noqa: B008
    emulator: str | None = None,
) -> UploadedSavesResponse:
    rom = db_rom_handler.get_rom(rom_id)
    if not rom:
        raise RomNotFoundInDatabaseException(rom_id)

    current_user = request.user
    log.info(f"Uploading saves to {rom.name}")

    saves_path = fs_asset_handler.build_saves_file_path(
        user=request.user, platform_fs_slug=rom.platform.fs_slug, emulator=emulator
    )

    for save in saves:
        if not save.filename:
            log.error("Save file has no filename")
            continue

        fs_asset_handler.write_file(file=save, path=saves_path)

        # Scan or update save
        scanned_save = scan_save(
            file_name=save.filename,
            user=request.user,
            platform_fs_slug=rom.platform.fs_slug,
            emulator=emulator,
        )
        db_save = db_save_handler.get_save_by_filename(
            rom_id=rom.id, user_id=current_user.id, file_name=save.filename
        )
        if db_save:
            db_save_handler.update_save(
                db_save.id, {"file_size_bytes": scanned_save.file_size_bytes}
            )
            continue

        scanned_save.rom_id = rom.id
        scanned_save.user_id = current_user.id
        scanned_save.emulator = emulator
        db_save_handler.add_save(scanned_save)

        # Set the last played time for the current user
        rom_user = db_rom_handler.get_rom_user(rom.id, current_user.id)
        if not rom_user:
            rom_user = db_rom_handler.add_rom_user(rom.id, current_user.id)
        db_rom_handler.update_rom_user(
            rom_user.id, {"last_played": datetime.now(timezone.utc)}
        )

    # Refetch the rom to get updated saves
    rom = db_rom_handler.get_rom(rom_id)
    if not rom:
        raise RomNotFoundInDatabaseException(rom_id)

    return {
        "uploaded": len(saves),
        "saves": [
            SaveSchema.model_validate(s)
            for s in rom.saves
            if s.user_id == current_user.id
        ],
    }


# @protected_route(router.get, "", [Scope.ASSETS_READ])
# def get_saves(request: Request) -> MessageResponse:
#     pass


# @protected_route(router.get, "/{id}", [Scope.ASSETS_READ])
# def get_save(request: Request, id: int) -> MessageResponse:
#     pass


@protected_route(router.put, "/{id}", [Scope.ASSETS_WRITE])
async def update_save(request: Request, id: int) -> SaveSchema:
    data = await request.form()

    db_save = db_save_handler.get_save(id)
    if not db_save:
        error = f"Save with ID {id} not found"
        log.error(error)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)

    if db_save.user_id != request.user.id:
        error = "You are not authorized to update this save"
        log.error(error)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error)

    if "file" in data:
        file: UploadFile = data["file"]  # type: ignore
        fs_asset_handler.write_file(file=file, path=db_save.file_path)
        db_save_handler.update_save(db_save.id, {"file_size_bytes": file.size})

    # Set the last played time for the current user
    current_user = request.user
    rom_user = db_rom_handler.get_rom_user(db_save.rom_id, current_user.id)
    if not rom_user:
        rom_user = db_rom_handler.add_rom_user(db_save.rom_id, current_user.id)
    db_rom_handler.update_rom_user(
        rom_user.id, {"last_played": datetime.now(timezone.utc)}
    )

    # Refetch the save to get updated fields
    db_save = db_save_handler.get_save(id)
    return SaveSchema.model_validate(db_save)


@protected_route(router.post, "/delete", [Scope.ASSETS_WRITE])
async def delete_saves(request: Request) -> MessageResponse:
    data: dict = await request.json()
    save_ids: list = data["saves"]
    delete_from_fs: list = data["delete_from_fs"]

    if not save_ids:
        error = "No saves were provided"
        log.error(error)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    for save_id in save_ids:
        save = db_save_handler.get_save(save_id)
        if not save:
            error = f"Save with ID {save_id} not found"
            log.error(error)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)

        if save.user_id != request.user.id:
            error = "You are not authorized to delete this save"
            log.error(error)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error)

        db_save_handler.delete_save(save_id)

        if save_id in delete_from_fs:
            log.info(f"Deleting {save.file_name} from filesystem")

            try:
                fs_asset_handler.remove_file(
                    file_name=save.file_name, file_path=save.file_path
                )
            except FileNotFoundError as exc:
                error = f"Save file {save.file_name} not found for platform {save.rom.platform_slug}"
                log.error(error)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=error
                ) from exc

        if save.screenshot:
            db_screenshot_handler.delete_screenshot(save.screenshot.id)

            if delete_from_fs:
                try:
                    fs_asset_handler.remove_file(
                        file_name=save.screenshot.file_name,
                        file_path=save.screenshot.file_path,
                    )
                except FileNotFoundError:
                    error = f"Screenshot file {save.screenshot.file_name} not found for save {save.file_name}"
                    log.error(error)

    return {"msg": f"Successfully deleted {len(save_ids)} saves"}
