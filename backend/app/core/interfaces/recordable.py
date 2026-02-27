from abc import ABC, abstractmethod
from datetime import date


class IRecordable(ABC):
    """Interface for devices that support recording playback."""

    @abstractmethod
    async def get_recordings(self, recording_date: date) -> list[dict]:
        """Get list of recordings for a specific date."""
        ...

    @abstractmethod
    async def get_recording_days(self, year: int, month: int) -> list[int]:
        """Get days in a month that have recordings."""
        ...
