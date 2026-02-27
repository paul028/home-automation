from datetime import date

from app.core.interfaces.device import IDevice
from app.core.interfaces.streamable import IStreamable
from app.core.interfaces.controllable import IControllable, PTZDirection, PTZAction
from app.core.interfaces.recordable import IRecordable
from app.core.exceptions import DeviceConnectionError
from app.devices.tapo.tapo_client import TapoClient


class TapoCamera(IDevice, IStreamable, IControllable, IRecordable):
    """Tapo camera implementation supporting all device interfaces."""

    def __init__(self, ip: str, username: str, password: str, name: str = ""):
        self._name = name
        self._tapo_client = TapoClient(ip, username, password)
        self._connected = False

    async def connect(self) -> bool:
        await self._tapo_client.connect()
        self._connected = True
        return True

    async def disconnect(self) -> None:
        self._connected = False

    async def get_status(self) -> dict:
        try:
            client = self._tapo_client.client
            info = client.getBasicInfo()
            return {
                "online": True,
                "device_info": info,
            }
        except Exception:
            return {"online": False}

    def get_device_info(self) -> dict:
        try:
            client = self._tapo_client.client
            info = client.getBasicInfo()
            return {
                "name": self._name,
                "model": info.get("device_info", {})
                .get("basic_info", {})
                .get("device_model", "Unknown"),
                "firmware": info.get("device_info", {})
                .get("basic_info", {})
                .get("sw_version", "Unknown"),
            }
        except Exception:
            return {"name": self._name, "model": "Unknown", "firmware": "Unknown"}

    # IStreamable

    def get_rtsp_url(self, stream: str = "main") -> str:
        return self._tapo_client.get_rtsp_url(stream)

    async def get_snapshot(self) -> bytes:
        raise NotImplementedError("Snapshot capture not yet implemented for Tapo cameras")

    # IControllable

    async def move(self, direction: PTZDirection, action: PTZAction) -> None:
        if not self._connected:
            raise DeviceConnectionError("Camera not connected")

        client = self._tapo_client.client

        if action == PTZAction.STOP:
            await self.stop()
            return

        direction_map = {
            PTZDirection.UP: lambda: client.moveMotor(0, 10),
            PTZDirection.DOWN: lambda: client.moveMotor(0, -10),
            PTZDirection.LEFT: lambda: client.moveMotor(-10, 0),
            PTZDirection.RIGHT: lambda: client.moveMotor(10, 0),
        }

        move_fn = direction_map.get(direction)
        if move_fn:
            move_fn()

    async def stop(self) -> None:
        pass  # pytapo movement commands are discrete steps, no continuous stop needed

    async def get_presets(self) -> list[dict]:
        try:
            client = self._tapo_client.client
            presets = client.getPresets()
            return [
                {"id": str(k), "name": v}
                for k, v in presets.items()
            ]
        except Exception:
            return []

    async def go_to_preset(self, preset_id: str) -> None:
        client = self._tapo_client.client
        client.setPreset(preset_id)

    # IRecordable

    async def get_recordings(self, recording_date: date) -> list[dict]:
        try:
            client = self._tapo_client.client
            recordings = client.getRecordings(recording_date)
            results = []
            for rec in recordings:
                results.append({
                    "start_time": rec.get("startTime", ""),
                    "end_time": rec.get("endTime", ""),
                    "duration": rec.get("duration", 0),
                })
            return results
        except Exception:
            return []

    async def get_recording_days(self, year: int, month: int) -> list[int]:
        try:
            client = self._tapo_client.client
            search_date = date(year, month, 1)
            recordings = client.getRecordings(search_date)
            days = set()
            for rec in recordings:
                start = rec.get("startTime", "")
                if start:
                    day = int(start[8:10]) if len(start) >= 10 else 0
                    if day > 0:
                        days.add(day)
            return sorted(days)
        except Exception:
            return []
