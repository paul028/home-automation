from abc import ABC, abstractmethod


class IStreamable(ABC):
    """Interface for devices that provide video/audio streams."""

    @abstractmethod
    def get_rtsp_url(self, stream: str = "main") -> str:
        """Get the RTSP stream URL.

        Args:
            stream: 'main' for high quality, 'sub' for low quality.
        """
        ...

    @abstractmethod
    async def get_snapshot(self) -> bytes:
        """Capture a still image from the device."""
        ...
