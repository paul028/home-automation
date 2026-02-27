import asyncio
import logging
from pathlib import Path

from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models.camera import Camera
from app.services.gdrive_service import GDriveService

logger = logging.getLogger(__name__)

# How often the upload worker scans for completed segments
UPLOAD_INTERVAL = 30  # seconds

# How often the cleanup worker runs
CLEANUP_INTERVAL = 86400  # once per day


class RecordingManager:
    """Manages ffmpeg recording processes and Google Drive upload lifecycle."""

    def __init__(self):
        self._processes: dict[int, asyncio.subprocess.Process] = {}
        self._tasks: list[asyncio.Task] = []
        self._gdrive: GDriveService | None = None
        self._running = False
        # Cache: camera_id → camera name (for Drive folder names)
        self._camera_names: dict[int, str] = {}
        # Cache: (camera_name) → Drive folder ID, (camera_name, date_str) → Drive folder ID
        self._folder_cache: dict[str, str] = {}

    async def start(self) -> None:
        """Start recording all active cameras and background workers."""
        self._running = True
        local_path = Path(settings.recordings_local_path)
        local_path.mkdir(parents=True, exist_ok=True)

        # Init Google Drive service
        if settings.gdrive_credentials_path and settings.gdrive_folder_id:
            try:
                self._gdrive = await asyncio.to_thread(
                    GDriveService, settings.gdrive_credentials_path
                )
                logger.info("Google Drive service initialized")
            except Exception as e:
                logger.error("Failed to init Google Drive: %s", e)
                self._gdrive = None
        else:
            logger.warning(
                "Google Drive not configured — recordings will stay local only"
            )

        # Fetch all active cameras
        async with async_session() as db:
            result = await db.execute(
                select(Camera).where(Camera.is_active.is_(True))
            )
            cameras = list(result.scalars().all())

        for camera in cameras:
            self._camera_names[camera.id] = camera.name
            await self._start_camera(camera.id)

        # Start background workers
        self._tasks.append(asyncio.create_task(self._upload_worker()))
        self._tasks.append(asyncio.create_task(self._cleanup_worker()))
        logger.info(
            "Recording manager started for %d camera(s)", len(self._processes)
        )

    async def stop(self) -> None:
        """Stop all ffmpeg processes and background workers."""
        self._running = False

        for task in self._tasks:
            task.cancel()

        for camera_id, proc in self._processes.items():
            logger.info("Stopping ffmpeg for camera %d (pid=%d)", camera_id, proc.pid)
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()

        self._processes.clear()
        self._tasks.clear()
        logger.info("Recording manager stopped")

    async def _start_camera(self, camera_id: int) -> None:
        """Launch an ffmpeg process for a single camera."""
        stream_name = f"camera_{camera_id}"
        rtsp_url = f"rtsp://localhost:8554/{stream_name}"

        output_dir = Path(settings.recordings_local_path) / str(camera_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_pattern = str(output_dir / "%Y-%m-%d_%H-%M-%S.mp4")

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "warning",
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            "-an",              # drop audio (pcm_alaw not supported in MP4)
            "-c:v", "copy",     # video passthrough, no transcoding
            "-f", "segment",
            "-segment_time", str(settings.recording_segment_seconds),
            "-strftime", "1",
            "-reset_timestamps", "1",
            output_pattern,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            self._processes[camera_id] = proc
            logger.info(
                "Started ffmpeg for camera %d (pid=%d)", camera_id, proc.pid
            )
            # Monitor this process in the background
            self._tasks.append(asyncio.create_task(self._watch(camera_id)))
        except FileNotFoundError:
            logger.error("ffmpeg not found — install it with: brew install ffmpeg")
        except Exception as e:
            logger.error("Failed to start ffmpeg for camera %d: %s", camera_id, e)

    async def _watch(self, camera_id: int) -> None:
        """Monitor an ffmpeg process and restart it if it dies."""
        while self._running:
            proc = self._processes.get(camera_id)
            if proc is None:
                return

            retcode = await proc.wait()
            if not self._running:
                return

            stderr_bytes = await proc.stderr.read() if proc.stderr else b""
            stderr_text = stderr_bytes.decode(errors="replace").strip()
            logger.warning(
                "ffmpeg for camera %d exited (code=%s): %s",
                camera_id,
                retcode,
                stderr_text[-500:] if stderr_text else "(no output)",
            )

            # Wait before restarting to avoid tight loops
            await asyncio.sleep(10)
            if self._running:
                logger.info("Restarting ffmpeg for camera %d", camera_id)
                await self._start_camera(camera_id)
                return  # new _watch task was created by _start_camera

    async def _upload_worker(self) -> None:
        """Periodically upload completed segments to Google Drive."""
        while self._running:
            await asyncio.sleep(UPLOAD_INTERVAL)
            if not self._gdrive:
                continue

            base = Path(settings.recordings_local_path)
            for cam_dir in base.iterdir():
                if not cam_dir.is_dir():
                    continue

                camera_id = int(cam_dir.name)
                mp4_files = sorted(cam_dir.glob("*.mp4"))

                # Skip the newest file — ffmpeg is still writing to it
                completed = mp4_files[:-1] if len(mp4_files) > 1 else []

                for mp4 in completed:
                    for attempt in range(3):
                        try:
                            await self._upload_segment(camera_id, mp4)
                            mp4.unlink()
                            logger.debug("Deleted local segment %s", mp4.name)
                            break
                        except Exception as e:
                            if attempt < 2:
                                logger.warning(
                                    "Upload attempt %d failed for %s: %s — retrying",
                                    attempt + 1, mp4.name, e,
                                )
                                await asyncio.sleep(5 * (attempt + 1))
                            else:
                                logger.error(
                                    "Upload failed for %s after 3 attempts: %s",
                                    mp4.name, e,
                                )

    async def _get_folder_id(self, name: str, parent_id: str) -> str:
        """Get or create a Drive folder, using a cache to reduce API calls."""
        cache_key = f"{parent_id}/{name}"
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]
        folder_id = await asyncio.to_thread(
            self._gdrive.get_or_create_folder, name, parent_id
        )
        self._folder_cache[cache_key] = folder_id
        return folder_id

    async def _upload_segment(self, camera_id: int, mp4: Path) -> None:
        """Upload a single segment to Google Drive."""
        camera_name = self._camera_names.get(camera_id, f"camera_{camera_id}")

        # Parse date from filename: YYYY-MM-DD_HH-MM-SS.mp4
        date_str = mp4.stem[:10]  # "2026-02-27"
        time_str = mp4.stem[11:]  # "14-00-00"
        drive_filename = f"{time_str.replace('-', ':')}.mp4"

        # Get or create folder: root → camera_name → date (cached)
        cam_folder_id = await self._get_folder_id(
            camera_name, settings.gdrive_folder_id
        )
        date_folder_id = await self._get_folder_id(date_str, cam_folder_id)
        await asyncio.to_thread(
            self._gdrive.upload_file, mp4, date_folder_id, drive_filename
        )

    async def _cleanup_worker(self) -> None:
        """Periodically delete old recordings from Google Drive."""
        while self._running:
            await asyncio.sleep(CLEANUP_INTERVAL)
            if not self._gdrive or settings.recording_retention_days <= 0:
                continue

            try:
                old_files = await asyncio.to_thread(
                    self._gdrive.list_old_files,
                    settings.gdrive_folder_id,
                    settings.recording_retention_days,
                )
                for f in old_files:
                    await asyncio.to_thread(self._gdrive.delete_file, f["id"])
                    logger.info("Deleted old recording from Drive: %s", f["name"])
                if old_files:
                    logger.info(
                        "Cleanup: removed %d old recording(s) from Drive",
                        len(old_files),
                    )
            except Exception as e:
                logger.error("Cleanup failed: %s", e)


recording_manager = RecordingManager()
