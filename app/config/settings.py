
"""Application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load the project's .env before reading environment variables.
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Application configuration."""

    APP_NAME: str = os.getenv("APP_NAME", "manufacturing-dss")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemma3:4b")
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434",
    )
    OLLAMA_TIMEOUT_SECONDS: int = int(
        os.getenv("OLLAMA_TIMEOUT_SECONDS", "120")
    )

    MES_DATABASE_PATH: Path = (
        PROJECT_ROOT
        / os.getenv("MES_DATABASE_PATH", "data/raw/MES.db")
    )


settings = Settings()