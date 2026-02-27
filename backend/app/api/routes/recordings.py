from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_camera_service, get_recording_service
from app.core.exceptions import DeviceNotFoundError
from app.services.camera_service import CameraService
from app.services.recording_service import RecordingService

router = APIRouter()


@router.get("/{camera_id}")
async def get_recordings(
    camera_id: int,
    recording_date: date = Query(..., description="Date in YYYY-MM-DD format"),
    camera_service: CameraService = Depends(get_camera_service),
    recording_service: RecordingService = Depends(get_recording_service),
):
    """Get recordings for a camera on a specific date."""
    try:
        camera = await camera_service.get_by_id(camera_id)
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return await recording_service.get_recordings(camera, recording_date)


@router.get("/{camera_id}/days")
async def get_recording_days(
    camera_id: int,
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    camera_service: CameraService = Depends(get_camera_service),
    recording_service: RecordingService = Depends(get_recording_service),
):
    """Get days in a month that have recordings for a camera."""
    try:
        camera = await camera_service.get_by_id(camera_id)
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    days = await recording_service.get_recording_days(camera, year, month)
    return {"camera_id": camera_id, "year": year, "month": month, "days": days}
