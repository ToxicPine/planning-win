import logging
from typing import Literal
from pydantic import BaseModel
from rich.logging import RichHandler

# Configuration models
class ConfigModel(BaseModel):
    """Base configuration model."""
    app_name: str = "state-service"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_port: int = 8000
    notification_url: str = "http://localhost:8001/notify"

# Logger setup
def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """Set up a rich logger with the specified name and level."""
    level = getattr(logging, log_level)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add rich handler
    rich_handler = RichHandler(rich_tracebacks=True)
    rich_handler.setLevel(level)
    logger.addHandler(rich_handler)
    
    return logger