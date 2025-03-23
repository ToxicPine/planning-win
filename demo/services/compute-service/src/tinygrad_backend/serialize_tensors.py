from tinygrad import Tensor, dtypes
from numpy import ndarray

###
# Tools For Serializing/Deserializing Tensors
###


class TensorSerializer:
    """Class for serializing and deserializing realized tensors to/from bytes."""

    @staticmethod
    def tensor_to_bytes(tensor: Tensor) -> bytes:
        """Convert a realized tensor to bytes.

        Args:
            tensor: The tensor to serialize

        Returns:
            Bytes containing the serialized tensor
        """
        # Ensure tensor is realized
        tensor.realize()

        # Get raw buffer data
        np_data: ndarray = tensor.numpy()
        raw_data = np_data.tobytes()

        # Build metadata and buffer
        shape_str = ",".join(str(x) for x in tensor.shape)
        dtype_str = tensor.dtype.name

        # Combine into bytes
        metadata = f"{shape_str}\n{dtype_str}\n".encode()
        return metadata + raw_data

    @staticmethod
    def tensor_from_bytes(data: bytes) -> Tensor:
        """Create a tensor from bytes.

        Args:
            data: Bytes containing the serialized tensor

        Returns:
            The deserialized tensor
        """
        # Split metadata and raw data
        lines = data.split(b"\n", 2)

        # Parse metadata
        shape = tuple(int(x) for x in lines[0].decode().split(","))
        dtype = getattr(dtypes, lines[1].decode())
        raw_data = lines[2]

        # Create tensor from bytes
        return Tensor(raw_data, dtype=dtype).reshape(shape)
