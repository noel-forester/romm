from datetime import datetime, timezone

from decorators.auth import protected_route
from endpoints.responses import MessageResponse
from endpoints.responses.assets import StateSchema, UploadedStatesResponse
from exceptions.endpoint_exceptions import RomNotFoundInDatabaseException
from fastapi import File, HTTPException, Request, UploadFile, status
from handler.auth.constants import Scope
from handler.database import db_rom_handler, db_screenshot_handler, db_state_handler
from handler.filesystem import fs_asset_handler
from handler.scan_handler import scan_state
from logger.logger import log
from utils.router import APIRouter

router = APIRouter(
    prefix="/states",
    tags=["states"],
)


@protected_route(router.post, "", [Scope.ASSETS_WRITE])
def add_states(
    request: Request,
    rom_id: int,
    states: list[UploadFile] = File(...),  # noqa: B008
    emulator: str | None = None,
) -> UploadedStatesResponse:
    rom = db_rom_handler.get_rom(rom_id)
    if not rom:
        raise RomNotFoundInDatabaseException(rom_id)

    current_user = request.user
    log.info(f"Uploading states to {rom.name}")

    states_path = fs_asset_handler.build_states_file_path(
        user=request.user, platform_fs_slug=rom.platform.fs_slug, emulator=emulator
    )

    for state in states:
        if not state.filename:
            log.warning("Skipping file with no filename")
            continue

        fs_asset_handler.write_file(file=state, path=states_path)

        # Scan or update state
        scanned_state = scan_state(
            file_name=state.filename,
            user=request.user,
            platform_fs_slug=rom.platform.fs_slug,
            emulator=emulator,
        )
        db_state = db_state_handler.get_state_by_filename(
            rom_id=rom.id, user_id=current_user.id, file_name=state.filename
        )
        if db_state:
            db_state_handler.update_state(
                db_state.id, {"file_size_bytes": scanned_state.file_size_bytes}
            )
            continue

        scanned_state.rom_id = rom.id
        scanned_state.user_id = current_user.id
        scanned_state.emulator = emulator
        db_state_handler.add_state(scanned_state)

        # Set the last played time for the current user
        rom_user = db_rom_handler.get_rom_user(rom.id, current_user.id)
        if not rom_user:
            rom_user = db_rom_handler.add_rom_user(rom.id, current_user.id)
        db_rom_handler.update_rom_user(
            rom_user.id, {"last_played": datetime.now(timezone.utc)}
        )

    rom = db_rom_handler.get_rom(rom_id)
    if not rom:
        raise RomNotFoundInDatabaseException(rom_id)

    return {
        "uploaded": len(states),
        "states": [
            StateSchema.model_validate(s)
            for s in rom.states
            if s.user_id == current_user.id
        ],
    }


# @protected_route(router.get, "", [Scope.ASSETS_READ])
# def get_states(request: Request) -> MessageResponse:
#     pass


# @protected_route(router.get, "/{id}", [Scope.ASSETS_READ])
# def get_state(request: Request, id: int) -> MessageResponse:
#     pass


@protected_route(router.put, "/{id}", [Scope.ASSETS_WRITE])
async def update_state(request: Request, id: int) -> StateSchema:
    data = await request.form()

    db_state = db_state_handler.get_state(id)
    if not db_state:
        error = f"Save with ID {id} not found"
        log.error(error)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)

    if db_state.user_id != request.user.id:
        error = "You are not authorized to update this save state"
        log.error(error)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error)

    if "file" in data:
        file: UploadFile = data["file"]  # type: ignore
        fs_asset_handler.write_file(file=file, path=db_state.file_path)
        db_state_handler.update_state(db_state.id, {"file_size_bytes": file.size})

    # Set the last played time for the current user
    current_user = request.user
    rom_user = db_rom_handler.get_rom_user(db_state.rom_id, current_user.id)
    if not rom_user:
        rom_user = db_rom_handler.add_rom_user(db_state.rom_id, current_user.id)
    db_rom_handler.update_rom_user(
        rom_user.id, {"last_played": datetime.now(timezone.utc)}
    )

    db_state = db_state_handler.get_state(id)
    return StateSchema.model_validate(db_state)


@protected_route(router.post, "/delete", [Scope.ASSETS_WRITE])
async def delete_states(request: Request) -> MessageResponse:
    data: dict = await request.json()
    state_ids: list = data["states"]
    delete_from_fs: list = data["delete_from_fs"]

    if not state_ids:
        error = "No states were provided"
        log.error(error)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    for state_id in state_ids:
        state = db_state_handler.get_state(state_id)
        if not state:
            error = f"Save with ID {state_id} not found"
            log.error(error)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)

        if state.user_id != request.user.id:
            error = "You are not authorized to delete this save state"
            log.error(error)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error)

        db_state_handler.delete_state(state_id)

        if state_id in delete_from_fs:
            log.info(f"Deleting {state.file_name} from filesystem")
            try:
                fs_asset_handler.remove_file(
                    file_name=state.file_name, file_path=state.file_path
                )
            except FileNotFoundError as exc:
                error = f"Save file {state.file_name} not found for platform {state.rom.platform_slug}"
                log.error(error)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=error
                ) from exc

        if state.screenshot:
            db_screenshot_handler.delete_screenshot(state.screenshot.id)

            if delete_from_fs:
                try:
                    fs_asset_handler.remove_file(
                        file_name=state.screenshot.file_name,
                        file_path=state.screenshot.file_path,
                    )
                except FileNotFoundError:
                    error = f"Screenshot file {state.screenshot.file_name} not found for state {state.file_name}"
                    log.error(error)

    return {"msg": f"Successfully deleted {len(state_ids)} states"}
