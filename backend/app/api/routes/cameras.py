import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_camera_service, get_stream_service

logger = logging.getLogger(__name__)
from app.core.exceptions import DeviceNotFoundError, DeviceConnectionError
from app.services.device_pool import device_pool, ptz_pool
from app.models.schemas import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraDetailResponse,
    PTZCommand,
)
from app.services.camera_service import CameraService
from app.services.stream_service import StreamService

router = APIRouter()


@router.get("", response_model=list[CameraResponse])
async def list_cameras(
    service: CameraService = Depends(get_camera_service),
):
    return await service.get_all()


@router.get("/locations")
async def list_locations(
    service: CameraService = Depends(get_camera_service),
) -> list[str]:
    return await service.get_locations()


@router.get("/{camera_id}", response_model=CameraDetailResponse)
async def get_camera(
    camera_id: int,
    service: CameraService = Depends(get_camera_service),
):
    try:
        return await service.get_by_id(camera_id)
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=CameraResponse, status_code=201)
async def create_camera(
    data: CameraCreate,
    camera_service: CameraService = Depends(get_camera_service),
    stream_service: StreamService = Depends(get_stream_service),
):
    camera = await camera_service.create(data)
    try:
        await stream_service.register_stream(camera)
    except Exception:
        pass  # go2rtc may not be running yet; stream registered on next access
    return camera


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    data: CameraUpdate,
    camera_service: CameraService = Depends(get_camera_service),
    stream_service: StreamService = Depends(get_stream_service),
):
    try:
        old_camera = await camera_service.get_by_id(camera_id)
        camera = await camera_service.update(camera_id, data)
        if data.ip_address or data.username or data.password:
            device_pool.invalidate(old_camera.ip_address)
            try:
                await stream_service.register_stream(camera)
            except Exception:
                pass
        return camera
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{camera_id}", status_code=204)
async def delete_camera(
    camera_id: int,
    camera_service: CameraService = Depends(get_camera_service),
    stream_service: StreamService = Depends(get_stream_service),
):
    try:
        camera = await camera_service.get_by_id(camera_id)
        device_pool.invalidate(camera.ip_address)
        await stream_service.unregister_stream(camera)
        await camera_service.delete(camera_id)
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{camera_id}/ptz")
async def ptz_control(
    camera_id: int,
    command: PTZCommand,
    camera_service: CameraService = Depends(get_camera_service),
):
    """Control camera pan/tilt/zoom."""
    try:
        camera = await camera_service.get_by_id(camera_id)
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not camera.has_ptz:
        raise HTTPException(status_code=400, detail="Camera does not support PTZ")

    try:
        ptz = await ptz_pool.get(camera)
        if command.action == "stop":
            await ptz.stop()
        else:
            await ptz.move(command.direction)
        return {"status": "ok"}
    except Exception as e:
        ptz_pool.invalidate(camera.ip_address)
        logger.error("PTZ error for camera %s: %s", camera_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"PTZ command failed: {e}")


@router.get("/{camera_id}/presets")
async def get_presets(
    camera_id: int,
    camera_service: CameraService = Depends(get_camera_service),
):
    """Get camera PTZ presets."""
    try:
        camera = await camera_service.get_by_id(camera_id)
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        tapo = await device_pool.get(camera)
        return await tapo.get_presets()
    except Exception as e:
        device_pool.invalidate(camera.ip_address)
        logger.error("Presets error for camera %s: %s", camera_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to get presets: {e}")
