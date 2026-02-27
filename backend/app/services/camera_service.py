from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.camera import Camera
from app.models.schemas import CameraCreate, CameraUpdate
from app.core.exceptions import DeviceNotFoundError


class CameraService:
    """Handles camera CRUD operations."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_all(self) -> list[Camera]:
        result = await self._db.execute(
            select(Camera).order_by(Camera.location, Camera.id)
        )
        return list(result.scalars().all())

    async def get_locations(self) -> list[str]:
        result = await self._db.execute(
            select(distinct(Camera.location))
            .where(Camera.location.isnot(None))
            .order_by(Camera.location)
        )
        return list(result.scalars().all())

    async def get_by_id(self, camera_id: int) -> Camera:
        result = await self._db.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        camera = result.scalar_one_or_none()
        if camera is None:
            raise DeviceNotFoundError(f"Camera with id {camera_id} not found")
        return camera

    async def create(self, data: CameraCreate) -> Camera:
        camera = Camera(**data.model_dump())
        self._db.add(camera)
        await self._db.commit()
        await self._db.refresh(camera)
        return camera

    async def update(self, camera_id: int, data: CameraUpdate) -> Camera:
        camera = await self.get_by_id(camera_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(camera, field, value)
        await self._db.commit()
        await self._db.refresh(camera)
        return camera

    async def delete(self, camera_id: int) -> None:
        camera = await self.get_by_id(camera_id)
        await self._db.delete(camera)
        await self._db.commit()
