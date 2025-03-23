#!/usr/bin/env python3
from typing import Dict, List, Tuple, Literal, Any, Union, Optional
from tinygrad.shape.shapetracker import ShapeTracker
from tinygrad.dtype import dtypes, DType
from tinygrad.device import Device
from tinygrad.ops import UOp, Ops
from .types import ActualTensors
from .graph_rewriting import substitute_placeholder_uop, find_all_placeholders
from tinygrad import Tensor
from dataclasses import dataclass
import pickle
import pathlib

# Directory for storing application data
APP_DIR = pathlib.Path.home() / ".tinygrad"

#####
# Logic For Creating Placeholder Info
#####


@dataclass(frozen=True)
class PlaceholderInfo:
    """Information about a placeholder tensor."""

    placeholder: Literal[True]
    name: str
    shape: Tuple[int, ...]
    dtype: DType

    @classmethod
    def from_dict(cls, d: dict) -> "PlaceholderInfo | None":
        """Create a PlaceholderInfo from a dict, with type checking.
        Returns None if the dict is invalid."""
        try:
            if not isinstance(d.get("placeholder"), bool) or not d.get("placeholder"):
                return None
            if not isinstance((name := d.get("name")), str):
                return None
            if not isinstance((shape := d.get("shape")), tuple) or not all(
                isinstance(x, int) for x in shape
            ):
                return None
            if not isinstance((dtype := d.get("dtype")), DType):
                return None
            return cls(True, name=name, shape=shape, dtype=dtype)
        except (KeyError, TypeError):
            return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "placeholder": True,
            "name": self.name,
            "shape": self.shape,
            "dtype": self.dtype.name,
        }

    def to_string(self) -> str:
        """Convert a PlaceholderInfo to a string representation."""
        d = self.to_dict()
        return f"placeholder:{d['name']}:{','.join(str(x) for x in d['shape'])}:{d['dtype']}"

    @classmethod
    def from_string(cls, s: str) -> "PlaceholderInfo | None":
        """Create a PlaceholderInfo from a string representation.
        Returns None if the string is invalid."""
        try:
            placeholder_str, name, shape_str, dtype_str = s.split(":")
            if placeholder_str != "placeholder":
                return None
            shape = tuple(int(x) for x in shape_str.split(",") if x)
            dtype = getattr(dtypes, dtype_str)
            return cls(True, name=name, shape=shape, dtype=dtype)
        except (ValueError, TypeError):
            return None


#####
# Logic For Creating Placeholder Tensors
#####


class TensorTemplateManager:
    """System for creating and managing placeholder tensors."""

    @staticmethod
    def create(
        name: str, shape: Tuple[int, ...], dtype: DType = dtypes.float32
    ) -> Tensor:
        """Create a placeholder tensor with the given shape, dtype, and name."""
        placeholder_id = name

        # Create placeholder info
        placeholder_info = PlaceholderInfo(
            placeholder=True, name=placeholder_id, shape=shape, dtype=dtype
        ).to_string()

        # Create buffer UOp
        buffer_uop = UOp.new_buffer(
            device=str(Device.DEFAULT),
            size=(st := ShapeTracker.from_shape(shape)).size,
            dtype=dtype,
        )

        # TODO: THIS IS A HACK
        # Add explicit placeholder info that won't conflict with normal usage
        buffer_uop = buffer_uop.replace(
            arg=(buffer_uop.arg[0], buffer_uop.arg[1], placeholder_info)
        )

        # Create a proper view UOp
        view_uop = UOp(Ops.VIEW, dtype, (buffer_uop,), ShapeTracker.from_shape(shape))

        return Tensor(view_uop)

    '''
    @staticmethod
    def _get_placeholder_dict(uop: UOp) -> PlaceholderInfo | Literal[False]:
        """Get the placeholder dict if it exists, otherwise False."""
        if not isinstance(uop.arg, dict):
            return False
        info = PlaceholderInfo.from_dict(uop.arg)
        return info if info is not None else False
    
    @staticmethod 
    def is_placeholder(tensor: Tensor) -> bool:
        """Check if a tensor is a placeholder."""
        if not TensorTemplateManager._get_placeholder_dict(tensor.lazydata):
            return False
        else: 
            return True
    
    @staticmethod
    def get_placeholder_name(tensor: Tensor) -> Optional[str]:
        """Get the name of a placeholder tensor."""
        placeholder_data = TensorTemplateManager._get_placeholder_dict(tensor.lazydata)
        if not placeholder_data:
            return None
        else: 
            return placeholder_data.name
    '''

    @staticmethod
    def substitute_placeholder_uop(uop: UOp, input_tensors: ActualTensors) -> UOp:
        """Replace placeholders in a schedule with actual tensors."""
        return substitute_placeholder_uop(uop, input_tensors)

    '''
    def update_schedule(
        self,
        schedule: List[ScheduleItem], 
        input_tensors: Dict[str, Tensor]
    ) -> List[ScheduleItem]:
        """Replace placeholders in a schedule with actual tensors."""

        # Process each schedule item
        updated_schedule: List[ScheduleItem] = []

        for item in schedule:
            updated_ast = self.substitute_placeholder_uop(item.ast, input_tensors)
            updated_item = ScheduleItem(updated_ast, item.bufs, item.metadata)
            updated_schedule.append(updated_item)
        
        return updated_schedule
    '''


#####
# Logic For Serializing/Deserializing Tasks
#####


@dataclass
class GraphProgram:
    """Exported task data."""

    tensor: Tensor
    placeholders: List[PlaceholderInfo]

    @classmethod
    def _sanity_check(cls, data: Any) -> Union["GraphProgram", ValueError]:
        """
        Validate a tensor and its placeholders.

        Args:
            data: Data to validate

        Returns:
            Union[GraphProgram, ValueError]: Either the exported task on success,
            or ValueError if import fails
        """
        # Type checking
        if not isinstance(data, dict):
            return ValueError("Imported data must be a dictionary")

        if "tensor" not in data or "placeholders" not in data:
            return ValueError(
                "Imported data missing required keys: 'tensor' and 'placeholders'"
            )

        if not isinstance(data["tensor"], Tensor):
            return ValueError("Imported tensor must be a Tensor object")

        if not isinstance(data["placeholders"], list):
            return ValueError("Imported placeholders must be a list")

        if not all(isinstance(p, PlaceholderInfo) for p in data["placeholders"]):
            return ValueError("All placeholder values must be PlaceholderInfo objects")

        return GraphProgram(data["tensor"], data["placeholders"])

    def to_bytes(self) -> bytes:
        """Convert the task to bytes for storage."""
        data = {"tensor": self.tensor, "placeholders": self.placeholders}
        return pickle.dumps(data)

    @classmethod
    def from_bytes(cls, data: bytes) -> Union["GraphProgram", ValueError]:
        """
        Import a task from bytes.

        Args:
            data: Pickled bytes containing tensor and placeholder data

        Returns:
            Union[GraphProgram, ValueError]: Either the exported task on success,
            or ValueError if import fails
        """
        try:
            unpickled = pickle.loads(data)
            result = cls._sanity_check(unpickled)
            if isinstance(result, ValueError):
                return result
            return cls(**unpickled)
        except Exception as e:
            return ValueError(f"Failed to unpickle data: {str(e)}")

    def inputs_to_application(self) -> List[PlaceholderInfo]:
        """Get the inputs to the application."""
        return self.placeholders


#####
# Logic For Creating/Managing Tasks Using Placeholders
#####


class TensorContext:
    """Manages creation and tracking of placeholders for tensor serialization."""

    def __init__(self):
        self.placeholders: List[PlaceholderInfo] = []

    def add_graph_input(
        self, name: str, shape: Tuple[int, ...], dtype: DType = dtypes.float32
    ) -> Tensor:
        """Create a new placeholder tensor and track it."""
        tensor = TensorTemplateManager().create(name, shape, dtype)
        self.placeholders.append(
            PlaceholderInfo(placeholder=True, name=name, shape=shape, dtype=dtype)
        )
        return tensor

    """
    def import_safetensors(self, placeholders: List[PlaceholderInfo]) -> None:
        self.placeholders += placeholders
    """

    def compile_to_graph(self, tensor: Tensor) -> Union[GraphProgram, ValueError]:
        """
        Save a tensor and its placeholder information to disk.

        Args:
            tensor: The tensor to save
            output_path: Path to save the pickled tensor and placeholder names

        Returns:
            Union[dict, ValueError]: Either the pickled data dictionary on success,
            or ValueError if unknown placeholders are detected
        """

        # Find all placeholders in the tensor
        found_placeholders = find_all_placeholders(tensor.lazydata)

        # Check for unknown placeholders
        unknown = [
            p
            for p in found_placeholders
            if p not in [ph.name for ph in self.placeholders]
        ]
        if unknown:
            return ValueError(f"Unknown Placeholders Detected: {unknown}")

        # Get intersection of found and tracked placeholders
        known_placeholders = [
            ph
            for ph in self.placeholders
            if ph.name
            in set(found_placeholders).intersection(
                [ph.name for ph in self.placeholders]
            )
        ]
        try:
            return GraphProgram(tensor, known_placeholders)
        except Exception as e:
            return ValueError(f"Failed to pickle data: {str(e)}")

    @staticmethod
    def finalize_lazy_tensor(
        exported_task: GraphProgram, inputs: ActualTensors
    ) -> Union[Tensor, ValueError]:
        """
        Import a tensor task and substitute placeholders with provided tensors.

        Args:
            exported_task: The exported task instance containing tensor and placeholders
            inputs: Dictionary mapping placeholder names to tensors

        Returns:
            Union[Tensor, ValueError]: Either the tensor with substitutions on success,
            or ValueError if import fails
        """
        # Import the data from the instance, not the class
        tensor = exported_task.tensor
        placeholders = exported_task.placeholders

        # Validate substitutions
        if not isinstance(inputs, dict):
            return ValueError("Substitutions must be a dictionary")

        if not all(isinstance(v, Tensor) for v in inputs.values()):
            return ValueError("All substitution values must be Tensor objects")

        # Check that all placeholders have substitutions
        missing = set([ph.name for ph in placeholders]) - set(inputs.keys())
        if missing:
            return ValueError(f"Missing substitutions for placeholders: {missing}")

        # Substitute placeholders in computational graph
        try:
            final = TensorTemplateManager().substitute_placeholder_uop(
                tensor.lazydata, inputs
            )
            tensor.lazydata = final
            return tensor
        except Exception as e:
            return ValueError(f"Failed to substitute placeholders: {str(e)}")


###
# Logic For Inferring Tensor Context From Weights
###


def infer_tensor_context_from_weights(weights: ActualTensors) -> TensorContext:
    """Create a TensorContext with placeholders matching the weights.

    Args:
        weights: Dictionary mapping tensor names to tensors

    Returns:
        Tuple of (weights dict, TensorContext with matching placeholders)
    """
    tensor_context = TensorContext()
    for name, tensor in weights.items():
        tensor_context.add_graph_input(
            name=name, shape=tuple(int(x) for x in tensor.shape), dtype=tensor.dtype
        )
    return tensor_context


###
# Logic For Completing Tasks
###


def execute_graph_on_gpu(
    task: GraphProgram,
    user_inputs: ActualTensors,
    weights: Optional[ActualTensors] = None,
) -> Tensor | ValueError:
    """Complete a task with provided inputs and weights."""
    real_tensors: ActualTensors = {}
    needed_inputs = {
        info.name: {"shape": info.shape, "dtype": info.dtype}
        for info in task.placeholders
    }

    for key, tensor in user_inputs.items():
        if key in needed_inputs:
            real_tensors[key] = tensor
            del needed_inputs[key]

    if weights is not None:
        for key, tensor in weights.items():
            if key in needed_inputs:
                real_tensors[key] = tensor
                del needed_inputs[key]

    if len(needed_inputs) > 0:
        return ValueError(f"Missing tensors: {needed_inputs}")

    # Compute the result
    return TensorContext().finalize_lazy_tensor(task, real_tensors)
