from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings

from src.core.env_manager import EnvManager


class Settings(BaseSettings):
    DATABASE_URI: str = EnvManager.get_env_variable(
        "DATABASE_URL", "sqlite:///database.db"
    )
    ASYCNC_DATABASE_URL: str = EnvManager.get_env_variable(
        "ASYNC_DATABASE_URL", "sqlite+aiosqlite:///database.db"
    )
    SECRET_KEY: str = EnvManager.get_env_variable("SECRET_KEY", "supersecretkey")
    
    PROJECT_NAME: str = EnvManager.get_env_variable(
        "PROJECT_NAME", "My FastAPI Project"
    )
    PROJECT_INFO: str = EnvManager.get_env_variable(
        "PROJECT_INFO", "My FastAPI Project"
    )
    PROJECT_VERSION: str = EnvManager.get_env_variable("PROJECT_VERSION", "1.0.0")
    TIME_ZONE: str = EnvManager.get_env_variable("TIME_ZONE", "Asia/Aden")
    UPLOAD_FOLDER: str = EnvManager.get_env_variable("UPLOAD_FOLDER", "uploads")
    STATIC_DIR: str = EnvManager.get_env_variable("STATIC_DIR", "static")

    def get_now(self):
        """Get the current time in the configured time zone."""
        tz = ZoneInfo(self.TIME_ZONE)
        return datetime.now(tz)


settings = Settings()
