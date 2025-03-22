import json
import os
from pathlib import Path
from typing import Optional, Literal
import httpx
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from rich.logging import RichHandler
import logging
from functools import lru_cache
import sys
from .result import create_success, create_failure, Result
from .logger import ConfigModel, setup_logger
from .storage import ensure_config_directory, load_config_file, save_config_file

# Dependency for logger
@lru_cache()
def get_logger() -> logging.Logger:
    """Get The Application Logger."""
    return setup_logger("state-service")

# Environment configuration
class EnvSettings(BaseModel):
    """Environment settings with validation."""
    app_name: str = "state-service"
    log_level: str = "INFO"
    api_port: int = 8000
    notification_url: str = "http://localhost:8001/notify"
    
    class Config:
        env_prefix = "STATE_"

def load_env_config() -> Result[EnvSettings, str]:
    """Load configuration from environment variables."""
    try:
        config = EnvSettings()
        return create_success(config)
    except Exception as e:
        return create_failure(f"Failed to Load Environment Configuration: {str(e)}")

# API models
class ConfigUpdateRequest(BaseModel):
    """Request model for updating configuration."""
    app_name: Optional[str] = None
    log_level: Optional[str] = None
    api_port: Optional[int] = None
    notification_url: Optional[str] = None

class ConfigResponse(BaseModel):
    """Response model for configuration."""
    app_name: str
    log_level: str
    api_port: int
    notification_url: str

class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str

# Notification service
async def notify_config_change(config: ConfigModel, logger: logging.Logger) -> Result[None, str]:
    """Notify another service about configuration changes."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.notification_url,
                json={"event": "config_changed", "data": config.model_dump()}
            )
            response.raise_for_status()
        return create_success(None)
    except Exception as e:
        logger.error(f"Failed to notify about config change: {str(e)}")
        return create_failure(f"Failed to notify about config change: {str(e)}")

# Configuration service
class ConfigService:
    """Service class to handle configuration operations."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def get_config(self) -> Result[ConfigModel, str]:
        """Get the current configuration."""
        self.logger.info("Retrieving configuration")
        
        dir_result = ensure_config_directory()
        if dir_result.status == "failure":
            self.logger.error(dir_result.error)
            return create_failure(dir_result.error)
        
        config_path = dir_result.data / "config.json"
        return load_config_file(config_path)
    
    def update_config(self, update: ConfigUpdateRequest) -> Result[ConfigModel, str]:
        """Update the configuration with provided values."""
        self.logger.info(f"Updating configuration: {update}")
        
        dir_result = ensure_config_directory()
        if dir_result.status == "failure":
            self.logger.error(dir_result.error)
            return create_failure(dir_result.error)
        
        config_path = dir_result.data / "config.json"
        config_result = load_config_file(config_path)
        
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
        save_result = save_config_file(current_config, config_path)
        if save_result.status == "failure":
            self.logger.error(save_result.error)
            return create_failure(save_result.error)
        
        return create_success(current_config)
    
    async def notify_config_change(self, config: ConfigModel) -> Result[None, str]:
        """Notify another service about configuration changes."""
        return await notify_config_change(config, self.logger)

# Dependency for config service
@lru_cache()
def get_config_service(logger: logging.Logger = Depends(get_logger)) -> ConfigService:
    """Get the configuration service instance."""
    return ConfigService(logger)

# Application setup
app = FastAPI(title="State Service API")

@app.get("/config", response_model=ConfigResponse, responses={500: {"model": ErrorResponse}})
async def get_config(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get the current configuration."""
    result = config_service.get_config()
    
    if result.status == "failure":
        raise HTTPException(status_code=500, detail=result.error)
    
    return result.data

@app.patch("/config", response_model=ConfigResponse, responses={500: {"model": ErrorResponse}})
async def update_config(
    update: ConfigUpdateRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update the configuration."""
    result = config_service.update_config(update)
    
    if result.status == "failure":
        raise HTTPException(status_code=500, detail=result.error)
    
    # Notify about the configuration change
    notify_result = await config_service.notify_config_change(result.data)
    if notify_result.status == "failure":
        config_service.logger.warning(f"Failed to notify about config change: {notify_result.error}")
    
    return result.data

def main():
    """Main entry point for the application."""
    # Load configuration from environment
    env_result = load_env_config()
    if env_result.status == "failure":
        print(f"Error: {env_result.error}", file=sys.stderr)
        sys.exit(1)
    
    env_config = env_result.data
    
    # Set up logger
    logger = setup_logger("state-service", env_config.log_level)
    logger.info("Starting state service")
    
    # Ensure config directory and file
    dir_result = ensure_config_directory()
    if dir_result.status == "failure":
        logger.error(dir_result.error)
        sys.exit(1)
    
    config_path = dir_result.data / "config.json"
    config_result = load_config_file(config_path)
    
    if config_result.status == "failure":
        logger.error(config_result.error)
        sys.exit(1)
    
    # Start the API server
    logger.info(f"Starting API server on port {env_config.api_port}")
    uvicorn.run(app, host="0.0.0.0", port=env_config.api_port)


if __name__ == "__main__":
    main()
