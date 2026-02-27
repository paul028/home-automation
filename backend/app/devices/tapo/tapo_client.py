from pytapo import Tapo

from app.core.exceptions import DeviceConnectionError, DeviceAuthenticationError


class TapoClient:
    """Wrapper around pytapo library for Tapo camera communication."""

    def __init__(self, ip: str, username: str, password: str):
        self._ip = ip
        self._username = username
        self._password = password
        self._client: Tapo | None = None

    async def connect(self) -> Tapo:
        """Create and return a pytapo client instance."""
        try:
            self._client = Tapo(self._ip, self._username, self._password)
            return self._client
        except Exception as e:
            error_msg = str(e).lower()
            if "unauthorized" in error_msg or "auth" in error_msg:
                raise DeviceAuthenticationError(
                    f"Authentication failed for camera at {self._ip}"
                ) from e
            raise DeviceConnectionError(
                f"Failed to connect to camera at {self._ip}: {e}"
            ) from e

    @property
    def client(self) -> Tapo:
        if self._client is None:
            raise DeviceConnectionError("Not connected. Call connect() first.")
        return self._client

    def get_rtsp_url(self, stream: str = "main") -> str:
        """Build RTSP URL for the camera.

        Args:
            stream: 'main' for high quality (stream1), 'sub' for low quality (stream2).
        """
        stream_path = "stream1" if stream == "main" else "stream2"
        return f"rtsp://{self._username}:{self._password}@{self._ip}:554/{stream_path}"
