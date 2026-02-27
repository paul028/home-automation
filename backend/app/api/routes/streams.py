from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_camera_service, get_stream_service
from app.core.exceptions import DeviceNotFoundError
from app.models.schemas import StreamInfo
from app.services.camera_service import CameraService
from app.services.stream_service import StreamService

router = APIRouter()


@router.get("/{camera_id}", response_model=StreamInfo)
async def get_stream_info(
    camera_id: int,
    camera_service: CameraService = Depends(get_camera_service),
    stream_service: StreamService = Depends(get_stream_service),
):
    """Get stream URLs for a camera. Registers the stream if not already active."""
    try:
        camera = await camera_service.get_by_id(camera_id)
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        await stream_service.register_stream(camera)
    except Exception:
        pass  # May already be registered

    urls = stream_service.get_stream_urls(camera)

    return StreamInfo(
        camera_id=camera.id,
        camera_name=camera.name,
        **urls,
    )


@router.get("")
async def list_active_streams(
    stream_service: StreamService = Depends(get_stream_service),
):
    """List all active streams in go2rtc."""
    return await stream_service.get_active_streams()
