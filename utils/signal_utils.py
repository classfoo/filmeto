"""
Signal utility classes for blocking, async, and asyncio-based signal implementations
"""
import asyncio
import threading
from typing import Any, Callable, List, Optional, Dict, Awaitable
from concurrent.futures import ThreadPoolExecutor
from qasync import asyncSlot


class BaseSignal:
    """Base signal class with common functionality"""
    
    def __init__(self):
        self._slots: List[Callable] = []
        self._slot_lock = threading.Lock()
    
    def connect(self, slot: Callable):
        """Connect a slot to this signal"""
        with self._slot_lock:
            if slot not in self._slots:
                self._slots.append(slot)
    
    def disconnect(self, slot: Callable):
        """Disconnect a slot from this signal"""
        with self._slot_lock:
            if slot in self._slots:
                self._slots.remove(slot)
    
    def disconnect_all(self):
        """Disconnect all slots"""
        with self._slot_lock:
            self._slots.clear()


class BlockingSignal(BaseSignal):
    """
    Blocking signal implementation that executes all connected slots synchronously
    """
    
    def emit(self, *args, **kwargs):
        """
        Emit the signal and execute all connected slots synchronously
        Blocks until all slots have completed execution
        """
        with self._slot_lock:
            slots_copy = self._slots.copy()
        
        for slot in slots_copy:
            slot(*args, **kwargs)


class AsyncSignal(BaseSignal):
    """
    Async signal implementation that executes all connected slots asynchronously
    """
    
    def __init__(self):
        super().__init__()
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    async def emit(self, *args, **kwargs):
        """
        Emit the signal and execute all connected slots asynchronously
        Returns when all slots have completed execution
        """
        with self._slot_lock:
            slots_copy = self._slots.copy()
        
        # Run all slots concurrently in the thread pool
        tasks = []
        for slot in slots_copy:
            if asyncio.iscoroutinefunction(slot):
                # If the slot is a coroutine function, await it directly
                task = asyncio.create_task(slot(*args, **kwargs))
            else:
                # If the slot is a regular function, run it in the executor
                task = asyncio.get_event_loop().run_in_executor(
                    self._executor, 
                    lambda: slot(*args, **kwargs)
                )
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def emit_nowait(self, *args, **kwargs):
        """
        Emit the signal without waiting for slots to complete
        """
        # Run the emit in the background
        asyncio.create_task(self.emit(*args, **kwargs))
    
    def close(self):
        """Clean up resources"""
        self._executor.shutdown(wait=True)


class AsyncioSignal(BaseSignal):
    """
    Asyncio-based signal implementation that integrates with the asyncio event loop
    """
    
    def __init__(self):
        super().__init__()
        self._event_loop = None
        self._tasks = set()
    
    async def emit(self, *args, **kwargs):
        """
        Emit the signal and execute all connected slots in the asyncio event loop
        """
        with self._slot_lock:
            slots_copy = self._slots.copy()
        
        # Create tasks for all slots
        tasks = []
        for slot in slots_copy:
            if asyncio.iscoroutinefunction(slot):
                # If the slot is a coroutine function, create a task directly
                task = asyncio.create_task(slot(*args, **kwargs))
            else:
                # If the slot is a regular function, create a task that runs it
                async def wrapper():
                    return slot(*args, **kwargs)
                task = asyncio.create_task(wrapper())
            
            tasks.append(task)
            self._tasks.add(task)
            # Remove completed tasks from the set
            task.add_done_callback(lambda t: self._tasks.discard(t))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
    
    def emit_nowait(self, *args, **kwargs):
        """
        Emit the signal without waiting for slots to complete
        """
        task = asyncio.create_task(self.emit(*args, **kwargs))
        self._tasks.add(task)
        # Remove completed tasks from the set
        task.add_done_callback(lambda t: self._tasks.discard(t))
    
    async def wait_all(self):
        """
        Wait for all currently running tasks to complete
        """
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
    
    def close(self):
        """
        Cancel all running tasks and clean up
        """
        for task in self._tasks:
            if not task.done():
                task.cancel()


# Convenience functions for commonly used signals
def create_blocking_signal() -> BlockingSignal:
    """Create and return a blocking signal"""
    return BlockingSignal()


def create_async_signal() -> AsyncSignal:
    """Create and return an async signal"""
    return AsyncSignal()


def create_asyncio_signal() -> AsyncioSignal:
    """Create and return an asyncio signal"""
    return AsyncioSignal()


# Example usage and test functions
async def example_usage():
    """Example of how to use the signal utilities"""
    
    # Example blocking signal
    blocking_sig = BlockingSignal()
    
    def sync_handler(msg):
        print(f"Blocking signal received: {msg}")
    
    blocking_sig.connect(sync_handler)
    blocking_sig.emit("Hello from blocking signal")
    
    # Example async signal
    async_sig = AsyncSignal()
    
    async def async_handler(msg):
        await asyncio.sleep(0.1)  # Simulate async work
        print(f"Async signal received: {msg}")
    
    def sync_handler_async(msg):
        print(f"Sync handler in async signal: {msg}")
    
    async_sig.connect(async_handler)
    async_sig.connect(sync_handler_async)
    await async_sig.emit("Hello from async signal")
    
    # Example asyncio signal
    asyncio_sig = AsyncioSignal()
    
    async def asyncio_handler(msg):
        await asyncio.sleep(0.1)  # Simulate async work
        print(f"Asyncio signal received: {msg}")
    
    asyncio_sig.connect(asyncio_handler)
    await asyncio_sig.emit("Hello from asyncio signal")
    
    # Cleanup
    async_sig.close()
    asyncio_sig.close()


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())