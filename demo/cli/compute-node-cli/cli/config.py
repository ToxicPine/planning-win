# cli/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    s3_api_key: str
    solana_private_key: str
    log_level: str = "INFO"
    model_cache_dir: str

    class Config:
        env_prefix = "SPLITUP_CLIENT_"

settings = Settings()
