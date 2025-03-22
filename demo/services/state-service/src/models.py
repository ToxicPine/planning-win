from pydantic import BaseModel
from typing import Optional


class SystemConfig(BaseModel):
    """Response Model for Configuration."""

    app_name: str
    log_level: str
    api_port: int
    notification_url: str


def DefaultConfig() -> SystemConfig:
    """Return default configuration values."""
    return SystemConfig(
        app_name="state-service",
        log_level="INFO",
        api_port=8000,
        notification_url="http://localhost:8001/notify"
    )


# API models
class SystemConfigUpdateRequest(BaseModel):
    """Request model for updating configuration."""

    app_name: Optional[str] = None
    log_level: Optional[str] = None
    api_port: Optional[int] = None
    notification_url: Optional[str] = None


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str 