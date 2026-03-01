from sqlalchemy import Boolean, Column, Integer, String
from app.database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    ip_address = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    model = Column(String, nullable=True)
    location = Column(String, nullable=True)
    brand = Column(String, nullable=False, default="tapo")
    has_ptz = Column(Boolean, default=False)
    has_recording = Column(Boolean, default=True)
    recording_segment_seconds = Column(Integer, nullable=True, default=None)
    is_active = Column(Boolean, default=True)
