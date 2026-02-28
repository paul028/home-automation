"""Unit tests for the recordings API router."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.api.routes.recordings import router, _parse_range
from app.api.dependencies import get_camera_service, get_recording_service
from app.core.exceptions import DeviceNotFoundError


# ---------------------------------------------------------------------------
# _parse_range (pure function)
# ---------------------------------------------------------------------------


class TestParseRange:
    def test_parse_range_ValidFullRange_ReturnsStartAndEnd(self):
        # Act
        start, end = _parse_range("bytes=0-1023", 5000)

        # Assert
        assert start == 0
        assert end == 1023

    def test_parse_range_OpenEndRange_ReturnsStartToFileEnd(self):
        # Act
        start, end = _parse_range("bytes=1000-", 5000)

        # Assert
        assert start == 1000
        assert end == 4999

    def test_parse_range_EndExceedsFileSize_ClampsToFileEnd(self):
        # Act
        start, end = _parse_range("bytes=0-99999", 5000)

        # Assert
        assert end == 4999

    def test_parse_range_InvalidFormat_ReturnsFullRange(self):
        # Act
        start, end = _parse_range("invalid", 5000)

        # Assert
        assert start == 0
        assert end == 4999


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_camera():
    """Build a mock camera ORM object."""
    cam = MagicMock()
    cam.id = 1
    cam.name = "Garage"
    cam.ip_address = "192.168.1.60"
    return cam


@pytest.fixture
def app(mock_camera):
    """Create a FastAPI app with mocked dependencies."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/recordings")

    mock_camera_svc = AsyncMock()
    mock_camera_svc.get_by_id = AsyncMock(return_value=mock_camera)

    mock_recording_svc = AsyncMock()
    mock_recording_svc.get_recordings = AsyncMock(return_value=[
        {"file_id": "abc", "start_time": "14:00:00", "end_time": "14:05:00", "duration": 300}
    ])
    mock_recording_svc.get_recording_days = AsyncMock(return_value=[1, 15, 28])

    test_app.dependency_overrides[get_camera_service] = lambda: mock_camera_svc
    test_app.dependency_overrides[get_recording_service] = lambda: mock_recording_svc

    test_app._mock_camera_svc = mock_camera_svc

    return test_app


@pytest.fixture
async def client(app):
    """Create an async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# GET /api/recordings/{camera_id}
# ---------------------------------------------------------------------------


class TestGetRecordings:
    async def test_get_recordings_ValidRequest_Returns200(self, client):
        # Act
        response = await client.get(
            "/api/recordings/1", params={"recording_date": "2026-02-28"}
        )

        # Assert
        assert response.status_code == 200

    async def test_get_recordings_ValidRequest_ReturnsSegments(self, client):
        # Act
        response = await client.get(
            "/api/recordings/1", params={"recording_date": "2026-02-28"}
        )

        # Assert
        data = response.json()
        assert len(data) == 1
        assert data[0]["file_id"] == "abc"

    async def test_get_recordings_CameraNotFound_Returns404(self, client, app):
        # Arrange
        app._mock_camera_svc.get_by_id = AsyncMock(
            side_effect=DeviceNotFoundError("Not found")
        )

        # Act
        response = await client.get(
            "/api/recordings/999", params={"recording_date": "2026-02-28"}
        )

        # Assert
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/recordings/{camera_id}/days
# ---------------------------------------------------------------------------


class TestGetRecordingDays:
    async def test_get_recording_days_ValidRequest_Returns200(self, client):
        # Act
        response = await client.get(
            "/api/recordings/1/days", params={"year": 2026, "month": 2}
        )

        # Assert
        assert response.status_code == 200

    async def test_get_recording_days_ValidRequest_ReturnsDaysList(self, client):
        # Act
        response = await client.get(
            "/api/recordings/1/days", params={"year": 2026, "month": 2}
        )

        # Assert
        data = response.json()
        assert data["days"] == [1, 15, 28]
        assert data["year"] == 2026
        assert data["month"] == 2

    async def test_get_recording_days_CameraNotFound_Returns404(self, client, app):
        # Arrange
        app._mock_camera_svc.get_by_id = AsyncMock(
            side_effect=DeviceNotFoundError("Not found")
        )

        # Act
        response = await client.get(
            "/api/recordings/999/days", params={"year": 2026, "month": 2}
        )

        # Assert
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/recordings/play/{file_id}
# ---------------------------------------------------------------------------


class TestPlayRecording:
    async def test_play_recording_NoGdrive_Returns503(self, client):
        # Arrange
        with patch("app.api.routes.recordings._get_gdrive", return_value=None):
            # Act
            response = await client.get("/api/recordings/play/some_file_id")

            # Assert
            assert response.status_code == 503

    async def test_play_recording_NoRangeHeader_Returns200WithFullContent(self, client):
        # Arrange
        CONTENT = b"full video content"
        mock_gdrive = MagicMock()
        mock_gdrive.get_file_size = MagicMock(return_value=len(CONTENT))
        mock_gdrive.download_bytes = MagicMock(return_value=CONTENT)

        with patch("app.api.routes.recordings._get_gdrive", return_value=mock_gdrive):
            # Act
            response = await client.get("/api/recordings/play/file_123")

            # Assert
            assert response.status_code == 200
            assert response.headers["content-type"] == "video/mp4"

    async def test_play_recording_WithRangeHeader_Returns206PartialContent(self, client):
        # Arrange
        FILE_SIZE = 10000
        PARTIAL_CONTENT = b"partial"
        mock_gdrive = MagicMock()
        mock_gdrive.get_file_size = MagicMock(return_value=FILE_SIZE)
        mock_gdrive.download_bytes = MagicMock(return_value=PARTIAL_CONTENT)

        with patch("app.api.routes.recordings._get_gdrive", return_value=mock_gdrive):
            # Act
            response = await client.get(
                "/api/recordings/play/file_123",
                headers={"Range": "bytes=0-999"},
            )

            # Assert
            assert response.status_code == 206
            assert "content-range" in response.headers
