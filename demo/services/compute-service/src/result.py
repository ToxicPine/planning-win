from typing import Generic, TypeVar, Literal, Union

# Type definitions for Result pattern
T = TypeVar("T")
E = TypeVar("E")


class SuccessResult(Generic[T]):
    """A Successful Result Containing Data."""

    status: Literal["success"] = "success"

    def __init__(self, data: T):
        self.data = data


class FailureResult(Generic[E]):
    """A Failure Result Containing An Error."""

    status: Literal["failure"] = "failure"

    def __init__(self, error: E):
        self.error = error


# Discriminated union type for Result
Result = Union[SuccessResult[T], FailureResult[E]]


def create_success(data: T) -> SuccessResult[T]:
    """Create A Successful Result."""
    return SuccessResult(data=data)


def create_failure(error: E) -> FailureResult[E]:
    """Create A Failed Result."""
    return FailureResult(error=error)
