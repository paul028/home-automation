"""Unit tests for the streams API router."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.api.routes.streams import router
from app.api.dependencies import get_camera_service, get_stream_service
from app.core.exceptions import DeviceNotFoundError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_camera():
    """Build a mock camera ORM object."""
    cam = MagicMock()
    cam.id = 1
    cam.name = "Terrace"
    cam.ip_address = "192.168.1.50"
    cam.username = "admin"
    cam.password = "pass"
    cam.model = "C220"
    cam.location = "Terrace"
    cam.brand = "tapo"
    cam.has_ptz = True
    cam.has_recording = True
    cam.is_active = True
    return cam


@pytest.fixture
def app(mock_camera):
    """Create a FastAPI app with mocked dependencies."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/streams")

    mock_camera_svc = AsyncMock()
    mock_camera_svc.get_by_id = AsyncMock(return_value=mock_camera)

    mock_stream_svc = AsyncMock()
    mock_stream_svc.register_stream = AsyncMock()
    mock_stream_svc.get_stream_urls = MagicMock(return_value={
        "webrtc_url": "ws://localhost:1984/api/ws?src=camera_1",
        "mse_url": "ws://localhost:1984/api/ws?src=camera_1",
        "hls_url": "http://localhost:1984/api/stream.m3u8?src=camera_1",
    })
    mock_stream_svc.get_active_streams = AsyncMock(return_value={"camera_1": {}})

    test_app.dependency_overrides[get_camera_service] = lambda: mock_camera_svc
    test_app.dependency_overrides[get_stream_service] = lambda: mock_stream_svc

    test_app._mock_camera_svc = mock_camera_svc

    return test_app


@pytest.fixture
async def client(app):
    """Create an async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# GET /api/streams/{camera_id}
# ---------------------------------------------------------------------------


class TestGetStreamInfo:
    async def test_get_stream_info_ValidCamera_Returns200(self, client):
        # Act
        response = await client.get("/api/streams/1")

        # Assert
        assert response.status_code == 200

    async def test_get_stream_info_ValidCamera_ReturnsMseUrl(self, client):
        # Act
        response = await client.get("/api/streams/1")

        # Assert
        data = response.json()
        assert "mse_url" in data
        assert data["mse_url"].startswith("ws://")

    async def test_get_stream_info_ValidCamera_ReturnsCameraName(self, client):
        # Act
        response = await client.get("/api/streams/1")

        # Assert
        assert response.json()["camera_name"] == "Terrace"

    async def test_get_stream_info_CameraNotFound_Returns404(self, client, app):
        # Arrange
        app._mock_camera_svc.get_by_id = AsyncMock(
            side_effect=DeviceNotFoundError("Not found")
        )

        # Act
        response = await client.get("/api/streams/999")

        # Assert
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/streams
# ---------------------------------------------------------------------------


class TestListActiveStreams:
    async def test_list_active_streams_StreamsExist_Returns200(self, client):
        # Act
        response = await client.get("/api/streams")

        # Assert
        assert response.status_code == 200

    async def test_list_active_streams_StreamsExist_ReturnsDict(self, client):
        # Act
        response = await client.get("/api/streams")

        # Assert
        assert "camera_1" in response.json()
