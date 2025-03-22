from typing import Generic, TypeVar, Literal, Union

# Type definitions for Result pattern
T = TypeVar("T")
E = TypeVar("E")


class SuccessResult(Generic[T]):
    """A successful result containing data."""

    status: Literal["success"] = "success"

    def __init__(self, data: T):
        self.data = data


class FailureResult(Generic[E]):
    """A failure result containing an error."""

    status: Literal["failure"] = "failure"

    def __init__(self, error: E):
        self.error = error


# Discriminated union type for Result
Result = Union[SuccessResult[T], FailureResult[E]]


def create_success(data: T) -> SuccessResult[T]:
    """Create a successful result."""
    return SuccessResult(data=data)


def create_failure(error: E) -> FailureResult[E]:
    """Create a failed result."""
    return FailureResult(error=error)
