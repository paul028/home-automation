"""Shared test fixtures for the Home Automation backend."""

from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.camera import Camera


@pytest.fixture
async def db_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create a fresh database session for each test."""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
def sample_camera_data():
    """Return a dict of valid camera creation data."""
    return {
        "name": "Front Yard",
        "ip_address": "192.168.1.100",
        "username": "admin",
        "password": "secret123",
        "model": "C520WS",
        "location": "Front Yard",
        "brand": "tapo",
        "has_ptz": True,
        "has_recording": True,
    }


@pytest.fixture
async def saved_camera(db_session, sample_camera_data):
    """Insert and return a camera ORM instance in the test database."""
    camera = Camera(**sample_camera_data)
    db_session.add(camera)
    await db_session.commit()
    await db_session.refresh(camera)
    return camera


@pytest.fixture
def make_camera():
    """Factory fixture to build lightweight camera-like objects without a DB session."""
    def _make(**overrides):
        defaults = {
            "id": 1,
            "name": "Test Camera",
            "ip_address": "192.168.1.50",
            "username": "admin",
            "password": "pass",
            "model": "C220",
            "location": "Living Room",
            "brand": "tapo",
            "has_ptz": True,
            "has_recording": True,
            "recording_segment_seconds": None,
            "is_active": True,
        }
        defaults.update(overrides)
        return SimpleNamespace(**defaults)
    return _make
