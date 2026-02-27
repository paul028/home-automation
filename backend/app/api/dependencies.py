from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.camera_service import CameraService
from app.services.stream_service import StreamService
from app.services.recording_service import RecordingService


async def get_camera_service(
    db: AsyncSession = Depends(get_db),
) -> CameraService:
    return CameraService(db)


async def get_stream_service() -> StreamService:
    return StreamService()


async def get_recording_service() -> RecordingService:
    return RecordingService()
