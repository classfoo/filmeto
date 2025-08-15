import asyncio
from typing import Dict, List, Callable, Any, Awaitable
from collections import defaultdict


class AsyncQueue:
    """
    An asyncio.Queue-based producer-consumer queue that processes tasks sequentially.
    
    Supports:
    - Adding tasks with a type and any payload
    - Connecting multiple async handlers for each task type
    - Sequential processing (concurrency of 1)
    - Type-based routing to appropriate handlers
    - Automatically starts processing when the event loop runs
    """
    
    def __init__(self):
        self._queue = asyncio.Queue()
        self._handlers: Dict[str, List[Callable[[Any], Awaitable[Any]]]] = defaultdict(list)
        self._running = True
        self._task = None
        
        # We'll start processing when the run method is called via asyncio.run or similar
        # This happens automatically when the event loop starts
    
    def add(self, task_type: str, task_data: Any) -> None:
        """
        Add a task to the queue for processing.
        
        Args:
            task_type: The type of task to route to appropriate handlers
            task_data: Data to be passed to the handler (can be any type)
        """
        self._queue.put_nowait({'type': task_type, 'data': task_data})
        
        # If this is the first task and no processing task is running, start processing
        if self._task is None or self._task.done():
            # We need to schedule the processing loop in the event loop
            try:
                # Try to get the running event loop
                loop = asyncio.get_running_loop()
                # Schedule the processing loop
                if self._task is None or self._task.done():
                    self._task = loop.create_task(self._run())
            except RuntimeError:
                # No event loop running yet, will start when event loop starts
                pass
    
    def connect(self, task_type: str, handler: Callable[[Any], Awaitable[Any]]) -> None:
        """
        Connect an async handler function to a specific task type.
        
        Args:
            task_type: The type of task this handler will process
            handler: An async function that takes task data (any type) and returns awaitable
        """
        self._handlers[task_type].append(handler)
    
    async def _process_task(self, task: Dict[str, Any]) -> None:
        """
        Process a single task by routing it to all connected handlers for its type.
        
        Args:
            task: Dictionary containing 'type' and 'data' keys
        """
        task_type = task['type']
        task_data = task['data']
        
        # Execute all handlers connected to this task type
        for handler in self._handlers[task_type]:
            await handler(task_data)
    
    async def _run(self) -> None:
        """
        Main processing loop that processes tasks sequentially from the queue.
        """
        while self._running:
            try:
                # Get the next task from the queue
                task = await self._queue.get()
                
                # Process the task
                await self._process_task(task)
                
                # Mark the task as done
                self._queue.task_done()
            except asyncio.CancelledError:
                # Handle cancellation properly
                break
            except Exception as e:
                # Log the error but continue processing other tasks
                print(f"Error processing task: {e}")
                try:
                    self._queue.task_done()
                except ValueError:
                    # Queue might be empty or already handled
                    pass
    
    def stop(self) -> None:
        """
        Stop the processing loop gracefully.
        """
        self._running = False
        if self._task:
            self._task.cancel()
    
    async def join(self) -> None:
        """
        Wait until all items in the queue are processed.
        """
        await self._queue.join()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        self.stop()