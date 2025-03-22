import logging
from rich.logging import RichHandler


# Logger setup
def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """Set Up A Rich Logger With The Specified Name And Level."""
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
