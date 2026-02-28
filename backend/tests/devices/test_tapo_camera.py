"""Unit tests for TapoCamera — device implementation with all interfaces."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date

from app.core.exceptions import DeviceConnectionError
from app.core.interfaces.controllable import PTZDirection, PTZAction
from app.devices.tapo.tapo_camera import TapoCamera


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tapo():
    """Create a TapoCamera with mocked internal client."""
    camera = TapoCamera(
        ip="192.168.1.100", username="admin", password="pass", name="Test Camera"
    )
    return camera


@pytest.fixture
def connected_tapo(tapo):
    """Return a TapoCamera with a mocked, connected pytapo client."""
    mock_client = MagicMock()
    tapo._tapo_client._client = mock_client
    tapo._connected = True
    return tapo


# ---------------------------------------------------------------------------
# IDevice — connect / disconnect / get_status
# ---------------------------------------------------------------------------


class TestConnect:
    async def test_connect_Success_ReturnsTrueAndSetsConnected(self, tapo):
        # Arrange
        with patch.object(tapo._tapo_client, "connect", new_callable=AsyncMock):
            # Act
            result = await tapo.connect()

            # Assert
            assert result is True
            assert tapo._connected is True


class TestDisconnect:
    async def test_disconnect_Connected_SetsConnectedFalse(self, connected_tapo):
        # Act
        await connected_tapo.disconnect()

        # Assert
        assert connected_tapo._connected is False


class TestGetStatus:
    async def test_get_status_OnlineCamera_ReturnsOnlineTrue(self, connected_tapo):
        # Arrange
        connected_tapo._tapo_client.client.getBasicInfo = MagicMock(
            return_value={"device_info": {}}
        )

        # Act
        status = await connected_tapo.get_status()

        # Assert
        assert status["online"] is True

    async def test_get_status_FailedCall_ReturnsOnlineFalse(self, connected_tapo):
        # Arrange
        connected_tapo._tapo_client.client.getBasicInfo = MagicMock(
            side_effect=Exception("timeout")
        )

        # Act
        status = await connected_tapo.get_status()

        # Assert
        assert status["online"] is False


# ---------------------------------------------------------------------------
# IStreamable — get_rtsp_url
# ---------------------------------------------------------------------------


class TestGetRtspUrl:
    def test_get_rtsp_url_MainStream_ReturnsStream1Url(self, tapo):
        # Act
        url = tapo.get_rtsp_url("main")

        # Assert
        assert "stream1" in url
        assert "192.168.1.100:554" in url

    def test_get_rtsp_url_SubStream_ReturnsStream2Url(self, tapo):
        # Act
        url = tapo.get_rtsp_url("sub")

        # Assert
        assert "stream2" in url


# ---------------------------------------------------------------------------
# IControllable — move / stop / get_presets
# ---------------------------------------------------------------------------


class TestMove:
    async def test_move_UpDirection_CallsMoveMotorWithPositiveY(self, connected_tapo):
        # Arrange
        mock_client = connected_tapo._tapo_client.client
        mock_client.moveMotor = MagicMock()

        # Act
        await connected_tapo.move(PTZDirection.UP, PTZAction.START)

        # Assert
        mock_client.moveMotor.assert_called_once_with(0, 10)

    async def test_move_LeftDirection_CallsMoveMotorWithNegativeX(self, connected_tapo):
        # Arrange
        mock_client = connected_tapo._tapo_client.client
        mock_client.moveMotor = MagicMock()

        # Act
        await connected_tapo.move(PTZDirection.LEFT, PTZAction.START)

        # Assert
        mock_client.moveMotor.assert_called_once_with(-10, 0)

    async def test_move_StopAction_CallsStop(self, connected_tapo):
        # Act
        await connected_tapo.move(PTZDirection.UP, PTZAction.STOP)

        # Assert — stop is a no-op for pytapo, should not raise

    async def test_move_NotConnected_RaisesDeviceConnectionError(self, tapo):
        # Arrange — tapo._connected is False by default

        # Act & Assert
        with pytest.raises(DeviceConnectionError, match="not connected"):
            await tapo.move(PTZDirection.UP, PTZAction.START)


class TestGetPresets:
    async def test_get_presets_PresetsAvailable_ReturnsList(self, connected_tapo):
        # Arrange
        connected_tapo._tapo_client.client.getPresets = MagicMock(
            return_value={"1": "Home", "2": "Gate"}
        )

        # Act
        presets = await connected_tapo.get_presets()

        # Assert
        assert len(presets) == 2
        assert presets[0] == {"id": "1", "name": "Home"}

    async def test_get_presets_ErrorOccurs_ReturnsEmptyList(self, connected_tapo):
        # Arrange
        connected_tapo._tapo_client.client.getPresets = MagicMock(
            side_effect=Exception("failed")
        )

        # Act
        presets = await connected_tapo.get_presets()

        # Assert
        assert presets == []


# ---------------------------------------------------------------------------
# IRecordable — get_recordings / get_recording_days
# ---------------------------------------------------------------------------


class TestGetRecordings:
    async def test_get_recordings_RecordingsExist_ReturnsMappedList(
        self, connected_tapo
    ):
        # Arrange
        connected_tapo._tapo_client.client.getRecordings = MagicMock(
            return_value=[
                {"startTime": "2026-02-28 14:00:00", "endTime": "2026-02-28 14:05:00", "duration": 300}
            ]
        )

        # Act
        recordings = await connected_tapo.get_recordings(date(2026, 2, 28))

        # Assert
        assert len(recordings) == 1
        assert recordings[0]["duration"] == 300

    async def test_get_recordings_ErrorOccurs_ReturnsEmptyList(self, connected_tapo):
        # Arrange
        connected_tapo._tapo_client.client.getRecordings = MagicMock(
            side_effect=Exception("error")
        )

        # Act
        recordings = await connected_tapo.get_recordings(date(2026, 2, 28))

        # Assert
        assert recordings == []


class TestGetRecordingDays:
    async def test_get_recording_days_RecordingsExist_ReturnsSortedDays(
        self, connected_tapo
    ):
        # Arrange
        connected_tapo._tapo_client.client.getRecordings = MagicMock(
            return_value=[
                {"startTime": "2026-02-15 08:00:00"},
                {"startTime": "2026-02-03 10:00:00"},
                {"startTime": "2026-02-15 12:00:00"},  # duplicate day
            ]
        )

        # Act
        days = await connected_tapo.get_recording_days(2026, 2)

        # Assert
        assert days == [3, 15]

    async def test_get_recording_days_ErrorOccurs_ReturnsEmptyList(
        self, connected_tapo
    ):
        # Arrange
        connected_tapo._tapo_client.client.getRecordings = MagicMock(
            side_effect=Exception("error")
        )

        # Act
        days = await connected_tapo.get_recording_days(2026, 2)

        # Assert
        assert days == []
