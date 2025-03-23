import logging
import asyncio
from typing import Callable, Awaitable, TypeVar, cast
from .result import Result, SuccessResult, FailureResult, create_failure

T = TypeVar("T")
E = TypeVar("E")


# Exponential backoff helper
async def with_exponential_backoff(
    operation: Callable[[], Awaitable[Result[T, E]]],
    logger: logging.Logger,
    operation_name: str,
    max_attempts: int = 5,
    initial_backoff: int = 3,
) -> Result[T, E]:
    """
    Executes the given operation with exponential backoff retry logic.

    Args:
        operation: Async function that returns a Result
        logger: Logger instance
        operation_name: Name of the operation for logging
        max_attempts: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds

    Returns:
        The Result from the operation, either success or the last failure
    """
    attempt = 0
    backoff_time = initial_backoff

    while attempt < max_attempts:
        result = await operation()

        if result.status == "success":
            if attempt > 0:
                logger.info(
                    f"Successfully completed {operation_name} after {attempt + 1} attempts"
                )
            return cast(SuccessResult[T], result)

        attempt += 1
        if attempt >= max_attempts:
            logger.error(
                f"Failed to {operation_name} after {max_attempts} attempts: {result.error}"
            )
            return cast(FailureResult[E], result)

        logger.warning(
            f"{operation_name} attempt {attempt} failed: {result.error}. Retrying in {backoff_time}s..."
        )
        await asyncio.sleep(backoff_time)
        backoff_time *= 2

    # This should never be reached due to the return inside the loop
    return cast(FailureResult[E], create_failure("Max Retry Attempts Exceeded"))
