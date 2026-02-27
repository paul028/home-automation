from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Home Automation Dashboard"
    database_url: str = "sqlite+aiosqlite:///./home_automation.db"
    go2rtc_url: str = "http://localhost:1984"
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
