# Read application and database settings from environment variables and .env.
# The cached settings object is shared by imports throughout the API.

from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr, model_validator
from functools import lru_cache
from typing import Literal


# Validate required database settings when the application configuration is loaded.
class Settings(BaseSettings):
    APP_NAME: str = "Student Mapping API"
    AUTH_REQUIRED: bool = True
    AUTH_SESSION_HOURS: int = Field(default=168, ge=1, le=720)

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: SecretStr
    DB_NAME: str

    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    ALLOW_LOCAL_FILE_PATHS: bool = True
    MAX_UPLOAD_BYTES: int = Field(default=100 * 1024 * 1024, gt=0)
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_SAMESITE: Literal["lax", "none", "strict"] = "lax"

    @model_validator(mode="after")
    def validate_browser_security(self):
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if not origins or "*" in origins:
            raise ValueError("CORS_ORIGINS must contain explicit frontend origins.")
        if self.SESSION_COOKIE_SAMESITE == "none" and not self.SESSION_COOKIE_SECURE:
            raise ValueError("SESSION_COOKIE_SAMESITE=none requires SESSION_COOKIE_SECURE=true.")
        return self

    # Read settings from the local .env file.
    class Config:
        env_file = ".env"
        hide_input_in_errors = True


# Load validated settings once; lru_cache reuses the object on subsequent calls.
@lru_cache
def get_settings():
    return Settings()


settings = get_settings()

# Purpose: Loads and validates backend settings from environment variables.
# Its public interface includes Settings, get_settings.
# It keeps environment and infrastructure setup separate from request handling.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.api.session_cookie, app.config.database, app.main.
# It also has 5 additional direct importers in the backend.
# Tests and higher-level workflows exercise this behavior through its public callers.
