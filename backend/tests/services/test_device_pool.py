"""Unit tests for DevicePool and PTZPool — connection caching with TTL and suspension."""

import time

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.exceptions import DeviceConnectionError
from app.services.device_pool import (
    DevicePool,
    PTZPool,
    _Entry,
    _Suspension,
    _parse_suspension_seconds,
    SESSION_TTL,
)


# ---------------------------------------------------------------------------
# _parse_suspension_seconds
# ---------------------------------------------------------------------------


class TestParseSuspensionSeconds:
    def test_parse_suspension_seconds_ValidMessage_ReturnsSeconds(self):
        # Arrange
        ERROR_MSG = "Temporary Suspension: Try again in 1800 seconds"

        # Act
        result = _parse_suspension_seconds(ERROR_MSG)

        # Assert
        assert result == 1800

    def test_parse_suspension_seconds_NoMatch_ReturnsNone(self):
        # Arrange
        ERROR_MSG = "Connection timed out"

        # Act
        result = _parse_suspension_seconds(ERROR_MSG)

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# _Entry
# ---------------------------------------------------------------------------


class TestEntry:
    def test_is_expired_FreshEntry_ReturnsFalse(self):
        # Arrange
        entry = _Entry(MagicMock())

        # Act / Assert
        assert entry.is_expired() is False

    def test_is_expired_OldEntry_ReturnsTrue(self):
        # Arrange
        entry = _Entry(MagicMock())
        entry.created_at = time.monotonic() - SESSION_TTL - 1

        # Act / Assert
        assert entry.is_expired() is True


# ---------------------------------------------------------------------------
# _Suspension
# ---------------------------------------------------------------------------


class TestSuspension:
    def test_is_active_FutureSuspension_ReturnsTrue(self):
        # Arrange
        suspension = _Suspension(time.monotonic() + 100)

        # Act / Assert
        assert suspension.is_active() is True

    def test_is_active_ExpiredSuspension_ReturnsFalse(self):
        # Arrange
        suspension = _Suspension(time.monotonic() - 1)

        # Act / Assert
        assert suspension.is_active() is False

    def test_remaining_seconds_ActiveSuspension_ReturnsPositive(self):
        # Arrange
        suspension = _Suspension(time.monotonic() + 60)

        # Act
        remaining = suspension.remaining_seconds()

        # Assert
        assert remaining > 0
        assert remaining <= 60


# ---------------------------------------------------------------------------
# DevicePool.get
# ---------------------------------------------------------------------------


class TestDevicePoolGet:
    async def test_get_FirstCall_CreatesNewConnection(self, make_camera):
        # Arrange
        pool = DevicePool()
        camera = make_camera(ip_address="10.0.0.1")

        with patch("app.services.device_pool.TapoCamera") as MockTapo:
            mock_tapo = AsyncMock()
            mock_tapo.connect = AsyncMock()
            MockTapo.return_value = mock_tapo

            # Act
            result = await pool.get(camera)

            # Assert
            assert result is mock_tapo
            mock_tapo.connect.assert_awaited_once()

    async def test_get_CachedSession_ReturnsSameInstance(self, make_camera):
        # Arrange
        pool = DevicePool()
        camera = make_camera(ip_address="10.0.0.1")

        with patch("app.services.device_pool.TapoCamera") as MockTapo:
            mock_tapo = AsyncMock()
            mock_tapo.connect = AsyncMock()
            MockTapo.return_value = mock_tapo

            # Act
            first = await pool.get(camera)
            second = await pool.get(camera)

            # Assert
            assert first is second
            assert mock_tapo.connect.await_count == 1

    async def test_get_ExpiredSession_CreatesNewConnection(self, make_camera):
        # Arrange
        pool = DevicePool()
        camera = make_camera(ip_address="10.0.0.1")

        with patch("app.services.device_pool.TapoCamera") as MockTapo:
            mock_tapo = AsyncMock()
            mock_tapo.connect = AsyncMock()
            MockTapo.return_value = mock_tapo

            await pool.get(camera)
            # Force expiration
            pool._pool["10.0.0.1"].created_at = time.monotonic() - SESSION_TTL - 1

            # Act
            await pool.get(camera)

            # Assert
            assert mock_tapo.connect.await_count == 2

    async def test_get_ActiveSuspension_RaisesDeviceConnectionError(self, make_camera):
        # Arrange
        pool = DevicePool()
        camera = make_camera(ip_address="10.0.0.1")
        pool._suspensions["10.0.0.1"] = _Suspension(time.monotonic() + 300)

        # Act & Assert
        with pytest.raises(DeviceConnectionError, match="temporarily suspended"):
            await pool.get(camera)

    async def test_get_ConnectRaisesSuspension_CachesSuspension(self, make_camera):
        # Arrange
        pool = DevicePool()
        camera = make_camera(ip_address="10.0.0.1")

        with patch("app.services.device_pool.TapoCamera") as MockTapo:
            mock_tapo = AsyncMock()
            mock_tapo.connect = AsyncMock(
                side_effect=Exception("Temporary Suspension: Try again in 1800 seconds")
            )
            MockTapo.return_value = mock_tapo

            # Act & Assert
            with pytest.raises(Exception):
                await pool.get(camera)

            assert "10.0.0.1" in pool._suspensions


# ---------------------------------------------------------------------------
# DevicePool.remove / invalidate
# ---------------------------------------------------------------------------


class TestDevicePoolRemove:
    async def test_remove_CachedCamera_RemovesFromPool(self, make_camera):
        # Arrange
        pool = DevicePool()
        camera = make_camera(ip_address="10.0.0.1")

        with patch("app.services.device_pool.TapoCamera") as MockTapo:
            mock_tapo = AsyncMock()
            mock_tapo.connect = AsyncMock()
            MockTapo.return_value = mock_tapo
            await pool.get(camera)

            # Act
            pool.remove("10.0.0.1")

            # Assert
            assert "10.0.0.1" not in pool._pool

    def test_remove_UnknownIp_DoesNotRaise(self):
        # Arrange
        pool = DevicePool()

        # Act & Assert — should not raise
        pool.remove("10.0.0.99")

    def test_invalidate_CallsRemove(self):
        # Arrange
        pool = DevicePool()
        pool._pool["10.0.0.1"] = MagicMock()

        # Act
        pool.invalidate("10.0.0.1")

        # Assert
        assert "10.0.0.1" not in pool._pool


# ---------------------------------------------------------------------------
# PTZPool.get
# ---------------------------------------------------------------------------


class TestPTZPoolGet:
    async def test_get_FirstCall_CreatesNewClient(self, make_camera):
        # Arrange
        pool = PTZPool()
        camera = make_camera(ip_address="10.0.0.1")

        with patch("app.services.device_pool.OnvifPTZClient") as MockPTZ:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            MockPTZ.return_value = mock_client

            # Act
            result = await pool.get(camera)

            # Assert
            assert result is mock_client
            mock_client.connect.assert_awaited_once()

    async def test_get_CachedClient_ReturnsSameInstance(self, make_camera):
        # Arrange
        pool = PTZPool()
        camera = make_camera(ip_address="10.0.0.1")

        with patch("app.services.device_pool.OnvifPTZClient") as MockPTZ:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            MockPTZ.return_value = mock_client

            # Act
            first = await pool.get(camera)
            second = await pool.get(camera)

            # Assert
            assert first is second
            assert mock_client.connect.await_count == 1
