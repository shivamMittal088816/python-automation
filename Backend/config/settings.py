# Read application and database settings from environment variables and .env.
# The cached settings object is shared by imports throughout the API.

from pydantic_settings import BaseSettings
from functools import lru_cache


# Validate required database settings when the application configuration is loaded.
class Settings(BaseSettings):
    APP_NAME: str = "Student Mapping API"

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    ALLOW_LOCAL_FILE_PATHS: bool = True
    SESSION_COOKIE_SECURE: bool = True

    # Read settings from the local .env file.
    class Config:
        env_file = ".env"


# Load validated settings once; lru_cache reuses the object on subsequent calls.
@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
