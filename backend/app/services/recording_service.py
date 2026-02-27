from datetime import date

from app.models.camera import Camera
from app.services.device_pool import device_pool


class RecordingService:
    """Handles recording retrieval from cameras."""

    async def get_recordings(self, camera: Camera, recording_date: date) -> list[dict]:
        """Get recordings for a camera on a specific date."""
        tapo = await device_pool.get(camera)
        return await tapo.get_recordings(recording_date)

    async def get_recording_days(
        self, camera: Camera, year: int, month: int
    ) -> list[int]:
        """Get days with recordings for a camera in a given month."""
        tapo = await device_pool.get(camera)
        return await tapo.get_recording_days(year, month)
