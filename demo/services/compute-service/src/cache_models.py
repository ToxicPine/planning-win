from .storage import StorageService
from .result import create_failure, create_success, Result


async def ensure_weights_cached(
    weights_data_key: str, storage_service: StorageService
) -> Result[bool, str]:
    if storage_service.is_downloaded(weights_data_key):
        return create_success(True)
    else:
        result = await storage_service.get_object(weights_data_key)
        if result.status == "failure":
            return create_failure(result.error)
    return create_success(True)
