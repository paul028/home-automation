"""Unit tests for RecordingManager — ffmpeg process lifecycle and upload logic."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.recording_manager import RecordingManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def manager():
    """Create a fresh RecordingManager instance."""
    return RecordingManager()


# ---------------------------------------------------------------------------
# _get_folder_id (caching)
# ---------------------------------------------------------------------------


class TestGetFolderId:
    async def test_get_folder_id_FirstCall_QueriesDriveAndCaches(self, manager):
        # Arrange
        FOLDER_ID = "folder_abc"
        mock_gdrive = MagicMock()
        mock_gdrive.get_or_create_folder = MagicMock(return_value=FOLDER_ID)
        manager._gdrive = mock_gdrive

        # Act
        result = await manager._get_folder_id("Camera 1", "root_id")

        # Assert
        assert result == FOLDER_ID
        mock_gdrive.get_or_create_folder.assert_called_once()

    async def test_get_folder_id_SecondCall_ReturnsCachedValue(self, manager):
        # Arrange
        FOLDER_ID = "folder_abc"
        mock_gdrive = MagicMock()
        mock_gdrive.get_or_create_folder = MagicMock(return_value=FOLDER_ID)
        manager._gdrive = mock_gdrive

        # Act
        await manager._get_folder_id("Camera 1", "root_id")
        result = await manager._get_folder_id("Camera 1", "root_id")

        # Assert
        assert result == FOLDER_ID
        assert mock_gdrive.get_or_create_folder.call_count == 1

    async def test_get_folder_id_DifferentNames_QueriesDriveForEach(self, manager):
        # Arrange
        mock_gdrive = MagicMock()
        mock_gdrive.get_or_create_folder = MagicMock(side_effect=["id_a", "id_b"])
        manager._gdrive = mock_gdrive

        # Act
        result_a = await manager._get_folder_id("Camera A", "root_id")
        result_b = await manager._get_folder_id("Camera B", "root_id")

        # Assert
        assert result_a == "id_a"
        assert result_b == "id_b"
        assert mock_gdrive.get_or_create_folder.call_count == 2


# ---------------------------------------------------------------------------
# _upload_segment
# ---------------------------------------------------------------------------


class TestUploadSegment:
    async def test_upload_segment_ValidFile_UploadsToCorrectDrivePath(self, manager):
        # Arrange
        mock_gdrive = MagicMock()
        mock_gdrive.get_or_create_folder = MagicMock(side_effect=["cam_folder", "date_folder"])
        mock_gdrive.upload_file = MagicMock()
        manager._gdrive = mock_gdrive
        manager._camera_names = {1: "Front Yard"}
        mp4 = Path("/tmp/ha-recordings/1/2026-02-28_14-00-00.mp4")

        with patch("app.services.recording_manager.settings") as mock_settings:
            mock_settings.gdrive_folder_id = "root_id"

            # Act
            await manager._upload_segment(1, mp4)

            # Assert
            mock_gdrive.upload_file.assert_called_once_with(
                mp4, "date_folder", "14:00:00.mp4"
            )

    async def test_upload_segment_UnknownCameraId_UsesFallbackName(self, manager):
        # Arrange
        mock_gdrive = MagicMock()
        mock_gdrive.get_or_create_folder = MagicMock(side_effect=["cam_folder", "date_folder"])
        mock_gdrive.upload_file = MagicMock()
        manager._gdrive = mock_gdrive
        manager._camera_names = {}  # camera_id=99 not in cache
        mp4 = Path("/tmp/ha-recordings/99/2026-02-28_10-00-00.mp4")

        with patch("app.services.recording_manager.settings") as mock_settings:
            mock_settings.gdrive_folder_id = "root_id"

            # Act
            await manager._upload_segment(99, mp4)

            # Assert
            first_call = mock_gdrive.get_or_create_folder.call_args_list[0]
            assert first_call[0][0] == "camera_99"


# ---------------------------------------------------------------------------
# stop
# ---------------------------------------------------------------------------


class TestStop:
    async def test_stop_RunningProcesses_TerminatesAll(self, manager):
        # Arrange
        mock_proc = AsyncMock()
        mock_proc.pid = 12345
        mock_proc.terminate = MagicMock()
        mock_proc.wait = AsyncMock()
        manager._processes = {1: mock_proc}
        manager._running = True
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()
        manager._tasks = [mock_task]

        # Act
        await manager.stop()

        # Assert
        mock_proc.terminate.assert_called_once()
        assert manager._running is False

    async def test_stop_NoProcesses_CompletesCleanly(self, manager):
        # Arrange
        manager._running = True

        # Act
        await manager.stop()

        # Assert
        assert manager._running is False
        assert len(manager._processes) == 0
