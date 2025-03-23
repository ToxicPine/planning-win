from .result import create_success, create_failure, Result
from pydantic import BaseModel, model_validator
from urllib.parse import urlparse
from typing import TypeVar, Type, Optional, Callable, Any, Dict
import os

T = TypeVar("T", bound=BaseModel)


def load_env_config(
    model_class: Type[T], error_handler: Optional[Callable[[Exception], str]] = None
) -> Result[T, str]:
    """
    Generic function to load and validate configuration from environment variables.

    Args:
        model_class: A Pydantic model class that defines the configuration schema
        error_handler: Optional custom error handler function

    Returns:
        Result containing either the validated model instance or an error message
    """
    try:
        # Get model fields and annotations
        model_fields = getattr(model_class, "__annotations__", {})

        # Collect environment variables
        env_values: Dict[str, Any] = {}
        for field_name in model_fields:
            if field_name in os.environ:
                env_values[field_name] = os.environ[field_name]

        # Create and validate the model with values from environment
        config = model_class(**env_values)

        return create_success(config)
    except Exception as e:
        if error_handler:
            error_message = error_handler(e)
        else:
            error_message = f"Failed to Load Environment Configuration for {model_class.__name__}: {str(e)}"
        return create_failure(error_message)


P = TypeVar("P", bound=BaseModel)


def create_optional_model(model_class: Type[BaseModel]) -> Type[BaseModel]:
    """Create a new model class with all fie = ""
    lds as optional."""
    new_annotations = {}
    for field_name, field_type in getattr(model_class, "__annotations__", {}).items():
        new_annotations[field_name] = Optional[field_type]

    new_name = f"Optional{model_class.__name__}"
    new_class = type(
        new_name,
        (BaseModel,),
        {
            "__annotations__": new_annotations,
            "__doc__": f"Optional version of {model_class.__name__} with all fields nullable",
        },
    )

    return new_class


# Environment Configuration
class EnvSettings(BaseModel):
    """Environment Settings With Validation."""

    SPLITUP_STORAGE_S3_BUCKET: str
    SPLITUP_STORAGE_API_ENDPOINT: str
    SPLITUP_STORAGE_API_KEY: str
    SPLITUP_STORAGE_REGION: str = "eu-west-2"
    SPLITUP_COMPUTE_SERVICE_NAME: str = "compute-service"
    SPLITUP_COMPUTE_SERVICE_LOG_LEVEL: str = "INFO"
    SPLITUP_COMPUTE_SERVICE_API_PORT: int = 6068
    SPLITUP_COMPUTE_SERVICE_HEARTBEAT_URL: str
    SPLITUP_COMPUTE_SERVICE_LISTENER_URL: str
    SPLITUP_COMPUTE_SERVICE_CONFIG_URL: str

    model_config = {"validate_assignment": True}

    @model_validator(mode="after")
    def validate_urls(self):
        """Validate That URLs Are Valid."""
        urls = [
            self.SPLITUP_COMPUTE_SERVICE_HEARTBEAT_URL,
            self.SPLITUP_COMPUTE_SERVICE_LISTENER_URL,
            self.SPLITUP_COMPUTE_SERVICE_CONFIG_URL,
        ]

        for url in urls:
            try:
                result = urlparse(url)
                if not all([result.scheme, result.netloc]):
                    raise ValueError(f"URL {url} Must Have A Scheme And Host")
            except Exception as e:
                raise ValueError(f"Invalid URL {url}: {str(e)}")

        return self
