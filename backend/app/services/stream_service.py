import logging
from urllib.parse import quote

import httpx

from app.config import settings
from app.core.exceptions import StreamError
from app.models.camera import Camera

logger = logging.getLogger(__name__)


class StreamService:
    """Manages go2rtc stream registration and URL generation."""

    def __init__(self):
        self._go2rtc_url = settings.go2rtc_url

    def _stream_name(self, camera: Camera) -> str:
        return f"camera_{camera.id}"

    @staticmethod
    def _encode_cred(value: str) -> str:
        """URL-encode credentials (handles @, :, etc.)."""
        return quote(value, safe="")

    async def register_stream(self, camera: Camera) -> None:
        """Register a camera's RTSP stream (and ONVIF for PTZ) with go2rtc."""
        stream_name = self._stream_name(camera)
        user = self._encode_cred(camera.username)
        pwd = self._encode_cred(camera.password)
        rtsp_url = f"rtsp://{user}:{pwd}@{camera.ip_address}:554/stream1"

        # Build list of sources — RTSP always, ONVIF for PTZ cameras
        sources = [rtsp_url]
        if camera.has_ptz:
            sources.append(f"onvif://{user}:{pwd}@{camera.ip_address}:2020")

        try:
            async with httpx.AsyncClient() as client:
                # go2rtc PUT replaces all sources, so pass all in one call
                response = await client.put(
                    f"{self._go2rtc_url}/api/streams",
                    params=[("name", stream_name)] + [("src", s) for s in sources],
                )
                if response.status_code >= 400:
                    raise StreamError(
                        f"go2rtc returned {response.status_code}: {response.text}"
                    )
        except httpx.HTTPError as e:
            raise StreamError(f"Failed to register stream: {e}") from e

    async def unregister_stream(self, camera: Camera) -> None:
        """Remove a camera's stream from go2rtc."""
        stream_name = self._stream_name(camera)

        try:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{self._go2rtc_url}/api/streams",
                    params={"name": stream_name},
                )
        except httpx.HTTPError:
            pass  # Stream may already be removed

    def get_stream_urls(self, camera: Camera) -> dict:
        """Get browser-consumable stream URLs from go2rtc."""
        stream_name = self._stream_name(camera)
        # Replace http:// with ws:// for WebSocket URLs
        ws_base = self._go2rtc_url.replace("http://", "ws://").replace(
            "https://", "wss://"
        )

        return {
            "webrtc_url": f"{ws_base}/api/ws?src={stream_name}",
            "mse_url": f"{ws_base}/api/ws?src={stream_name}",
            "hls_url": f"{self._go2rtc_url}/api/stream.m3u8?src={stream_name}",
        }

    async def get_active_streams(self) -> dict:
        """Get all active streams from go2rtc."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self._go2rtc_url}/api/streams")
                return response.json()
        except httpx.HTTPError:
            return {}
