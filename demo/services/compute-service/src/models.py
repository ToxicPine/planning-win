from pydantic import BaseModel, model_validator
from typing import Optional, Literal, Dict, Any, List
from urllib.parse import urlparse


class SystemConfig(BaseModel):
    """System configuration model."""

    weights_data_key: str


class ComputeStatus(BaseModel):
    """Status update from compute service to heartbeat service."""

    status: Literal["offline"] | Literal["idle"] | Literal["busy"] | Literal["error"]
    lastUpdated: int


class StatusUpdateResponse(BaseModel):
    """Response to status update."""

    success: bool
    message: str


# Common response models
class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str


class BaseResponse(BaseModel):
    """Base response model with success status."""

    success: bool
    message: str


# Config endpoint models
class ConfigResponse(BaseResponse):
    """Response model for config operations."""

    config: Optional[SystemConfig] = None


# Task execution models
class TaskExecutionRequest(BaseModel):
    """Request model for task execution."""

    execution_id: str
    task_id: str
    task_storage_key: str
    parameters: List[str] = []

    @model_validator(mode="after")
    def validate_urls(self):
        """Validate That URLs Are Valid."""
        for url in self.parameters:
            try:
                result = urlparse(url)
                if not all([result.scheme, result.netloc]):
                    raise ValueError(f"URL {url} Must Have A Scheme And Host")
            except Exception as e:
                raise ValueError(f"Invalid URL {url}: {str(e)}")

        return self


class TaskScheduledData(BaseModel):
    """Data indicating a task has been successfully scheduled."""

    execution_id: str
    task_id: str
    scheduled_at: int


class TaskScheduledResponse(BaseResponse):
    """Response indicating a task has been successfully scheduled."""

    data: TaskScheduledData


# Health check models
class HealthStatus(BaseModel):
    """Health status information."""

    status: Literal["healthy", "degraded", "unhealthy"]
    uptime: int
    version: str
    details: Dict[str, Any]


class HealthCheckResponse(BaseResponse):
    """Response model for health check endpoint."""

    health: HealthStatus


# API models
class SystemConfigUpdateRequest(BaseModel):
    """Request Model For Updating Configuration."""

    app_name: Optional[str] = None
    log_level: Optional[str] = None
    api_port: Optional[int] = None
    notification_url: Optional[str] = None


# Compute Result Models
class ComputeResult(BaseModel):
    """Result of a compute task."""

    execution_id: str
    task_id: str
    tensor_urls: List[str]
    status: Literal["success", "failure"]


class ActiveExecutionsResponse(BaseResponse):
    """Response model for active task executions."""

    data: Dict[str, str]
