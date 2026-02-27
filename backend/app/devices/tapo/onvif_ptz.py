import logging
import os

from onvif import ONVIFCamera

logger = logging.getLogger(__name__)

WSDL_DIR = os.path.join(os.path.dirname(__import__("onvif").__file__), "wsdl")

# Relative move step size (0.0 to 1.0) — small value for micro-movements
STEP_SIZE = 0.05

DIRECTION_MAP = {
    "up": (0, STEP_SIZE),
    "down": (0, -STEP_SIZE),
    "left": (-STEP_SIZE, 0),
    "right": (STEP_SIZE, 0),
}


class OnvifPTZClient:
    """ONVIF-based PTZ control for Tapo cameras."""

    def __init__(self, ip: str, port: int, username: str, password: str):
        self._ip = ip
        self._port = port
        self._username = username
        self._password = password
        self._camera: ONVIFCamera | None = None
        self._ptz_service = None
        self._profile_token: str | None = None

    async def connect(self) -> None:
        self._camera = ONVIFCamera(
            self._ip, self._port, self._username, self._password, WSDL_DIR
        )
        await self._camera.update_xaddrs()
        self._ptz_service = await self._camera.create_ptz_service()
        media_service = await self._camera.create_media_service()
        profiles = await media_service.GetProfiles()
        self._profile_token = profiles[0].token

    async def move(self, direction: str) -> None:
        if not self._ptz_service or not self._profile_token:
            raise RuntimeError("Not connected")

        coords = DIRECTION_MAP.get(direction)
        if not coords:
            raise ValueError(f"Unknown direction: {direction}")

        request = self._ptz_service.create_type("RelativeMove")
        request.ProfileToken = self._profile_token
        request.Translation = {
            "PanTilt": {"x": coords[0], "y": coords[1]},
        }
        await self._ptz_service.RelativeMove(request)

    async def stop(self) -> None:
        if self._ptz_service and self._profile_token:
            await self._ptz_service.Stop({"ProfileToken": self._profile_token})
