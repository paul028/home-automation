import asyncio
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response

from app.api.dependencies import get_camera_service, get_recording_service
from app.core.exceptions import DeviceNotFoundError
from app.services.camera_service import CameraService
from app.services.recording_service import RecordingService, _get_gdrive

router = APIRouter()


def _parse_range(range_header: str, file_size: int) -> tuple[int, int]:
    """Parse a Range header like 'bytes=0-1023' into (start, end)."""
    match = re.match(r"bytes=(\d+)-(\d*)", range_header)
    if not match:
        return 0, file_size - 1
    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) else file_size - 1
    return start, min(end, file_size - 1)


@router.get("/play/{file_id}")
async def play_recording(file_id: str, request: Request):
    """Proxy a Google Drive recording file with Range request support."""
    gdrive = _get_gdrive()
    if not gdrive:
        raise HTTPException(status_code=503, detail="Google Drive not configured")

    file_size = await asyncio.to_thread(gdrive.get_file_size, file_id)

    range_header = request.headers.get("range")
    if range_header:
        start, end = _parse_range(range_header, file_size)
        content = await asyncio.to_thread(gdrive.download_bytes, file_id, start, end)
        return Response(
            content=content,
            status_code=206,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(end - start + 1),
                "Accept-Ranges": "bytes",
                "Content-Type": "video/mp4",
            },
        )

    content = await asyncio.to_thread(gdrive.download_bytes, file_id)
    return Response(
        content=content,
        status_code=200,
        headers={
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
            "Content-Type": "video/mp4",
        },
    )


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
