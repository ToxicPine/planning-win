import json
from pathlib import Path
from .result import create_success, create_failure, Result
from .logger import ConfigModel

# File system operations
def ensure_config_directory() -> Result[Path, str]:
    """Ensure the configuration directory exists."""
    try:
        home_dir = Path("./splitup").resolve()
        home_dir.mkdir(exist_ok=True)
        return create_success(home_dir)
    except Exception as e:
        return create_failure(f"Failed to create config directory: {str(e)}")

def load_config_file(config_path: Path) -> Result[ConfigModel, str]:
    """Load configuration from a JSON file."""
    try:
        if not config_path.exists():
            config = ConfigModel()
            with open(config_path, 'w') as f:
                f.write(config.model_dump_json(indent=2))
            return create_success(config)
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        config = ConfigModel(**config_data)
        return create_success(config)
    except Exception as e:
        return create_failure(f"Failed to Load Config File: {str(e)}")

def save_config_file(config: ConfigModel, config_path: Path) -> Result[None, str]:
    """Save configuration to a JSON file."""
    try:
        with open(config_path, 'w') as f:
            f.write(config.model_dump_json(indent=2))
        return create_success(None)
    except Exception as e:
        return create_failure(f"Failed to Save Config File: {str(e)}")