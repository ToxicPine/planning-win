import asyncio
import logging
import time
from typing import Dict, Optional
from .models import TaskExecutionRequest, ComputeResult, TaskScheduledData
from .result import create_success, create_failure, Result
from .notification import notify_completed_execution
from .storage import StorageService


# Task execution service
class ExecutionService:
    """Service Class to Handle Task Execution Queue and Processing."""

    def __init__(self, logger: logging.Logger, listener_url: str):
        self.logger = logger
        self.listener_url = listener_url
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, asyncio.Task] = {}  # execution_id -> task
        self.task_results: Dict[str, ComputeResult] = {}  # execution_id -> result
        self.storage_service = StorageService()
        self._start_worker()

    def _start_worker(self):
        """Start the Task Processing Worker."""
        asyncio.create_task(self._process_tasks())

    async def _process_tasks(self):
        """Process Tasks From The Queue."""
        while True:
            try:
                task_request = await self.task_queue.get()
                self.logger.info(
                    f"Processing Task Execution {task_request.execution_id} of Type {task_request.task_id}"
                )

                # Create task execution
                task = asyncio.create_task(
                    self._execute_task(task_request),
                    name=task_request.execution_id,
                )

                # Track active task by execution_id
                self.active_tasks[task_request.execution_id] = task

                # Wait for task completion
                try:
                    result = await task
                    self.task_results[task_request.execution_id] = result

                    # Notify listener of completion
                    await notify_completed_execution(
                        execution_id=task_request.execution_id,
                        task_id=task_request.task_id,
                        result=result,
                        listener_url=self.listener_url,
                        logger=self.logger,
                    )
                except Exception as e:
                    self.logger.error(
                        f"Task Execution {task_request.execution_id} Failed: {str(e)}"
                    )
                    self.task_results[task_request.execution_id] = ComputeResult(
                        result=str(e), status="failure"
                    )
                finally:
                    # Clean up
                    del self.active_tasks[task_request.execution_id]
                    self.task_queue.task_done()

            except Exception as e:
                self.logger.error(f"Error Processing Task Queue: {str(e)}")
                await asyncio.sleep(1)

    async def _execute_task(
        self, request: TaskExecutionRequest
    ) -> Result[ComputeResult, str]:
        """
        Execute a single task.

        This is a placeholder implementation. In a real system, this would:
        1. Download any required resources from the parameters
        2. Execute the actual computation
        3. Upload results
        4. Return the compute result
        """
        try:
            # Simulate some work
            result = await self.storage_service.get_object(request.task_storage_key)
            if result.status == "failure":
                return create_failure(result.error)

            # TODO: ML Implementation Here, Must Put Result In Result Directory
            upload_from = "MOCK"
            ###

            key = f"results/{request.execution_id}/task_{request.task_id}.pt"

            tensor_url = await self.storage_service.put_object(
                key=key,
                file_path=upload_from,
            )

            if tensor_url.status == "failure":
                return create_failure(tensor_url.error)

            # For now, just return a success result
            return create_success(
                ComputeResult(
                    execution_id=request.execution_id,
                    task_id=request.task_id,
                    tensor_urls=[tensor_url.data],
                    status="success",
                )
            )
        except Exception as e:
            return create_failure(f"Failed To Execute Task: {str(e)}")

    async def enqueue_task(
        self, request: TaskExecutionRequest
    ) -> Result[TaskScheduledData, str]:
        """Add a Task to the Execution Queue."""
        try:
            # Record scheduling time
            scheduled_at = int(time.time())

            # Add to queue
            await self.task_queue.put(request)

            self.logger.info(
                f"Task Execution {request.execution_id} of Type {request.task_id} Queued"
            )

            return create_success(
                TaskScheduledData(
                    execution_id=request.execution_id,
                    task_id=request.task_id,
                    scheduled_at=scheduled_at,
                )
            )
        except Exception as e:
            return create_failure(f"Failed To Queue Task: {str(e)}")

    async def get_execution_status(self, execution_id: str) -> Optional[ComputeResult]:
        """Get the Current Status of a Task Execution."""
        return self.task_results.get(execution_id)

    async def cancel_execution(self, execution_id: str) -> Result[bool, str]:
        """Cancel a Running Task Execution."""
        if execution_id in self.active_tasks:
            try:
                task = self.active_tasks[execution_id]
                task.cancel()
                return create_success(True)
            except Exception as e:
                return create_failure(f"Failed To Cancel Task Execution: {str(e)}")
        return create_failure("Task Execution Not Found Or Not Running")

    async def list_active_executions(self) -> Dict[str, str]:
        """List All Currently Active Task Executions With Their Task Types."""
        return {
            execution_id: task.get_name()
            for execution_id, task in self.active_tasks.items()
        }
