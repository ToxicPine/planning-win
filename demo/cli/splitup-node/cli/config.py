# cli/config.py
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings  # Fallback for older versions
from typing import Optional
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Node settings
    SPLITUP_NODE_STAKE_AMOUNT: int = 100  # Fixed stake amount of $100
    SPLITUP_NODE_SPECIALIZATION: Optional[str] = None
    
    # Model deployment settings
    SPLITUP_CLIENT_S3_API_KEY: Optional[str] = None
    SPLITUP_CLIENT_SOLANA_PRIVATE_KEY: Optional[str] = None
    SPLITUP_CLIENT_TARGET_VRAM: int = 12
    SPLITUP_CLIENT_MODEL_FRAMEWORK: str = "tinygrad"
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )

settings = Settings()
