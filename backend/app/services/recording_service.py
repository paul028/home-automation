import asyncio
import logging
import re
from datetime import date

from app.config import settings
from app.models.camera import Camera
from app.services.gdrive_service import GDriveService

logger = logging.getLogger(__name__)

# Lazy singleton — initialized on first use
_gdrive: GDriveService | None = None


def _get_gdrive() -> GDriveService | None:
    global _gdrive
    if _gdrive is None and settings.gdrive_credentials_path:
        try:
            _gdrive = GDriveService(settings.gdrive_credentials_path)
        except Exception as e:
            logger.error("Failed to init GDrive for recordings: %s", e)
    return _gdrive


class RecordingService:
    """Handles recording retrieval from Google Drive."""

    async def get_recordings(
        self, camera: Camera, recording_date: date
    ) -> list[dict]:
        """Get recording segments for a camera on a specific date."""
        gdrive = _get_gdrive()
        if not gdrive or not settings.gdrive_folder_id:
            return []

        date_str = recording_date.strftime("%Y-%m-%d")

        # Navigate: root → camera_name → date folder
        cam_folder_id = await asyncio.to_thread(
            gdrive.find_folder, camera.name, settings.gdrive_folder_id
        )
        if not cam_folder_id:
            return []

        date_folder_id = await asyncio.to_thread(
            gdrive.find_folder, date_str, cam_folder_id
        )
        if not date_folder_id:
            return []

        files = await asyncio.to_thread(
            gdrive.list_files_in_folder, date_folder_id
        )

        segments = []
        for f in files:
            # Filename format: HH:MM:SS.mp4
            match = re.match(r"(\d{2}):(\d{2}):(\d{2})\.mp4", f["name"])
            if not match:
                continue

            h, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3))
            start_seconds = h * 3600 + m * 60 + s
            end_seconds = start_seconds + settings.recording_segment_seconds

            end_h = (end_seconds // 3600) % 24
            end_m = (end_seconds % 3600) // 60
            end_s = end_seconds % 60

            segments.append({
                "file_id": f["id"],
                "start_time": f"{h:02d}:{m:02d}:{s:02d}",
                "end_time": f"{end_h:02d}:{end_m:02d}:{end_s:02d}",
                "duration": settings.recording_segment_seconds,
            })

        segments.sort(key=lambda s: s["start_time"], reverse=True)
        return segments

    async def get_recording_days(
        self, camera: Camera, year: int, month: int
    ) -> list[int]:
        """Get days with recordings for a camera in a given month."""
        gdrive = _get_gdrive()
        if not gdrive or not settings.gdrive_folder_id:
            return []

        cam_folder_id = await asyncio.to_thread(
            gdrive.find_folder, camera.name, settings.gdrive_folder_id
        )
        if not cam_folder_id:
            return []

        # List all date subfolders and filter by year-month
        date_folders = await asyncio.to_thread(
            gdrive.list_subfolders, cam_folder_id
        )

        prefix = f"{year:04d}-{month:02d}-"
        days = []
        for folder in date_folders:
            name = folder["name"]
            if name.startswith(prefix):
                try:
                    day = int(name[len(prefix):])
                    days.append(day)
                except ValueError:
                    continue

        return sorted(days)
