import asyncio
import logging
import re
import time

from app.core.exceptions import DeviceConnectionError
from app.devices.tapo.onvif_ptz import OnvifPTZClient
from app.devices.tapo.tapo_camera import TapoCamera
from app.models.camera import Camera

logger = logging.getLogger(__name__)

# Session TTL in seconds — reconnect after this long to avoid stale sessions
SESSION_TTL = 600  # 10 minutes


class _Entry:
    __slots__ = ("camera", "created_at")

    def __init__(self, camera: TapoCamera):
        self.camera = camera
        self.created_at = time.monotonic()

    def is_expired(self) -> bool:
        return (time.monotonic() - self.created_at) > SESSION_TTL


class _Suspension:
    __slots__ = ("retry_after",)

    def __init__(self, retry_after: float):
        self.retry_after = retry_after

    def is_active(self) -> bool:
        return time.monotonic() < self.retry_after

    def remaining_seconds(self) -> int:
        return max(0, int(self.retry_after - time.monotonic()))


def _parse_suspension_seconds(error_msg: str) -> int | None:
    """Extract seconds from 'Temporary Suspension: Try again in N seconds'."""
    match = re.search(r"Try again in (\d+) seconds", error_msg)
    return int(match.group(1)) if match else None


class DevicePool:
    """Caches authenticated TapoCamera instances to avoid repeated auth handshakes."""

    def __init__(self):
        self._pool: dict[str, _Entry] = {}
        self._suspensions: dict[str, _Suspension] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock_for(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def get(self, camera: Camera) -> TapoCamera:
        key = camera.ip_address
        lock = self._lock_for(key)

        async with lock:
            # Check for active suspension before attempting connection
            suspension = self._suspensions.get(key)
            if suspension and suspension.is_active():
                remaining = suspension.remaining_seconds()
                raise DeviceConnectionError(
                    f"Camera at {key} is temporarily suspended. "
                    f"Try again in {remaining} seconds."
                )

            # Clear expired suspension
            if suspension:
                del self._suspensions[key]

            entry = self._pool.get(key)
            if entry and not entry.is_expired():
                return entry.camera

            # Expired or missing — create a fresh connection
            if entry:
                logger.debug("Session expired for %s, reconnecting", key)

            tapo = TapoCamera(
                ip=camera.ip_address,
                username=camera.username,
                password=camera.password,
                name=camera.name,
            )
            try:
                await tapo.connect()
            except Exception as e:
                # Detect suspension and cache it
                seconds = _parse_suspension_seconds(str(e))
                if seconds:
                    self._suspensions[key] = _Suspension(
                        time.monotonic() + seconds
                    )
                    logger.warning(
                        "Camera %s suspended for %d seconds", key, seconds
                    )
                raise

            self._pool[key] = _Entry(tapo)
            return tapo

    def remove(self, ip_address: str) -> None:
        self._pool.pop(ip_address, None)

    def invalidate(self, ip_address: str) -> None:
        """Force reconnect on next access (does not clear suspensions)."""
        self.remove(ip_address)


class _PtzEntry:
    __slots__ = ("client", "created_at")

    def __init__(self, client: OnvifPTZClient):
        self.client = client
        self.created_at = time.monotonic()

    def is_expired(self) -> bool:
        return (time.monotonic() - self.created_at) > SESSION_TTL


class PTZPool:
    """Caches ONVIF PTZ clients per camera IP."""

    def __init__(self):
        self._pool: dict[str, _PtzEntry] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock_for(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def get(self, camera: Camera) -> OnvifPTZClient:
        key = camera.ip_address
        lock = self._lock_for(key)

        async with lock:
            entry = self._pool.get(key)
            if entry and not entry.is_expired():
                return entry.client

            client = OnvifPTZClient(
                ip=camera.ip_address,
                port=2020,
                username=camera.username,
                password=camera.password,
            )
            await client.connect()
            self._pool[key] = _PtzEntry(client)
            return client

    def invalidate(self, ip_address: str) -> None:
        self._pool.pop(ip_address, None)


# Singleton instances
device_pool = DevicePool()
ptz_pool = PTZPool()
