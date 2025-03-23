# cli/models.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class NodeRegistration(BaseModel):
    stake_amount: int = Field(..., description="Amount to stake for node registration")

class NodeSpecialization(BaseModel):
    model_id: str = Field(..., description="Model identifier")
    tasks: List[str] = Field(..., description="List of task IDs")

    @field_validator('tasks', mode='before')
    @classmethod
    def split_tasks(cls, v):
        # Accept comma-separated values from the CLI and convert to list
        if isinstance(v, str):
            try:
                return [task.strip() for task in v.split(',')]
            except ValueError:
                raise ValueError("Tasks must be a comma-separated list")
        return v

class ModelRegistration(BaseModel):
    model_path: str = Field(..., description="Path to the model file")
    target_vram: int = Field(..., description="Target VRAM constraint in GB")
    name: str = Field(..., description="Model name")
    description: str = Field(..., description="Model description")
    framework: str = Field(..., description="Model framework (e.g. tinygrad)")

class ModelExecution(BaseModel):
    model_id: str = Field(..., description="Model identifier")
    input_file: str = Field(..., description="Path to input file")
    output_file: Optional[str] = Field(None, description="Path to output file")
