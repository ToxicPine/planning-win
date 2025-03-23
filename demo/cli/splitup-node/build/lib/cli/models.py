# cli/models.py
from pydantic import BaseModel, Field, validator
from typing import List

class NodeRegistration(BaseModel):
    stake_amount: int = Field(..., gt=0, description="Amount to stake (must be positive)")

class NodeSpecialization(BaseModel):
    model_id: str
    tasks: List[int]

    @validator('tasks', pre=True)
    def split_tasks(cls, v):
        # Accept comma-separated values from the CLI and convert to list of ints
        if isinstance(v, str):
            try:
                return [int(task.strip()) for task in v.split(',')]
            except ValueError:
                raise ValueError("Tasks must be a comma-separated list of integers")
        return v
