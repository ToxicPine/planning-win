import json
import os
from pathlib import Path
from .result import create_success, create_failure, Result
from .logger import ConfigModel


# File system operations
def ensure_config_directory() -> Result[Path, str]:
    """Ensure the configuration directory exists."""
    try:
        # Use $HOME/.splitup/state-service for better organization
        home_dir = Path(os.path.expanduser("~")) / ".splitup" / "state-service"
        home_dir.mkdir(exist_ok=True, parents=True)
        return create_success(home_dir)
    except Exception as e:
        return create_failure(f"Failed to create config directory: {str(e)}")


def get_config_path(filename: str = "config.json") -> Result[Path, str]:
    """Get the path to a configuration file."""
    dir_result = ensure_config_directory()
    if dir_result.status == "failure":
        return create_failure(dir_result.error)

    return create_success(dir_result.data / filename)


def load_config_file(config_path: Path) -> Result[ConfigModel, str]:
    """Load configuration from a JSON file."""
    try:
        if not config_path.exists():
            config = ConfigModel()
            with open(config_path, "w") as f:
                f.write(config.model_dump_json(indent=2))
            return create_success(config)

        with open(config_path, "r") as f:
            config_data = json.load(f)

        config = ConfigModel(**config_data)
        return create_success(config)
    except Exception as e:
        return create_failure(f"Failed to Load Config File: {str(e)}")


def save_config_file(config: ConfigModel, config_path: Path) -> Result[None, str]:
    """Save configuration to a JSON file."""
    try:
        with open(config_path, "w") as f:
            f.write(config.model_dump_json(indent=2))
        return create_success(None)
    except Exception as e:
        return create_failure(f"Failed to Save Config File: {str(e)}")
