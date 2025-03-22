import httpx
import uvicorn
import logging
import sys
from urllib.parse import urlparse
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, model_validator
from typing import Optional, Literal
from functools import lru_cache
from .result import create_success, create_failure, Result
from .logger import ConfigModel, setup_logger
from .storage import (
    load_config_file,
    save_config_file,
    get_config_path,
)
from .environment import load_env_config


# Dependency for logger
@lru_cache()
def get_logger() -> logging.Logger:
    """Get The Application Logger."""
    return setup_logger("state-service")


# Environment Configuration
class EnvSettings(BaseModel):
    """Environment Settings With Validation."""

    SPLITUP_STATE_SERVICE_NAME: str = "state-service"
    SPLITUP_STATE_SERVICE_LOG_LEVEL: str = "INFO"
    SPLITUP_STATE_SERVICE_API_PORT: int = 8000
    SPLITUP_STATE_SERVICE_NOTIFICATION_URL: str

    class Config:
        """Pydantic Model Configuration."""

        validate_assignment = True

    @model_validator(mode="after")
    def validate_url(self):
        """Validate That The Notification URL Is A Valid URL."""
        try:
            result = urlparse(self.SPLITUP_STATE_SERVICE_NOTIFICATION_URL)
            if not all([result.scheme, result.netloc]):
                raise ValueError("URL must have a scheme and host")
            return self
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")


class SystemConfig(BaseModel):
    """Response model for configuration."""

    app_name: str
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    api_port: int
    notification_url: str


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


# Notification service
async def notify_config_change(
    config: ConfigModel, logger: logging.Logger
) -> Result[None, str]:
    """Notify Another Service About Configuration Changes."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.notification_url,
                json={"event": "config_changed", "data": config.model_dump()},
            )
            response.raise_for_status()
        return create_success(None)
    except Exception as e:
        logger.error(f"Failed to Notify About Configuration Change: {str(e)}")
        return create_failure(f"Failed to Notify About Configuration Change: {str(e)}")


# Configuration service
class ConfigService:
    """Service Class To Handle Configuration Operations."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def get_config(self) -> Result[ConfigModel, str]:
        """Get The Current Configuration."""
        self.logger.info("Retrieving Configuration")

        config_path_result = get_config_path()
        if config_path_result.status == "failure":
            self.logger.error(config_path_result.error)
            return create_failure(config_path_result.error)

        return load_config_file(config_path_result.data)

    def update_config(
        self, update: SystemConfigUpdateRequest
    ) -> Result[ConfigModel, str]:
        """Update The Configuration with Provided Values."""
        self.logger.info(f"Updating Configuration: {update}")

        config_path_result = get_config_path()
        if config_path_result.status == "failure":
            self.logger.error(config_path_result.error)
            return create_failure(config_path_result.error)

        config_result = load_config_file(config_path_result.data)

        if config_result.status == "failure":
            self.logger.error(config_result.error)
            return create_failure(config_result.error)

        current_config = config_result.data

        # Update only the fields that are provided
        update_dict = update.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(current_config, key, value)

        # Save the updated configuration
        save_result = save_config_file(current_config, config_path_result.data)
        if save_result.status == "failure":
            self.logger.error(save_result.error)
            return create_failure(save_result.error)

        return create_success(current_config)

    async def notify_config_change(self, config: ConfigModel) -> Result[None, str]:
        """Notify Another Service about Configuration Changes."""
        return await notify_config_change(config, self.logger)


# Dependency for config service
@lru_cache()
def get_config_service(logger: logging.Logger = Depends(get_logger)) -> ConfigService:
    """Get The Configuration Service Instance."""
    return ConfigService(logger)


# Application setup
app = FastAPI(title="State Service API")


@app.get(
    "/config", response_model=SystemConfig, responses={500: {"model": ErrorResponse}}
)
async def get_config(config_service: ConfigService = Depends(get_config_service)):
    """Get The Current Configuration."""
    result = config_service.get_config()

    if result.status == "failure":
        raise HTTPException(status_code=500, detail=result.error)

    return result.data


@app.patch(
    "/config", response_model=SystemConfig, responses={500: {"model": ErrorResponse}}
)
async def update_config(
    update: SystemConfigUpdateRequest,
    config_service: ConfigService = Depends(get_config_service),
):
    """Update The Configuration."""
    result = config_service.update_config(update)

    if result.status == "failure":
        raise HTTPException(status_code=500, detail=result.error)

    # Notify About The Configuration Change
    notify_result = await config_service.notify_config_change(result.data)
    if notify_result.status == "failure":
        config_service.logger.warning(
            f"Failed to Notify About Configuration Change: {notify_result.error}"
        )

    return result.data


def main():
    """Main Entry Point For The Application."""
    # Load Configuration From Environment
    env_result = load_env_config(EnvSettings)
    if env_result.status == "failure":
        print(f"Error: {env_result.error}", file=sys.stderr)
        sys.exit(1)

    env_config = env_result.data

    # Set Up Logger
    logger = setup_logger("state-service", env_config.SPLITUP_STATE_SERVICE_LOG_LEVEL)
    logger.info("Starting State Service")

    # Ensure Config Directory And File
    config_path_result = get_config_path()
    if config_path_result.status == "failure":
        logger.error(config_path_result.error)
        sys.exit(1)

    config_result = load_config_file(config_path_result.data)

    if config_result.status == "failure":
        logger.error(config_result.error)
        sys.exit(1)

    # Start the API server
    logger.info(
        f"Starting API Server on Port {env_config.SPLITUP_STATE_SERVICE_API_PORT}"
    )
    uvicorn.run(app, host="0.0.0.0", port=env_config.SPLITUP_STATE_SERVICE_API_PORT)


if __name__ == "__main__":
    main()
