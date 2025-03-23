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
        # Simulate realistic system metrics with jitter
        cpu_usage = random.gauss(50, 10)  # Mean 50%, std dev 10%
        memory_usage = random.gauss(60, 15)  # Mean 60%, std dev 15%
        gpu_usage = random.gauss(40, 20)  # Mean 40%, std dev 20%
        
        # Ensure values are within reasonable bounds
        cpu_usage = max(0, min(100, cpu_usage))
        memory_usage = max(0, min(100, memory_usage))
        gpu_usage = max(0, min(100, gpu_usage))

        return {
            "health": {
                "status": "healthy",
                "uptime": random.randint(3600, 7200),
                "version": "1.0.0",
                "details": {
                    "cpu_usage": f"{cpu_usage:.1f}%",
                    "memory_usage": f"{memory_usage:.1f}%",
                    "gpu_usage": f"{gpu_usage:.1f}%",
                    "active_tasks": random.randint(1, 5),
                    "queue_size": random.randint(0, 10),
                    "network_latency": f"{random.gauss(50, 10):.1f}ms",
                    "disk_io": f"{random.randint(100, 1000)} MB/s",
                    "gpu_memory": f"{random.randint(4, 16)}GB / 16GB"
                }
            }
        }

    @staticmethod
    def task_execution(task_id: str, parameters: List[str] = None):
        # Simulate realistic processing times with jitter
        processing_time = random.gauss(1.5, 0.5)  # Mean 1.5s, std dev 0.5s
        memory_used = random.gauss(300, 50)  # Mean 300MB, std dev 50MB
        gpu_utilization = random.gauss(50, 15)  # Mean 50%, std dev 15%

        # Ensure values are within reasonable bounds
        processing_time = max(0.5, processing_time)
        memory_used = max(100, min(500, memory_used))
        gpu_utilization = max(20, min(80, gpu_utilization))

        return {
            "execution_id": f"sim-{task_id}-{int(time.time())}",
            "status": "success",
            "start_time": datetime.now().isoformat(),
            "end_time": (datetime.now() + timedelta(seconds=processing_time)).isoformat(),
            "result": {
                "task_id": task_id,
                "parameters": parameters or [],
                "output": f"Simulated output for {task_id}",
                "metrics": {
                    "processing_time": f"{processing_time:.2f}s",
                    "memory_used": f"{memory_used:.1f}MB",
                    "gpu_utilization": f"{gpu_utilization:.1f}%",
                    "network_throughput": f"{random.randint(100, 500)} MB/s",
                    "cache_hit_rate": f"{random.randint(80, 100)}%"
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
        """Simulate loading with a spinner and network jitter."""
        # Base delay with jitter
        base_delay = random.uniform(min_delay, max_delay)
        
        # Add network jitter
        jitter = random.gauss(0, 0.2)  # Mean 0, std dev 0.2
        total_delay = max(0.5, base_delay + jitter)  # Ensure minimum delay of 0.5s
        
        with click.progressbar(length=100, label=message) as bar:
            steps = 20
            for i in range(steps):
                # Add micro-jitter to each step
                step_delay = (total_delay / steps) * (1 + random.uniform(-0.1, 0.1))
                time.sleep(step_delay)
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
                "gpu_support": True,
                "network_compression": True,
                "cache_optimization": True
            },
            "limits": {
                "max_models": 10,
                "max_concurrent_tasks": 5,
                "max_model_size": "50GB",
                "max_network_bandwidth": "1GB/s",
                "max_gpu_memory": "16GB"
            },
            "performance": {
                "average_latency": f"{random.gauss(50, 10):.1f}ms",
                "cache_hit_rate": f"{random.randint(80, 100)}%",
                "network_throughput": f"{random.randint(100, 500)} MB/s"
            }
        }

    def get_model_signed_url(self, model_id: str, operation: str = "download") -> str:
        """Get a signed URL for model operations."""
        self._simulate_loading(f"Generating {operation} URL for model: {model_id}")
        return SimulatedResponse.signed_url(f"{self.models_prefix}{model_id}", operation)["signed_url"]

    def __del__(self):
        self.client.close() 