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
    """Service class to handle task execution queue and processing."""

    def __init__(self, logger: logging.Logger, listener_url: str):
        self.logger = logger
        self.listener_url = listener_url
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, asyncio.Task] = {}  # execution_id -> task
        self.task_results: Dict[str, ComputeResult] = {}  # execution_id -> result
        self._start_worker()

    def _start_worker(self):
        """Start the task processing worker."""
        asyncio.create_task(self._process_tasks())

    async def _process_tasks(self):
        """Process tasks from the queue."""
        while True:
            try:
                task_request = await self.task_queue.get()
                self.logger.info(
                    f"Processing task execution {task_request.execution_id} of type {task_request.task_id}"
                )

                # Create task execution
                task = asyncio.create_task(
                    self._execute_task(task_request),
                    name=f"execution_{task_request.execution_id}",
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
                await asyncio.sleep(1)  # Prevent Tight Loop On Errors

    async def _execute_task(self, request: TaskExecutionRequest) -> ComputeResult:
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
            ###
            # IMPLEMENT WORK HERE
            ###

            # For now, just return a success result
            return ComputeResult(
                result="Execution Completed Successfully", status="success"
            )
        except Exception as e:
            return ComputeResult(result=str(e), status="failure")

    async def enqueue_task(
        self, request: TaskExecutionRequest
    ) -> Result[TaskScheduledData, str]:
        """Add a task to the execution queue."""
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
        """Get the current status of a task execution."""
        return self.task_results.get(execution_id)

    async def cancel_execution(self, execution_id: str) -> Result[bool, str]:
        """Cancel a running task execution."""
        if execution_id in self.active_tasks:
            try:
                task = self.active_tasks[execution_id]
                task.cancel()
                return create_success(True)
            except Exception as e:
                return create_failure(f"Failed To Cancel Task Execution: {str(e)}")
        return create_failure("Task Execution Not Found Or Not Running")

    async def list_active_executions(self) -> Dict[str, str]:
        """List all currently active task executions with their task types."""
        return {
            execution_id: task.get_name()
            for execution_id, task in self.active_tasks.items()
        }
