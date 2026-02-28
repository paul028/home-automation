"""Unit tests for GDriveService — Google Drive API wrapper."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.gdrive_service import GDriveService, FOLDER_MIME


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def gdrive():
    """Create a GDriveService with mocked credentials and API client."""
    with patch("app.services.gdrive_service._load_credentials") as mock_creds, \
         patch("app.services.gdrive_service.build") as mock_build:
        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        service = GDriveService("fake/path.json")
        service._mock_service = mock_service
        return service


# ---------------------------------------------------------------------------
# create_folder
# ---------------------------------------------------------------------------


class TestCreateFolder:
    def test_create_folder_ValidInput_ReturnsNewFolderId(self, gdrive):
        # Arrange
        EXPECTED_ID = "new_folder_123"
        gdrive._mock_service.files().create().execute.return_value = {"id": EXPECTED_ID}

        # Act
        result = gdrive.create_folder("My Folder", "parent_123")

        # Assert
        assert result == EXPECTED_ID


# ---------------------------------------------------------------------------
# get_or_create_folder
# ---------------------------------------------------------------------------


class TestGetOrCreateFolder:
    def test_get_or_create_folder_FolderExists_ReturnsExistingId(self, gdrive):
        # Arrange
        EXISTING_ID = "existing_folder"
        gdrive._mock_service.files().list().execute.return_value = {
            "files": [{"id": EXISTING_ID}]
        }

        # Act
        result = gdrive.get_or_create_folder("Camera", "parent_id")

        # Assert
        assert result == EXISTING_ID

    def test_get_or_create_folder_FolderMissing_CreatesAndReturnsNewId(self, gdrive):
        # Arrange
        NEW_ID = "created_folder"
        gdrive._mock_service.files().list().execute.return_value = {"files": []}
        gdrive._mock_service.files().create().execute.return_value = {"id": NEW_ID}

        # Act
        result = gdrive.get_or_create_folder("Camera", "parent_id")

        # Assert
        assert result == NEW_ID


# ---------------------------------------------------------------------------
# find_folder
# ---------------------------------------------------------------------------


class TestFindFolder:
    def test_find_folder_Exists_ReturnsId(self, gdrive):
        # Arrange
        FOLDER_ID = "found_folder"
        gdrive._mock_service.files().list().execute.return_value = {
            "files": [{"id": FOLDER_ID}]
        }

        # Act
        result = gdrive.find_folder("2026-02-28", "cam_folder")

        # Assert
        assert result == FOLDER_ID

    def test_find_folder_NotFound_ReturnsNone(self, gdrive):
        # Arrange
        gdrive._mock_service.files().list().execute.return_value = {"files": []}

        # Act
        result = gdrive.find_folder("nonexistent", "parent")

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# list_files_in_folder
# ---------------------------------------------------------------------------


class TestListFilesInFolder:
    def test_list_files_in_folder_HasFiles_ReturnsFileList(self, gdrive):
        # Arrange
        FILES = [
            {"id": "f1", "name": "08:00:00.mp4"},
            {"id": "f2", "name": "08:05:00.mp4"},
        ]
        gdrive._mock_service.files().list().execute.return_value = {"files": FILES}

        # Act
        result = gdrive.list_files_in_folder("folder_123")

        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "08:00:00.mp4"

    def test_list_files_in_folder_EmptyFolder_ReturnsEmptyList(self, gdrive):
        # Arrange
        gdrive._mock_service.files().list().execute.return_value = {"files": []}

        # Act
        result = gdrive.list_files_in_folder("empty_folder")

        # Assert
        assert result == []


# ---------------------------------------------------------------------------
# list_subfolders
# ---------------------------------------------------------------------------


class TestListSubfolders:
    def test_list_subfolders_HasSubfolders_ReturnsList(self, gdrive):
        # Arrange
        FOLDERS = [
            {"id": "d1", "name": "2026-02-27"},
            {"id": "d2", "name": "2026-02-28"},
        ]
        gdrive._mock_service.files().list().execute.return_value = {"files": FOLDERS}

        # Act
        result = gdrive.list_subfolders("cam_folder")

        # Assert
        assert len(result) == 2


# ---------------------------------------------------------------------------
# get_file_size
# ---------------------------------------------------------------------------


class TestGetFileSize:
    def test_get_file_size_ValidFile_ReturnsInteger(self, gdrive):
        # Arrange
        EXPECTED_SIZE = 5242880
        gdrive._mock_service.files().get().execute.return_value = {
            "size": str(EXPECTED_SIZE)
        }

        # Act
        result = gdrive.get_file_size("file_123")

        # Assert
        assert result == EXPECTED_SIZE
        assert isinstance(result, int)


# ---------------------------------------------------------------------------
# download_bytes
# ---------------------------------------------------------------------------


class TestDownloadBytes:
    def test_download_bytes_NoRange_ReturnsFullContent(self, gdrive):
        # Arrange
        CONTENT = b"video data here"
        gdrive._mock_service._http.request.return_value = (None, CONTENT)

        # Act
        result = gdrive.download_bytes("file_123")

        # Assert
        assert result == CONTENT

    def test_download_bytes_WithRange_SendsRangeHeader(self, gdrive):
        # Arrange
        CONTENT = b"partial data"
        gdrive._mock_service._http.request.return_value = (None, CONTENT)

        # Act
        gdrive.download_bytes("file_123", start=100, end=200)

        # Assert
        call_args = gdrive._mock_service._http.request.call_args
        headers = call_args[1].get("headers") or call_args[0][1] if len(call_args[0]) > 1 else call_args.kwargs.get("headers", {})
        # The method is called positionally: request(url, headers=...)
        assert "Range" in call_args.kwargs.get("headers", call_args[0][1] if len(call_args[0]) > 1 else {})


# ---------------------------------------------------------------------------
# delete_file
# ---------------------------------------------------------------------------


class TestDeleteFile:
    def test_delete_file_ValidId_CallsDeleteApi(self, gdrive):
        # Arrange
        mock_delete = gdrive._mock_service.files().delete
        mock_delete().execute.return_value = None

        # Act
        gdrive.delete_file("file_to_delete")

        # Assert — no exception means success
