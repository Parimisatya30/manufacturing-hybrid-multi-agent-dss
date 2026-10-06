from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings:
    """Application configuration."""

    APP_NAME: str = os.getenv("APP_NAME", "manufacturing-dss")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    MES_DATABASE_PATH: Path = (
        PROJECT_ROOT
        / os.getenv("MES_DATABASE_PATH", "data/raw/MES.db")
    )


settings = Settings()