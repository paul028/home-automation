from datetime import date

from app.devices.tapo.tapo_camera import TapoCamera
from app.models.camera import Camera


class RecordingService:
    """Handles recording retrieval from cameras."""

    def _create_camera(self, camera: Camera) -> TapoCamera:
        return TapoCamera(
            ip=camera.ip_address,
            username=camera.username,
            password=camera.password,
            name=camera.name,
        )

    async def get_recordings(self, camera: Camera, recording_date: date) -> list[dict]:
        """Get recordings for a camera on a specific date."""
        tapo = self._create_camera(camera)
        await tapo.connect()
        try:
            return await tapo.get_recordings(recording_date)
        finally:
            await tapo.disconnect()

    async def get_recording_days(
        self, camera: Camera, year: int, month: int
    ) -> list[int]:
        """Get days with recordings for a camera in a given month."""
        tapo = self._create_camera(camera)
        await tapo.connect()
        try:
            return await tapo.get_recording_days(year, month)
        finally:
            await tapo.disconnect()
