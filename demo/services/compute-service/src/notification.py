import httpx
import logging
from .models import ComputeStatus, StatusUpdateResponse, ComputeResult
from .result import create_success, create_failure, Result
from .util import with_exponential_backoff


# Notification service
async def notify_status_update(
    status: ComputeStatus, heartbeat_url: str, logger: logging.Logger
) -> Result[bool, str]:
    """Notify Heartbeat Service About Compute Status."""

    async def _notify_operation() -> Result[bool, str]:
        try:
            logger.debug(f"Sending status update to {heartbeat_url}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    heartbeat_url,
                    json=status.model_dump(),
                )
                response.raise_for_status()
                status_response = StatusUpdateResponse.model_validate(response.json())

                if status_response.success:
                    return create_success(True)
                else:
                    return create_failure(status_response.message)
        except Exception as e:
            return create_failure(f"Failed to Send Status Update: {str(e)}")

    return await with_exponential_backoff(
        operation=_notify_operation,
        logger=logger,
        operation_name=f"notify status '{status.status}'",
    )


async def notify_completed_execution(
    execution_id: str,
    task_id: str,
    result: ComputeResult,
    listener_url: str,
    logger: logging.Logger,
) -> Result[bool, str]:
    """Notify Listener Service About Completed Task."""

    report_url = f"{listener_url}/report_completed"

    async def _notify_operation() -> Result[bool, str]:
        try:
            logger.debug(f"Sending Completed Task Notification To {report_url}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    report_url,
                    json={
                        "execution_id": execution_id,
                        "task_id": task_id,
                        "result": result.model_dump(),
                    },
                )
                response.raise_for_status()
                status_response = StatusUpdateResponse.model_validate(response.json())

                if status_response.success:
                    return create_success(True)
                else:
                    return create_failure(status_response.message)
        except Exception as e:
            return create_failure(
                f"Failed to Send Completed Task Notification: {str(e)}"
            )

    return await with_exponential_backoff(
        operation=_notify_operation,
        logger=logger,
        operation_name=f"Notify Completed Task '{task_id}'",
    )
