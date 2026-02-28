"""Unit tests for OnvifPTZClient — ONVIF-based PTZ control."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.devices.tapo.onvif_ptz import OnvifPTZClient, DIRECTION_MAP, STEP_SIZE


# ---------------------------------------------------------------------------
# DIRECTION_MAP constants
# ---------------------------------------------------------------------------


class TestDirectionMap:
    def test_direction_map_Up_HasPositiveY(self):
        # Assert
        x, y = DIRECTION_MAP["up"]
        assert x == 0
        assert y == STEP_SIZE

    def test_direction_map_Down_HasNegativeY(self):
        # Assert
        x, y = DIRECTION_MAP["down"]
        assert x == 0
        assert y == -STEP_SIZE

    def test_direction_map_Left_HasNegativeX(self):
        # Assert
        x, y = DIRECTION_MAP["left"]
        assert x == -STEP_SIZE
        assert y == 0

    def test_direction_map_Right_HasPositiveX(self):
        # Assert
        x, y = DIRECTION_MAP["right"]
        assert x == STEP_SIZE
        assert y == 0


# ---------------------------------------------------------------------------
# move
# ---------------------------------------------------------------------------


class TestMove:
    async def test_move_ValidDirection_CallsRelativeMove(self):
        # Arrange
        client = OnvifPTZClient("10.0.0.1", 2020, "admin", "pass")
        mock_ptz = AsyncMock()
        mock_request = MagicMock()
        mock_ptz.create_type = MagicMock(return_value=mock_request)
        client._ptz_service = mock_ptz
        client._profile_token = "token_1"

        # Act
        await client.move("up")

        # Assert
        mock_ptz.RelativeMove.assert_awaited_once()

    async def test_move_InvalidDirection_RaisesValueError(self):
        # Arrange
        client = OnvifPTZClient("10.0.0.1", 2020, "admin", "pass")
        client._ptz_service = AsyncMock()
        client._profile_token = "token_1"

        # Act & Assert
        with pytest.raises(ValueError, match="Unknown direction"):
            await client.move("diagonal")

    async def test_move_NotConnected_RaisesRuntimeError(self):
        # Arrange
        client = OnvifPTZClient("10.0.0.1", 2020, "admin", "pass")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Not connected"):
            await client.move("up")


# ---------------------------------------------------------------------------
# stop
# ---------------------------------------------------------------------------


class TestStop:
    async def test_stop_Connected_CallsPtzStop(self):
        # Arrange
        client = OnvifPTZClient("10.0.0.1", 2020, "admin", "pass")
        mock_ptz = AsyncMock()
        client._ptz_service = mock_ptz
        client._profile_token = "token_1"

        # Act
        await client.stop()

        # Assert
        mock_ptz.Stop.assert_awaited_once()

    async def test_stop_NotConnected_DoesNotRaise(self):
        # Arrange
        client = OnvifPTZClient("10.0.0.1", 2020, "admin", "pass")

        # Act — should not raise
        await client.stop()
