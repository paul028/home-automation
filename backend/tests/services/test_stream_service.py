"""Unit tests for StreamService — go2rtc stream registration and URL generation."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

from app.core.exceptions import StreamError
from app.services.stream_service import StreamService


# ---------------------------------------------------------------------------
# _stream_name
# ---------------------------------------------------------------------------


class TestStreamName:
    def test_stream_name_CameraWithId_ReturnsExpectedFormat(self, make_camera):
        # Arrange
        service = StreamService()
        camera = make_camera(id=42)

        # Act
        name = service._stream_name(camera)

        # Assert
        assert name == "camera_42"


# ---------------------------------------------------------------------------
# _encode_cred
# ---------------------------------------------------------------------------


class TestEncodeCred:
    def test_encode_cred_PlainText_ReturnsUnchanged(self):
        # Arrange / Act
        result = StreamService._encode_cred("admin")

        # Assert
        assert result == "admin"

    def test_encode_cred_SpecialCharacters_ReturnsUrlEncoded(self):
        # Arrange / Act
        result = StreamService._encode_cred("p@ss:word")

        # Assert
        assert result == "p%40ss%3Aword"


# ---------------------------------------------------------------------------
# register_stream
# ---------------------------------------------------------------------------


class TestRegisterStream:
    async def test_register_stream_CameraWithPtz_SendsRtspOnvifAndFfmpegSources(
        self, make_camera
    ):
        # Arrange
        service = StreamService()
        camera = make_camera(id=1, has_ptz=True, username="admin", password="pass", ip_address="10.0.0.1")
        mock_response = MagicMock(status_code=200)

        with patch("app.services.stream_service.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.put = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            # Act
            await service.register_stream(camera)

            # Assert
            call_kwargs = mock_client.put.call_args
            params = call_kwargs.kwargs["params"]
            sources = [v for k, v in params if k == "src"]
            assert len(sources) == 3
            assert any("rtsp://" in s for s in sources)
            assert any("onvif://" in s for s in sources)
            assert any("ffmpeg:" in s and "#audio=aac" in s for s in sources)

    async def test_register_stream_CameraWithoutPtz_OmitsOnvifSource(
        self, make_camera
    ):
        # Arrange
        service = StreamService()
        camera = make_camera(id=2, has_ptz=False)
        mock_response = MagicMock(status_code=200)

        with patch("app.services.stream_service.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.put = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            # Act
            await service.register_stream(camera)

            # Assert
            call_kwargs = mock_client.put.call_args
            params = call_kwargs.kwargs["params"]
            sources = [v for k, v in params if k == "src"]
            assert not any("onvif://" in s for s in sources)

    async def test_register_stream_Go2rtcReturns400_RaisesStreamError(
        self, make_camera
    ):
        # Arrange
        service = StreamService()
        camera = make_camera(id=1)
        mock_response = MagicMock(status_code=400, text="Bad Request")

        with patch("app.services.stream_service.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.put = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            # Act & Assert
            with pytest.raises(StreamError, match="400"):
                await service.register_stream(camera)

    async def test_register_stream_NetworkError_RaisesStreamError(self, make_camera):
        # Arrange
        service = StreamService()
        camera = make_camera(id=1)

        with patch("app.services.stream_service.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.put = AsyncMock(side_effect=httpx.ConnectError("refused"))
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            # Act & Assert
            with pytest.raises(StreamError, match="Failed to register"):
                await service.register_stream(camera)


# ---------------------------------------------------------------------------
# unregister_stream
# ---------------------------------------------------------------------------


class TestUnregisterStream:
    async def test_unregister_stream_Success_CallsDeleteWithStreamName(
        self, make_camera
    ):
        # Arrange
        service = StreamService()
        camera = make_camera(id=5)

        with patch("app.services.stream_service.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.delete = AsyncMock(return_value=MagicMock(status_code=200))
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            # Act
            await service.unregister_stream(camera)

            # Assert
            call_kwargs = mock_client.delete.call_args
            assert call_kwargs.kwargs["params"]["name"] == "camera_5"

    async def test_unregister_stream_NetworkError_DoesNotRaise(self, make_camera):
        # Arrange
        service = StreamService()
        camera = make_camera(id=5)

        with patch("app.services.stream_service.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.delete = AsyncMock(side_effect=httpx.ConnectError("refused"))
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            # Act — should not raise
            await service.unregister_stream(camera)


# ---------------------------------------------------------------------------
# get_stream_urls
# ---------------------------------------------------------------------------


class TestGetStreamUrls:
    def test_get_stream_urls_HttpGo2rtcUrl_ReturnsWsUrls(self, make_camera):
        # Arrange
        service = StreamService()
        camera = make_camera(id=3)

        # Act
        urls = service.get_stream_urls(camera)

        # Assert
        assert urls["mse_url"].startswith("ws://")
        assert "camera_3" in urls["mse_url"]

    def test_get_stream_urls_HttpGo2rtcUrl_ReturnsHlsWithHttpScheme(self, make_camera):
        # Arrange
        service = StreamService()
        camera = make_camera(id=3)

        # Act
        urls = service.get_stream_urls(camera)

        # Assert
        assert urls["hls_url"].startswith("http://")
        assert "camera_3" in urls["hls_url"]


# ---------------------------------------------------------------------------
# get_active_streams
# ---------------------------------------------------------------------------


class TestGetActiveStreams:
    async def test_get_active_streams_Go2rtcResponds_ReturnsJsonDict(self, make_camera):
        # Arrange
        service = StreamService()
        EXPECTED_DATA = {"camera_1": {"producers": []}}

        with patch("app.services.stream_service.httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.json.return_value = EXPECTED_DATA
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            # Act
            result = await service.get_active_streams()

            # Assert
            assert result == EXPECTED_DATA

    async def test_get_active_streams_NetworkError_ReturnsEmptyDict(self):
        # Arrange
        service = StreamService()

        with patch("app.services.stream_service.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            # Act
            result = await service.get_active_streams()

            # Assert
            assert result == {}
