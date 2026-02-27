from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Home Automation Dashboard"
    database_url: str = "sqlite+aiosqlite:///./home_automation.db"
    go2rtc_url: str = "http://localhost:1984"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Continuous recording
    recording_enabled: bool = False
    recordings_local_path: str = "/tmp/ha-recordings"
    recording_segment_seconds: int = 300  # 5 minutes
    recording_retention_days: int = 30

    # Google Drive upload
    gdrive_credentials_path: str = ""
    gdrive_folder_id: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
