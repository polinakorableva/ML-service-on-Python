from pydantic_settings import BaseSettings
from pathlib import Path

ENV_PATH = Path(__file__).parent.parent.parent / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    REDIS_URL: str
    MODEL_STORAGE_PATH: str = "./data/models"
    INITIAL_CREDITS: int = 10
    CREDITS_PER_PREDICTION: int = 1
    DASHBOARD_DB_URL: str

    class Config:
        env_file = str(ENV_PATH)  # абсолютный путь вместо ".env"

settings = Settings()