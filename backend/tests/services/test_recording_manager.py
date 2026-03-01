"""Unit tests for RecordingManager — ffmpeg process lifecycle and upload logic."""

import asyncio
from pathlib import Path
from types import SimpleNamespace
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


def _make_camera(**overrides):
    """Build a lightweight camera-like object for manager tests."""
    defaults = {
        "id": 1,
        "name": "Test Camera",
        "ip_address": "192.168.1.50",
        "username": "admin",
        "password": "pass",
        "has_ptz": True,
        "has_recording": True,
        "recording_segment_seconds": None,
        "is_active": True,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# start — has_recording filtering & per-camera segment seconds
# ---------------------------------------------------------------------------


class TestStart:
    async def test_start_OnlyRecordingEnabled_SkipsCamerasWithRecordingDisabled(
        self, manager
    ):
        # Arrange
        cam_recording = _make_camera(id=1, name="Cam A", has_recording=True)
        cam_no_recording = _make_camera(id=2, name="Cam B", has_recording=False)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [cam_recording]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.recording_manager.async_session", return_value=mock_session), \
             patch("app.services.recording_manager.settings") as mock_settings, \
             patch.object(manager, "_start_camera", new_callable=AsyncMock) as mock_start, \
             patch.object(manager, "_upload_worker", new_callable=AsyncMock), \
             patch.object(manager, "_cleanup_worker", new_callable=AsyncMock):
            mock_settings.recordings_local_path = "/tmp/test-rec"
            mock_settings.gdrive_credentials_path = None
            mock_settings.gdrive_folder_id = None
            mock_settings.recording_segment_seconds = 300

            # Act
            await manager.start()

            # Assert — only camera with has_recording=True was started
            mock_start.assert_called_once_with(1)

    async def test_start_PerCameraSegment_StoresCustomDurationInCache(self, manager):
        # Arrange
        CUSTOM_SECONDS = 60
        cam = _make_camera(id=5, name="Custom Cam", recording_segment_seconds=CUSTOM_SECONDS)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [cam]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.recording_manager.async_session", return_value=mock_session), \
             patch("app.services.recording_manager.settings") as mock_settings, \
             patch.object(manager, "_start_camera", new_callable=AsyncMock), \
             patch.object(manager, "_upload_worker", new_callable=AsyncMock), \
             patch.object(manager, "_cleanup_worker", new_callable=AsyncMock):
            mock_settings.recordings_local_path = "/tmp/test-rec"
            mock_settings.gdrive_credentials_path = None
            mock_settings.gdrive_folder_id = None
            mock_settings.recording_segment_seconds = 300

            # Act
            await manager.start()

            # Assert
            assert manager._segment_seconds[5] == CUSTOM_SECONDS

    async def test_start_NullPerCameraSegment_FallsBackToGlobalInCache(self, manager):
        # Arrange
        GLOBAL_SECONDS = 300
        cam = _make_camera(id=3, name="Default Cam", recording_segment_seconds=None)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [cam]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.recording_manager.async_session", return_value=mock_session), \
             patch("app.services.recording_manager.settings") as mock_settings, \
             patch.object(manager, "_start_camera", new_callable=AsyncMock), \
             patch.object(manager, "_upload_worker", new_callable=AsyncMock), \
             patch.object(manager, "_cleanup_worker", new_callable=AsyncMock):
            mock_settings.recordings_local_path = "/tmp/test-rec"
            mock_settings.gdrive_credentials_path = None
            mock_settings.gdrive_folder_id = None
            mock_settings.recording_segment_seconds = GLOBAL_SECONDS

            # Act
            await manager.start()

            # Assert
            assert manager._segment_seconds[3] == GLOBAL_SECONDS


# ---------------------------------------------------------------------------
# _start_camera — per-camera segment_time in ffmpeg command
# ---------------------------------------------------------------------------


class TestStartCamera:
    async def test_start_camera_CustomSegment_UsesPerCameraSegmentTime(self, manager):
        # Arrange
        CUSTOM_SECONDS = 120
        manager._segment_seconds = {1: CUSTOM_SECONDS}

        with patch("app.services.recording_manager.settings") as mock_settings, \
             patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_settings.recordings_local_path = "/tmp/test-rec"
            mock_settings.recording_segment_seconds = 300
            mock_proc = AsyncMock()
            mock_proc.pid = 9999
            mock_exec.return_value = mock_proc

            # Act
            await manager._start_camera(1)

            # Assert — find "-segment_time" in the call args
            call_args = mock_exec.call_args[0]
            seg_idx = list(call_args).index("-segment_time")
            assert call_args[seg_idx + 1] == str(CUSTOM_SECONDS)

    async def test_start_camera_NoCustomSegment_FallsBackToGlobal(self, manager):
        # Arrange
        GLOBAL_SECONDS = 300
        manager._segment_seconds = {}  # no per-camera override

        with patch("app.services.recording_manager.settings") as mock_settings, \
             patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_settings.recordings_local_path = "/tmp/test-rec"
            mock_settings.recording_segment_seconds = GLOBAL_SECONDS
            mock_proc = AsyncMock()
            mock_proc.pid = 9999
            mock_exec.return_value = mock_proc

            # Act
            await manager._start_camera(1)

            # Assert
            call_args = mock_exec.call_args[0]
            seg_idx = list(call_args).index("-segment_time")
            assert call_args[seg_idx + 1] == str(GLOBAL_SECONDS)


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
