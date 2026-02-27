from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api.routes.cameras import router as cameras_router
from app.api.routes.streams import router as streams_router
from app.api.routes.recordings import router as recordings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras_router, prefix="/api/cameras", tags=["cameras"])
app.include_router(streams_router, prefix="/api/streams", tags=["streams"])
app.include_router(recordings_router, prefix="/api/recordings", tags=["recordings"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
