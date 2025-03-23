# cli/config.py
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings  # Fallback for older versions
from typing import Optional
from pydantic import ConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Node settings
    SPLITUP_NODE_STAKE_AMOUNT: float = 100.0
    SPLITUP_NODE_SPECIALIZATION: Optional[str] = None
    
    # Model deployment settings
    SPLITUP_CLIENT_S3_API_KEY: Optional[str] = None
    SPLITUP_CLIENT_SOLANA_PRIVATE_KEY: Optional[str] = None
    SPLITUP_CLIENT_TARGET_VRAM: int = 12
    SPLITUP_CLIENT_MODEL_FRAMEWORK: str = "tinygrad"
    
    # Compute service settings
    COMPUTE_SERVICE_URL: str = "http://localhost:8000"  # Default to local development
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings()
