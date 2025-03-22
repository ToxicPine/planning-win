import httpx
import uvicorn
import logging
import sys
from urllib.parse import urlparse
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, model_validator
from functools import lru_cache
from .result import create_success, create_failure, Result
from .logger import setup_logger
from .storage import (
    load_config_file,
    save_config_file,
    get_config_path,
)
from .environment import load_env_config
from .models import SystemConfig, SystemConfigUpdateRequest, ErrorResponse


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
                raise ValueError("URL Must Have A Scheme And Host")
            return self
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")


# Notification service
async def notify_config_change(
    config: SystemConfig, notification_url: str, logger: logging.Logger
) -> Result[None, str]:
    """Notify Another Service About Configuration Changes."""
    try:
        logger.info(f"Notifying {notification_url} about configuration change")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                notification_url,
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

    def __init__(self, logger: logging.Logger, notification_url: str):
        self.logger = logger
        self.notification_url = notification_url

    def get_config(self) -> Result[SystemConfig, str]:
        """Get The Current Configuration."""
        self.logger.info("Retrieving Configuration")

        config_path_result = get_config_path()
        if config_path_result.status == "failure":
            self.logger.error(config_path_result.error)
            return create_failure(config_path_result.error)

        return load_config_file(config_path_result.data)

    def update_config(
        self, update: SystemConfigUpdateRequest
    ) -> Result[SystemConfig, str]:
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

    async def notify_config_change(self) -> Result[None, str]:
        """Notify Another Service about Configuration Changes."""
        config_result = self.get_config()
        if config_result.status == "failure":
            self.logger.error(config_result.error)
            return create_failure(config_result.error)

        return await notify_config_change(config_result.data, self.notification_url, self.logger)


# Application setup
app = FastAPI(title="State Service API")

# Store environment config at app state level
app.state.env_config = None

# Dependency to get notification URL
def get_notification_url():
    """Get Notification URL From Environment Configuration."""
    if app.state.env_config is None:
        raise RuntimeError("Environment Configuration Not Initialized")
    return app.state.env_config.SPLITUP_STATE_SERVICE_NOTIFICATION_URL

# Dependency for config service
def get_config_service(
    logger: logging.Logger = Depends(get_logger),
    notification_url: str = Depends(get_notification_url)
) -> ConfigService:
    """Get The Configuration Service Instance."""
    return ConfigService(logger, notification_url)


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
    notify_result = await config_service.notify_config_change()
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

    # Store environment config in app state
    app.state.env_config = env_result.data

    # Set Up Logger
    logger = setup_logger("state-service", app.state.env_config.SPLITUP_STATE_SERVICE_LOG_LEVEL)
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
        f"Starting API Server on Port {app.state.env_config.SPLITUP_STATE_SERVICE_API_PORT}"
    )
    uvicorn.run(app, host="0.0.0.0", port=app.state.env_config.SPLITUP_STATE_SERVICE_API_PORT)


if __name__ == "__main__":
    main()
