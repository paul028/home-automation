"""Unit tests for CameraService — CRUD operations on the cameras table."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DeviceNotFoundError
from app.models.camera import Camera
from app.models.schemas import CameraCreate, CameraUpdate
from app.services.camera_service import CameraService


# ---------------------------------------------------------------------------
# get_all
# ---------------------------------------------------------------------------


class TestGetAll:
    async def test_get_all_EmptyDatabase_ReturnsEmptyList(self, db_session: AsyncSession):
        # Arrange
        service = CameraService(db_session)

        # Act
        cameras = await service.get_all()

        # Assert
        assert cameras == []

    async def test_get_all_MultipleCameras_ReturnsAllCamerasSortedByLocation(
        self, db_session: AsyncSession
    ):
        # Arrange
        service = CameraService(db_session)
        cam_b = Camera(
            name="B", ip_address="10.0.0.2", username="u", password="p", location="Zoo"
        )
        cam_a = Camera(
            name="A", ip_address="10.0.0.1", username="u", password="p", location="Attic"
        )
        db_session.add_all([cam_b, cam_a])
        await db_session.commit()

        # Act
        cameras = await service.get_all()

        # Assert
        assert len(cameras) == 2
        assert cameras[0].location == "Attic"
        assert cameras[1].location == "Zoo"


# ---------------------------------------------------------------------------
# get_locations
# ---------------------------------------------------------------------------


class TestGetLocations:
    async def test_get_locations_NoCameras_ReturnsEmptyList(
        self, db_session: AsyncSession
    ):
        # Arrange
        service = CameraService(db_session)

        # Act
        locations = await service.get_locations()

        # Assert
        assert locations == []

    async def test_get_locations_MixedLocations_ReturnsDistinctNonNullSorted(
        self, db_session: AsyncSession
    ):
        # Arrange
        service = CameraService(db_session)
        db_session.add_all([
            Camera(name="A", ip_address="10.0.0.1", username="u", password="p", location="Garden"),
            Camera(name="B", ip_address="10.0.0.2", username="u", password="p", location="Garden"),
            Camera(name="C", ip_address="10.0.0.3", username="u", password="p", location=None),
            Camera(name="D", ip_address="10.0.0.4", username="u", password="p", location="Attic"),
        ])
        await db_session.commit()

        # Act
        locations = await service.get_locations()

        # Assert
        assert locations == ["Attic", "Garden"]


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


class TestGetById:
    async def test_get_by_id_ExistingCamera_ReturnsCamera(
        self, db_session: AsyncSession, saved_camera: Camera
    ):
        # Arrange
        service = CameraService(db_session)

        # Act
        camera = await service.get_by_id(saved_camera.id)

        # Assert
        assert camera.id == saved_camera.id
        assert camera.name == saved_camera.name

    async def test_get_by_id_NonExistentId_RaisesDeviceNotFoundError(
        self, db_session: AsyncSession
    ):
        # Arrange
        service = CameraService(db_session)
        NON_EXISTENT_ID = 9999

        # Act & Assert
        with pytest.raises(DeviceNotFoundError, match="9999"):
            await service.get_by_id(NON_EXISTENT_ID)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    async def test_create_ValidData_ReturnsCameraWithGeneratedId(
        self, db_session: AsyncSession, sample_camera_data: dict
    ):
        # Arrange
        service = CameraService(db_session)
        data = CameraCreate(**sample_camera_data)

        # Act
        camera = await service.create(data)

        # Assert
        assert camera.id is not None

    async def test_create_ValidData_PersistsAllFields(
        self, db_session: AsyncSession, sample_camera_data: dict
    ):
        # Arrange
        service = CameraService(db_session)
        data = CameraCreate(**sample_camera_data)

        # Act
        camera = await service.create(data)

        # Assert
        assert camera.name == sample_camera_data["name"]
        assert camera.ip_address == sample_camera_data["ip_address"]
        assert camera.has_ptz == sample_camera_data["has_ptz"]

    async def test_create_MinimalData_UsesDefaults(self, db_session: AsyncSession):
        # Arrange
        service = CameraService(db_session)
        data = CameraCreate(
            name="Minimal", ip_address="10.0.0.1", username="u", password="p"
        )

        # Act
        camera = await service.create(data)

        # Assert
        assert camera.brand == "tapo"
        assert camera.has_ptz is False


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestUpdate:
    async def test_update_ExistingCamera_UpdatesSpecifiedFields(
        self, db_session: AsyncSession, saved_camera: Camera
    ):
        # Arrange
        service = CameraService(db_session)
        NEW_LOCATION = "Backyard"
        update_data = CameraUpdate(location=NEW_LOCATION)

        # Act
        updated = await service.update(saved_camera.id, update_data)

        # Assert
        assert updated.location == NEW_LOCATION

    async def test_update_ExistingCamera_PreservesUnchangedFields(
        self, db_session: AsyncSession, saved_camera: Camera
    ):
        # Arrange
        service = CameraService(db_session)
        original_name = saved_camera.name
        update_data = CameraUpdate(location="New Location")

        # Act
        updated = await service.update(saved_camera.id, update_data)

        # Assert
        assert updated.name == original_name

    async def test_update_NonExistentCamera_RaisesDeviceNotFoundError(
        self, db_session: AsyncSession
    ):
        # Arrange
        service = CameraService(db_session)
        NON_EXISTENT_ID = 9999

        # Act & Assert
        with pytest.raises(DeviceNotFoundError):
            await service.update(NON_EXISTENT_ID, CameraUpdate(name="X"))


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_delete_ExistingCamera_RemovesFromDatabase(
        self, db_session: AsyncSession, saved_camera: Camera
    ):
        # Arrange
        service = CameraService(db_session)

        # Act
        await service.delete(saved_camera.id)

        # Assert
        remaining = await service.get_all()
        assert len(remaining) == 0

    async def test_delete_NonExistentCamera_RaisesDeviceNotFoundError(
        self, db_session: AsyncSession
    ):
        # Arrange
        service = CameraService(db_session)
        NON_EXISTENT_ID = 9999

        # Act & Assert
        with pytest.raises(DeviceNotFoundError):
            await service.delete(NON_EXISTENT_ID)
