from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from handler.scan_handler import MetadataSource, ScanType
from tasks.scan_library import ScanLibraryTask, scan_library_task


class TestScanLibraryTask:
    @pytest.fixture
    def task(self):
        return ScanLibraryTask()

    def test_init(self, task):
        """Test task initialization"""
        assert task.func == "tasks.scan_library.scan_library_task.run"
        assert task.description == "library scan"

    @patch("tasks.scan_library.ENABLE_SCHEDULED_RESCAN", True)
    @patch("tasks.scan_library.scan_platforms")
    @patch("tasks.scan_library.log")
    async def test_run_enabled(self, mock_log, mock_scan_platforms, task):
        """Test run when scheduled rescan is enabled"""
        mock_scan_platforms.return_value = AsyncMock()

        await task.run()

        mock_log.info.assert_any_call("Scheduled library scan started...")
        mock_scan_platforms.assert_called_once_with(
            [], scan_type=ScanType.UNIDENTIFIED, metadata_sources=[MetadataSource.LB]
        )
        mock_log.info.assert_any_call("Scheduled library scan done")

    @patch("tasks.scan_library.ENABLE_SCHEDULED_RESCAN", False)
    @patch("tasks.scan_library.scan_platforms")
    @patch("tasks.scan_library.log")
    async def test_run_disabled(self, mock_log, mock_scan_platforms, task):
        """Test run when scheduled rescan is disabled"""
        task.unschedule = MagicMock()

        await task.run()

        mock_log.info.assert_called_once_with(
            "Scheduled library scan not enabled, unscheduling..."
        )
        task.unschedule.assert_called_once()
        mock_scan_platforms.assert_not_called()

    def test_task_instance(self):
        """Test that the module-level task instance is created correctly"""
        assert isinstance(scan_library_task, ScanLibraryTask)
        assert scan_library_task.func == "tasks.scan_library.scan_library_task.run"
