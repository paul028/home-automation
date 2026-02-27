from abc import ABC, abstractmethod
from enum import Enum


class PTZDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class PTZAction(str, Enum):
    START = "start"
    STOP = "stop"


class IControllable(ABC):
    """Interface for devices with pan/tilt/zoom controls."""

    @abstractmethod
    async def move(self, direction: PTZDirection, action: PTZAction) -> None:
        """Move the camera in a direction."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop all movement."""
        ...

    @abstractmethod
    async def get_presets(self) -> list[dict]:
        """Get saved position presets."""
        ...

    @abstractmethod
    async def go_to_preset(self, preset_id: str) -> None:
        """Move camera to a saved preset position."""
        ...
