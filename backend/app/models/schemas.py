from pydantic import BaseModel, Field


class CameraCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    ip_address: str = Field(..., min_length=7)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    model: str | None = None
    brand: str = "tapo"
    has_ptz: bool = False
    has_recording: bool = True


class CameraUpdate(BaseModel):
    name: str | None = None
    ip_address: str | None = None
    username: str | None = None
    password: str | None = None
    model: str | None = None
    has_ptz: bool | None = None
    has_recording: bool | None = None
    is_active: bool | None = None


class CameraResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    model: str | None
    brand: str
    has_ptz: bool
    has_recording: bool
    is_active: bool

    model_config = {"from_attributes": True}


class CameraDetailResponse(CameraResponse):
    username: str


class StreamInfo(BaseModel):
    camera_id: int
    camera_name: str
    webrtc_url: str
    mse_url: str
    hls_url: str


class PTZCommand(BaseModel):
    direction: str = Field(..., pattern="^(up|down|left|right)$")
    action: str = Field("start", pattern="^(start|stop)$")


class RecordingDay(BaseModel):
    date: str
    has_recordings: bool


class RecordingSegment(BaseModel):
    start_time: str
    end_time: str
    duration: int
