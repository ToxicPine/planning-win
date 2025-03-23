# cli/models.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class NodeRegistration(BaseModel):
    """Node registration model."""
    stake_amount: float = Field(..., gt=0)

class NodeSpecialization(BaseModel):
    """Node specialization model."""
    model_id: str = Field(..., min_length=1)
    tasks: List[str]

    @field_validator('tasks')
    @classmethod
    def validate_tasks(cls, v):
        if not v or not all(v):
            raise ValueError("Tasks cannot be empty")
        return v

class ModelRegistration(BaseModel):
    """Model registration model."""
    model_path: str = Field(..., min_length=1)
    target_vram: int = Field(..., gt=0)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    framework: str = Field(..., min_length=1)

class ModelExecution(BaseModel):
    """Model execution model."""
    model_id: str = Field(..., min_length=1)
    input_file: str = Field(..., min_length=1)
    output_file: Optional[str] = None
