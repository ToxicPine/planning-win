import httpx
import uvicorn
import logging
import sys
import time
import platform
from datetime import datetime
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from fastapi import Depends, FastAPI, HTTPException, Body
from pydantic import BaseModel, model_validator
from functools import lru_cache
from typing import Optional, TypeVar, Dict
from .models import (
    ComputeStatus,
    StatusUpdateResponse,
    SystemConfig,
    ErrorResponse,
    ConfigResponse,
    TaskExecutionRequest,
    TaskScheduledResponse,
    HealthStatus,
    HealthCheckResponse,
    TaskScheduledData,
    ComputeResult,
    BaseResponse,
    ActiveExecutionsResponse,
)
from .result import create_success, create_failure, Result
from .logger import setup_logger
from .environment import load_env_config, EnvSettings
from .util import with_exponential_backoff
from .execution import ExecutionService
from .notification import notify_status_update

# Type variables for generic backoff function
T = TypeVar("T")
E = TypeVar("E")

# Version information
VERSION = "1.0.0"
START_TIME = time.time()


# Dependency for logger
@lru_cache()
def get_logger() -> logging.Logger:
    """Get The Application Logger."""
    return setup_logger("compute-service")


# In-memory config store
global_config: Optional[SystemConfig] = None


# Configuration service
class ConfigService:
    """Service Class To Handle Configuration Operations."""

    def __init__(self, logger: logging.Logger, config_url: str, heartbeat_url: str):
        self.logger = logger
        self.config_url = config_url
        self.heartbeat_url = heartbeat_url

    async def load_config(self) -> Result[SystemConfig, str]:
        """Get The Current Configuration From API With Retry Logic."""

        async def _fetch_config_operation() -> Result[SystemConfig, str]:
            try:
                self.logger.debug(f"Fetching Configuration From {self.config_url}")
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.config_url)
                    response.raise_for_status()

                    config = SystemConfig.model_validate(response.json())

                    global global_config
                    global_config = config
                    return create_success(config)
            except Exception as e:
                return create_failure(f"Failed to Fetch Configuration: {str(e)}")

        self.logger.info(f"Loading Configuration From {self.config_url}")
        return await with_exponential_backoff(
            operation=_fetch_config_operation,
            logger=self.logger,
            operation_name="Fetch Configuration",
        )


# Task execution service
class TaskService:
    """Service Class To Handle Task Execution."""

    def __init__(self, logger: logging.Logger, listener_url: str):
        self.logger = logger
        self.listener_url = listener_url
        self.execution_service = ExecutionService(logger, listener_url)

    async def schedule_task(
        self, request: TaskExecutionRequest
    ) -> Result[TaskScheduledResponse, str]:
        """Schedule a Task for Execution."""
        self.logger.info(
            f"Scheduling Task: {request.task_id} With Execution ID: {request.execution_id}"
        )

        try:
            # Enqueue the task for execution
            result = await self.execution_service.enqueue_task(request)

            if result.status == "failure":
                return create_failure(result.error)

            return create_success(
                TaskScheduledResponse(
                    success=True,
                    message="Task scheduled successfully",
                    data=result.data,
                )
            )
        except Exception as e:
            self.logger.error(f"Failed To Schedule Task: {str(e)}")
            return create_failure(f"Failed To Schedule Task: {str(e)}")


# Application setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application Lifespan Manager for Startup and Shutdown Events."""
    logger = setup_logger(
        "compute-service", app.state.env_config.SPLITUP_COMPUTE_SERVICE_LOG_LEVEL
    )
    logger.info("Starting Compute Service")

    # Notify that the service is online
    status = ComputeStatus(status="idle", lastUpdated=int(time.time()))

    # Notify service is starting up (with exponential backoff built into the function)
    result = await notify_status_update(
        status=status,
        heartbeat_url=app.state.env_config.SPLITUP_COMPUTE_SERVICE_HEARTBEAT_URL,
        logger=logger,
    )

    if result.status == "failure":
        logger.error(f"All Attempts To Notify Service Startup Failed: {result.error}")
    else:
        logger.info("Successfully Notified Service Startup")

    # Load initial configuration
    config_service = ConfigService(
        logger=logger,
        config_url=app.state.env_config.SPLITUP_COMPUTE_SERVICE_CONFIG_URL,
        heartbeat_url=app.state.env_config.SPLITUP_COMPUTE_SERVICE_HEARTBEAT_URL,
    )

    config_result = await config_service.load_config()
    if config_result.status == "failure":
        logger.error(
            f"All Attempts To Load Initial Configuration Failed: {config_result.error}"
        )
    else:
        logger.info("Successfully Loaded Initial Configuration")

    yield

    # Shutdown logic: notify that the service is going offline
    status = ComputeStatus(status="offline", lastUpdated=int(time.time()))

    result = await notify_status_update(
        status=status,
        heartbeat_url=app.state.env_config.SPLITUP_COMPUTE_SERVICE_HEARTBEAT_URL,
        logger=logger,
    )

    if result.status == "failure":
        logger.error(f"Failed to Notify Service Shutdown: {result.error}")
    else:
        logger.info("Successfully Notified Service Shutdown")

    logger.info("Shutting Down Compute Service")


app = FastAPI(title="Compute Service API", lifespan=lifespan)

# Store environment config at app state level
app.state.env_config = None


# Dependency to get notification URL
def get_heartbeat_url():
    """Get Notification URL From Environment Configuration."""
    if app.state.env_config is None:
        raise RuntimeError("Environment Configuration Not Initialized")
    return app.state.env_config.SPLITUP_COMPUTE_SERVICE_HEARTBEAT_URL


# Dependency to get config URL
def get_config_url():
    """Get Config URL From Environment Configuration."""
    if app.state.env_config is None:
        raise RuntimeError("Environment Configuration Not Initialized")
    return app.state.env_config.SPLITUP_COMPUTE_SERVICE_CONFIG_URL


# Dependency to get listener URL
def get_listener_url():
    """Get Result Listener URL From Environment Configuration."""
    if app.state.env_config is None:
        raise RuntimeError("Environment Configuration Not Initialized")
    return app.state.env_config.SPLITUP_COMPUTE_SERVICE_LISTENER_URL


# Dependency for config service
def get_config_service(
    logger: logging.Logger = Depends(get_logger),
    heartbeat_url: str = Depends(get_heartbeat_url),
    config_url: str = Depends(get_config_url),
) -> ConfigService:
    """Get The Configuration Service Instance."""
    return ConfigService(logger, config_url, heartbeat_url)


# Dependency for task service
def get_task_service(
    logger: logging.Logger = Depends(get_logger),
    listener_url: str = Depends(get_listener_url),
) -> TaskService:
    """Get The Task Service Instance."""
    return TaskService(logger, listener_url)


@app.post(
    "/load_config",
    response_model=ConfigResponse,
    responses={200: {"model": ConfigResponse}, 500: {"model": ErrorResponse}},
)
async def load_config(
    config_service: ConfigService = Depends(get_config_service),
):
    """Load Configuration From External Service."""
    result = await config_service.load_config()

    if result.status == "failure":
        raise HTTPException(status_code=500, detail=result.error)

    return ConfigResponse(
        success=True, message="Configuration Loaded Successfully", config=result.data
    )


@app.post(
    "/task_execution",
    response_model=TaskScheduledResponse,
    responses={200: {"model": TaskScheduledResponse}, 500: {"model": ErrorResponse}},
)
async def task_execution(
    request: TaskExecutionRequest = Body(...),
    task_service: TaskService = Depends(get_task_service),
):
    """Schedule A Task For Execution."""
    result = await task_service.schedule_task(request)

    if result.status == "failure":
        raise HTTPException(status_code=500, detail=result.error)

    return result.data


@app.get(
    "/execution/{execution_id}/status",
    response_model=ComputeResult,
    responses={
        200: {"model": ComputeResult},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def get_execution_status(
    execution_id: str,
    task_service: TaskService = Depends(get_task_service),
):
    """Get the current status of a task execution."""
    result = await task_service.execution_service.get_execution_status(execution_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Task execution not found")

    return result


@app.post(
    "/execution/{execution_id}/cancel",
    response_model=BaseResponse,
    responses={
        200: {"model": BaseResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def cancel_execution(
    execution_id: str,
    task_service: TaskService = Depends(get_task_service),
):
    """Cancel a running task execution."""
    result = await task_service.execution_service.cancel_execution(execution_id)

    if result.status == "failure":
        if "not found" in result.error.lower():
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail=result.error)

    return BaseResponse(
        success=True, message=f"Task Execution {execution_id} Cancelled Successfully"
    )


@app.get(
    "/executions/active",
    response_model=ActiveExecutionsResponse,
    responses={200: {"model": ActiveExecutionsResponse}, 500: {"model": ErrorResponse}},
)
async def list_active_executions(
    task_service: TaskService = Depends(get_task_service),
):
    """List all currently active task executions."""
    active_executions = await task_service.execution_service.list_active_executions()

    return ActiveExecutionsResponse(
        success=True,
        message=f"Found {len(active_executions)} Active Task Executions",
        data=active_executions,
    )


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    responses={200: {"model": HealthCheckResponse}, 500: {"model": ErrorResponse}},
)
async def health_check():
    """Get Health Status Of The Service."""
    try:
        uptime = int(time.time() - START_TIME)

        # Determine the system status
        status = "healthy"
        if global_config is None:
            status = "degraded"

        health_status = HealthStatus(
            status=status,
            uptime=uptime,
            version=VERSION,
            details={
                "system": platform.system(),
                "python_version": platform.python_version(),
                "config_loaded": global_config is not None,
                "start_time": datetime.fromtimestamp(START_TIME).isoformat(),
            },
        )

        return HealthCheckResponse(
            success=True,
            message="Service Health Check Successful",
            health=health_status,
        )
    except Exception as e:
        logger = get_logger()
        logger.error(f"Health Check Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health Check Failed: {str(e)}")


def main():
    """Main Entry Point For The Application."""
    # Load Configuration From Environment
    env_result = load_env_config(EnvSettings)
    if env_result.status == "failure":
        print(f"Error: {env_result.error}", file=sys.stderr)
        sys.exit(1)

    # Store environment config in app state
    app.state.env_config = env_result.data

    # Start the API server
    logger = get_logger()
    logger.info(
        f"Starting API Server on Port {app.state.env_config.SPLITUP_COMPUTE_SERVICE_API_PORT}"
    )
    uvicorn.run(
        app, host="0.0.0.0", port=app.state.env_config.SPLITUP_COMPUTE_SERVICE_API_PORT
    )


if __name__ == "__main__":
    main()
