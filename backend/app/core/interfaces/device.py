from abc import ABC, abstractmethod


class IDevice(ABC):
    """Base interface for all IoT devices."""

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the device."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the device."""
        ...

    @abstractmethod
    async def get_status(self) -> dict:
        """Get current device status."""
        ...

    @abstractmethod
    def get_device_info(self) -> dict:
        """Get static device information (model, firmware, etc.)."""
        ...
