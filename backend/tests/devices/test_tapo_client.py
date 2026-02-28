"""Unit tests for TapoClient — pytapo library wrapper."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.core.exceptions import DeviceConnectionError, DeviceAuthenticationError
from app.devices.tapo.tapo_client import TapoClient


# ---------------------------------------------------------------------------
# connect
# ---------------------------------------------------------------------------


class TestConnect:
    async def test_connect_Success_ReturnsTapoInstance(self):
        # Arrange
        client = TapoClient("10.0.0.1", "admin", "pass")
        mock_tapo = MagicMock()

        with patch("app.devices.tapo.tapo_client.Tapo", return_value=mock_tapo):
            # Act
            result = await client.connect()

            # Assert
            assert result is mock_tapo

    async def test_connect_AuthError_RaisesDeviceAuthenticationError(self):
        # Arrange
        client = TapoClient("10.0.0.1", "admin", "wrong_pass")

        with patch(
            "app.devices.tapo.tapo_client.Tapo",
            side_effect=Exception("Unauthorized access"),
        ):
            # Act & Assert
            with pytest.raises(DeviceAuthenticationError, match="Authentication failed"):
                await client.connect()

    async def test_connect_GenericError_RaisesDeviceConnectionError(self):
        # Arrange
        client = TapoClient("10.0.0.1", "admin", "pass")

        with patch(
            "app.devices.tapo.tapo_client.Tapo",
            side_effect=Exception("Connection timed out"),
        ):
            # Act & Assert
            with pytest.raises(DeviceConnectionError, match="Failed to connect"):
                await client.connect()


# ---------------------------------------------------------------------------
# client property
# ---------------------------------------------------------------------------


class TestClientProperty:
    def test_client_NotConnected_RaisesDeviceConnectionError(self):
        # Arrange
        client = TapoClient("10.0.0.1", "admin", "pass")

        # Act & Assert
        with pytest.raises(DeviceConnectionError, match="Not connected"):
            _ = client.client

    async def test_client_Connected_ReturnsInstance(self):
        # Arrange
        client = TapoClient("10.0.0.1", "admin", "pass")
        mock_tapo = MagicMock()

        with patch("app.devices.tapo.tapo_client.Tapo", return_value=mock_tapo):
            await client.connect()

            # Act
            result = client.client

            # Assert
            assert result is mock_tapo


# ---------------------------------------------------------------------------
# get_rtsp_url
# ---------------------------------------------------------------------------


class TestGetRtspUrl:
    def test_get_rtsp_url_MainStream_ReturnsStream1(self):
        # Arrange
        client = TapoClient("192.168.1.100", "admin", "secret")

        # Act
        url = client.get_rtsp_url("main")

        # Assert
        assert url == "rtsp://admin:secret@192.168.1.100:554/stream1"

    def test_get_rtsp_url_SubStream_ReturnsStream2(self):
        # Arrange
        client = TapoClient("192.168.1.100", "admin", "secret")

        # Act
        url = client.get_rtsp_url("sub")

        # Assert
        assert url == "rtsp://admin:secret@192.168.1.100:554/stream2"
