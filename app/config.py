from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Python Beats Music Backend"
    redis_url: str = "redis://redis:6379/0"
    database_url: str = "sqlite:///./app.db"
    upload_dir: Path = Path("/data/uploads")
    output_dir: Path = Path("/data/outputs")
    max_upload_mb: int = 200

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
