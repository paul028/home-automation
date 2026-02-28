"""Unit tests for the cameras API router."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.api.routes.cameras import router
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
    cam.name = "Front Yard"
    cam.ip_address = "192.168.1.100"
    cam.username = "admin"
    cam.password = "secret"
    cam.model = "C520WS"
    cam.location = "Front Yard"
    cam.brand = "tapo"
    cam.has_ptz = True
    cam.has_recording = True
    cam.is_active = True
    return cam


@pytest.fixture
def app(mock_camera):
    """Create a FastAPI app with mocked dependencies."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/cameras")

    mock_camera_svc = AsyncMock()
    mock_camera_svc.get_all = AsyncMock(return_value=[mock_camera])
    mock_camera_svc.get_by_id = AsyncMock(return_value=mock_camera)
    mock_camera_svc.create = AsyncMock(return_value=mock_camera)
    mock_camera_svc.update = AsyncMock(return_value=mock_camera)
    mock_camera_svc.delete = AsyncMock()
    mock_camera_svc.get_locations = AsyncMock(return_value=["Front Yard", "Garden"])

    mock_stream_svc = AsyncMock()
    mock_stream_svc.register_stream = AsyncMock()
    mock_stream_svc.unregister_stream = AsyncMock()

    test_app.dependency_overrides[get_camera_service] = lambda: mock_camera_svc
    test_app.dependency_overrides[get_stream_service] = lambda: mock_stream_svc

    test_app._mock_camera_svc = mock_camera_svc
    test_app._mock_stream_svc = mock_stream_svc

    return test_app


@pytest.fixture
async def client(app):
    """Create an async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# GET /api/cameras
# ---------------------------------------------------------------------------


class TestListCameras:
    async def test_list_cameras_CamerasExist_Returns200WithList(self, client):
        # Act
        response = await client.get("/api/cameras")

        # Assert
        assert response.status_code == 200

    async def test_list_cameras_CamerasExist_ReturnsCorrectCount(self, client):
        # Act
        response = await client.get("/api/cameras")

        # Assert
        assert len(response.json()) == 1


# ---------------------------------------------------------------------------
# GET /api/cameras/locations
# ---------------------------------------------------------------------------


class TestListLocations:
    async def test_list_locations_LocationsExist_Returns200(self, client):
        # Act
        response = await client.get("/api/cameras/locations")

        # Assert
        assert response.status_code == 200

    async def test_list_locations_LocationsExist_ReturnsCorrectList(self, client):
        # Act
        response = await client.get("/api/cameras/locations")

        # Assert
        assert response.json() == ["Front Yard", "Garden"]


# ---------------------------------------------------------------------------
# GET /api/cameras/{camera_id}
# ---------------------------------------------------------------------------


class TestGetCamera:
    async def test_get_camera_ExistingId_Returns200(self, client):
        # Act
        response = await client.get("/api/cameras/1")

        # Assert
        assert response.status_code == 200

    async def test_get_camera_ExistingId_IncludesUsername(self, client):
        # Act
        response = await client.get("/api/cameras/1")

        # Assert
        assert "username" in response.json()

    async def test_get_camera_NonExistentId_Returns404(self, client, app):
        # Arrange
        app._mock_camera_svc.get_by_id = AsyncMock(
            side_effect=DeviceNotFoundError("Not found")
        )

        # Act
        response = await client.get("/api/cameras/999")

        # Assert
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/cameras
# ---------------------------------------------------------------------------


class TestCreateCamera:
    async def test_create_camera_ValidPayload_Returns201(self, client):
        # Arrange
        payload = {
            "name": "New Camera",
            "ip_address": "10.0.0.1",
            "username": "admin",
            "password": "pass",
        }

        # Act
        response = await client.post("/api/cameras", json=payload)

        # Assert
        assert response.status_code == 201

    async def test_create_camera_ValidPayload_RegistersStream(self, client, app):
        # Arrange
        payload = {
            "name": "New Camera",
            "ip_address": "10.0.0.1",
            "username": "admin",
            "password": "pass",
        }

        # Act
        await client.post("/api/cameras", json=payload)

        # Assert
        app._mock_stream_svc.register_stream.assert_awaited_once()


# ---------------------------------------------------------------------------
# PUT /api/cameras/{camera_id}
# ---------------------------------------------------------------------------


class TestUpdateCamera:
    async def test_update_camera_ValidPayload_Returns200(self, client):
        # Arrange
        payload = {"location": "Backyard"}

        # Act
        response = await client.put("/api/cameras/1", json=payload)

        # Assert
        assert response.status_code == 200

    async def test_update_camera_NonExistentId_Returns404(self, client, app):
        # Arrange
        app._mock_camera_svc.get_by_id = AsyncMock(
            side_effect=DeviceNotFoundError("Not found")
        )

        # Act
        response = await client.put("/api/cameras/999", json={"name": "X"})

        # Assert
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/cameras/{camera_id}
# ---------------------------------------------------------------------------


class TestDeleteCamera:
    async def test_delete_camera_ExistingId_Returns204(self, client):
        # Act
        response = await client.delete("/api/cameras/1")

        # Assert
        assert response.status_code == 204

    async def test_delete_camera_ExistingId_UnregistersStream(self, client, app):
        # Act
        await client.delete("/api/cameras/1")

        # Assert
        app._mock_stream_svc.unregister_stream.assert_awaited_once()

    async def test_delete_camera_NonExistentId_Returns404(self, client, app):
        # Arrange
        app._mock_camera_svc.get_by_id = AsyncMock(
            side_effect=DeviceNotFoundError("Not found")
        )

        # Act
        response = await client.delete("/api/cameras/999")

        # Assert
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/cameras/{camera_id}/ptz
# ---------------------------------------------------------------------------


class TestPTZControl:
    async def test_ptz_control_NoPtzSupport_Returns400(self, client, app, mock_camera):
        # Arrange
        mock_camera.has_ptz = False

        # Act
        response = await client.post(
            "/api/cameras/1/ptz", json={"direction": "up", "action": "start"}
        )

        # Assert
        assert response.status_code == 400

    async def test_ptz_control_CameraNotFound_Returns404(self, client, app):
        # Arrange
        app._mock_camera_svc.get_by_id = AsyncMock(
            side_effect=DeviceNotFoundError("Not found")
        )

        # Act
        response = await client.post(
            "/api/cameras/999/ptz", json={"direction": "up", "action": "start"}
        )

        # Assert
        assert response.status_code == 404
