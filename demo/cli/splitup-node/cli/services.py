import httpx
import time
from typing import Optional, List
from .models import NodeRegistration, NodeSpecialization, ModelRegistration, ModelExecution
from .config import settings

class ComputeServiceClient:
    def __init__(self, base_url: str = settings.COMPUTE_SERVICE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)
        self.bucket_name = "zappa-secure-storage-api"
        self.models_prefix = "models/"

    def _make_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def execute_task(self, task_id: str, parameters: Optional[List[str]] = None) -> dict:
        """Execute a task via the compute service."""
        url = self._make_url("/task_execution")
        payload = {
            "execution_id": f"cli-{task_id}-{int(time.time())}",
            "task_id": task_id,
            "parameters": parameters or []
        }
        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def get_health_status(self) -> dict:
        """Get the health status of the compute service."""
        url = self._make_url("/health")
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()

    def load_config(self) -> dict:
        """Load the current configuration from the compute service."""
        url = self._make_url("/load_config")
        response = self.client.post(url)
        response.raise_for_status()
        return response.json()

    def get_model_signed_url(self, model_id: str, operation: str = "download") -> str:
        """Get a signed URL for model operations."""
        url = self._make_url("/signed-url")
        payload = {
            "key": f"{self.models_prefix}{model_id}",
            "operation": operation
        }
        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()["signed_url"]

    def __del__(self):
        self.client.close() 