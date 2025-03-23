import httpx
import time
import random
from typing import Optional, List
from .models import NodeRegistration, NodeSpecialization, ModelRegistration, ModelExecution
from .config import settings
import click
from datetime import datetime, timedelta

class SimulatedResponse:
    """Simulates API responses with realistic data."""
    @staticmethod
    def health_status():
        return {
            "health": {
                "status": "healthy",
                "uptime": random.randint(3600, 7200),
                "version": "1.0.0",
                "details": {
                    "cpu_usage": f"{random.randint(30, 70)}%",
                    "memory_usage": f"{random.randint(40, 80)}%",
                    "gpu_usage": f"{random.randint(20, 60)}%",
                    "active_tasks": random.randint(1, 5),
                    "queue_size": random.randint(0, 10)
                }
            }
        }

    @staticmethod
    def task_execution(task_id: str, parameters: List[str] = None):
        return {
            "execution_id": f"sim-{task_id}-{int(time.time())}",
            "status": "success",
            "start_time": datetime.now().isoformat(),
            "end_time": (datetime.now() + timedelta(seconds=random.randint(1, 5))).isoformat(),
            "result": {
                "task_id": task_id,
                "parameters": parameters or [],
                "output": f"Simulated output for {task_id}",
                "metrics": {
                    "processing_time": random.uniform(0.5, 3.0),
                    "memory_used": random.randint(100, 500),
                    "gpu_utilization": random.randint(20, 80)
                }
            }
        }

    @staticmethod
    def signed_url(key: str, operation: str):
        return {
            "signed_url": f"https://{settings.COMPUTE_SERVICE_URL}/simulated/{operation}/{key}"
        }

class ComputeServiceClient:
    def __init__(self, base_url: str = settings.COMPUTE_SERVICE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)
        self.bucket_name = "zappa-secure-storage-api"
        self.models_prefix = "models/"

    def _make_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _simulate_loading(self, message: str, min_delay: float = 1.0, max_delay: float = 3.0):
        """Simulate loading with a spinner."""
        delay = random.uniform(min_delay, max_delay)
        with click.progressbar(length=100, label=message) as bar:
            steps = 20
            for _ in range(steps):
                time.sleep(delay / steps)
                bar.update(100 // steps)

    def execute_task(self, task_id: str, parameters: Optional[List[str]] = None) -> dict:
        """Execute a task via the compute service."""
        self._simulate_loading(f"Processing task: {task_id}")
        return SimulatedResponse.task_execution(task_id, parameters)

    def get_health_status(self) -> dict:
        """Get the health status of the compute service."""
        self._simulate_loading("Fetching health status")
        return SimulatedResponse.health_status()

    def load_config(self) -> dict:
        """Load the current configuration from the compute service."""
        self._simulate_loading("Loading configuration")
        return {
            "version": "1.0.0",
            "environment": "development",
            "features": {
                "model_optimization": True,
                "auto_scaling": True,
                "gpu_support": True
            },
            "limits": {
                "max_models": 10,
                "max_concurrent_tasks": 5,
                "max_model_size": "50GB"
            }
        }

    def get_model_signed_url(self, model_id: str, operation: str = "download") -> str:
        """Get a signed URL for model operations."""
        self._simulate_loading(f"Generating {operation} URL for model: {model_id}")
        return SimulatedResponse.signed_url(f"{self.models_prefix}{model_id}", operation)["signed_url"]

    def __del__(self):
        self.client.close() 