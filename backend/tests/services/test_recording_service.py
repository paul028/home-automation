"""Unit tests for RecordingService — Google Drive recording retrieval."""

import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from app.services.recording_service import RecordingService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_gdrive_mock(
    cam_folder_id="cam_folder",
    date_folder_id="date_folder",
    files=None,
    subfolders=None,
):
    """Build a mock GDriveService with pre-configured return values."""
    mock = MagicMock()
    mock.find_folder = MagicMock(side_effect=lambda name, parent: {
        "Front Yard": cam_folder_id,
        "2026-02-28": date_folder_id,
    }.get(name))
    mock.list_files_in_folder = MagicMock(return_value=files or [])
    mock.list_subfolders = MagicMock(return_value=subfolders or [])
    return mock


# ---------------------------------------------------------------------------
# get_recordings
# ---------------------------------------------------------------------------


class TestGetRecordings:
    async def test_get_recordings_NoGdrive_ReturnsEmptyList(self, make_camera):
        # Arrange
        service = RecordingService()
        camera = make_camera(name="Front Yard")

        with patch("app.services.recording_service._get_gdrive", return_value=None):
            # Act
            result = await service.get_recordings(camera, date(2026, 2, 28))

            # Assert
            assert result == []

    async def test_get_recordings_CameraFolderNotFound_ReturnsEmptyList(
        self, make_camera
    ):
        # Arrange
        service = RecordingService()
        camera = make_camera(name="Nonexistent")
        mock_gdrive = MagicMock()
        mock_gdrive.find_folder = MagicMock(return_value=None)

        with patch("app.services.recording_service._get_gdrive", return_value=mock_gdrive), \
             patch("app.services.recording_service.settings") as mock_settings:
            mock_settings.gdrive_folder_id = "root_id"
            mock_settings.recording_segment_seconds = 300

            # Act
            result = await service.get_recordings(camera, date(2026, 2, 28))

            # Assert
            assert result == []

    async def test_get_recordings_FilesExist_ReturnsSegmentsInDescOrder(
        self, make_camera
    ):
        # Arrange
        service = RecordingService()
        camera = make_camera(name="Front Yard")
        files = [
            {"id": "file_a", "name": "08:00:00.mp4"},
            {"id": "file_b", "name": "08:05:00.mp4"},
            {"id": "file_c", "name": "07:55:00.mp4"},
        ]
        mock_gdrive = _make_gdrive_mock(files=files)

        with patch("app.services.recording_service._get_gdrive", return_value=mock_gdrive), \
             patch("app.services.recording_service.settings") as mock_settings:
            mock_settings.gdrive_folder_id = "root_id"
            mock_settings.recording_segment_seconds = 300

            # Act
            result = await service.get_recordings(camera, date(2026, 2, 28))

            # Assert
            assert len(result) == 3
            assert result[0]["start_time"] == "08:05:00"
            assert result[-1]["start_time"] == "07:55:00"

    async def test_get_recordings_ValidSegment_CalculatesCorrectEndTime(
        self, make_camera
    ):
        # Arrange
        service = RecordingService()
        camera = make_camera(name="Front Yard")
        SEGMENT_SECONDS = 300  # 5 minutes
        files = [{"id": "file_1", "name": "14:30:00.mp4"}]
        mock_gdrive = _make_gdrive_mock(files=files)

        with patch("app.services.recording_service._get_gdrive", return_value=mock_gdrive), \
             patch("app.services.recording_service.settings") as mock_settings:
            mock_settings.gdrive_folder_id = "root_id"
            mock_settings.recording_segment_seconds = SEGMENT_SECONDS

            # Act
            result = await service.get_recordings(camera, date(2026, 2, 28))

            # Assert
            assert result[0]["end_time"] == "14:35:00"
            assert result[0]["duration"] == SEGMENT_SECONDS

    async def test_get_recordings_InvalidFilename_SkipsFile(self, make_camera):
        # Arrange
        service = RecordingService()
        camera = make_camera(name="Front Yard")
        files = [
            {"id": "good", "name": "10:00:00.mp4"},
            {"id": "bad", "name": "not-a-time.mp4"},
        ]
        mock_gdrive = _make_gdrive_mock(files=files)

        with patch("app.services.recording_service._get_gdrive", return_value=mock_gdrive), \
             patch("app.services.recording_service.settings") as mock_settings:
            mock_settings.gdrive_folder_id = "root_id"
            mock_settings.recording_segment_seconds = 300

            # Act
            result = await service.get_recordings(camera, date(2026, 2, 28))

            # Assert
            assert len(result) == 1

    async def test_get_recordings_ValidSegment_IncludesFileId(self, make_camera):
        # Arrange
        service = RecordingService()
        camera = make_camera(name="Front Yard")
        EXPECTED_FILE_ID = "abc123"
        files = [{"id": EXPECTED_FILE_ID, "name": "12:00:00.mp4"}]
        mock_gdrive = _make_gdrive_mock(files=files)

        with patch("app.services.recording_service._get_gdrive", return_value=mock_gdrive), \
             patch("app.services.recording_service.settings") as mock_settings:
            mock_settings.gdrive_folder_id = "root_id"
            mock_settings.recording_segment_seconds = 300

            # Act
            result = await service.get_recordings(camera, date(2026, 2, 28))

            # Assert
            assert result[0]["file_id"] == EXPECTED_FILE_ID


# ---------------------------------------------------------------------------
# get_recording_days
# ---------------------------------------------------------------------------


class TestGetRecordingDays:
    async def test_get_recording_days_NoGdrive_ReturnsEmptyList(self, make_camera):
        # Arrange
        service = RecordingService()
        camera = make_camera(name="Test")

        with patch("app.services.recording_service._get_gdrive", return_value=None):
            # Act
            result = await service.get_recording_days(camera, 2026, 2)

            # Assert
            assert result == []

    async def test_get_recording_days_FoldersExist_ReturnsSortedDays(
        self, make_camera
    ):
        # Arrange
        service = RecordingService()
        camera = make_camera(name="Front Yard")
        subfolders = [
            {"id": "f1", "name": "2026-02-15"},
            {"id": "f2", "name": "2026-02-03"},
            {"id": "f3", "name": "2026-02-28"},
            {"id": "f4", "name": "2026-01-10"},  # different month — excluded
        ]
        mock_gdrive = MagicMock()
        mock_gdrive.find_folder = MagicMock(return_value="cam_folder_id")
        mock_gdrive.list_subfolders = MagicMock(return_value=subfolders)

        with patch("app.services.recording_service._get_gdrive", return_value=mock_gdrive), \
             patch("app.services.recording_service.settings") as mock_settings:
            mock_settings.gdrive_folder_id = "root_id"

            # Act
            result = await service.get_recording_days(camera, 2026, 2)

            # Assert
            assert result == [3, 15, 28]

    async def test_get_recording_days_CameraFolderNotFound_ReturnsEmptyList(
        self, make_camera
    ):
        # Arrange
        service = RecordingService()
        camera = make_camera(name="Ghost")
        mock_gdrive = MagicMock()
        mock_gdrive.find_folder = MagicMock(return_value=None)

        with patch("app.services.recording_service._get_gdrive", return_value=mock_gdrive), \
             patch("app.services.recording_service.settings") as mock_settings:
            mock_settings.gdrive_folder_id = "root_id"

            # Act
            result = await service.get_recording_days(camera, 2026, 2)

            # Assert
            assert result == []
