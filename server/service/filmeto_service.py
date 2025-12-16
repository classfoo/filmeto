"""
Filmeto Service

Core service layer that manages task execution through plugins.
"""

import asyncio
from typing import AsyncIterator, Union
from datetime import datetime

from server.api.types import (
    FilmetoTask, TaskProgress, TaskResult, ProgressType,
    ValidationError, PluginNotFoundError, PluginExecutionError, TimeoutError as TaskTimeoutError
)
from server.api.resource_processor import ResourceProcessor
from server.plugins.plugin_manager import PluginManager


class FilmetoService:
    """
    Service layer managing plugin lifecycle and task execution.
    """
    
    def __init__(self, plugins_dir: str = None, cache_dir: str = None):
        """
        Initialize Filmeto service.
        
        Args:
            plugins_dir: Directory containing plugins
            cache_dir: Directory for resource caching
        """
        self.plugin_manager = PluginManager(plugins_dir)
        self.resource_processor = ResourceProcessor(cache_dir)
        self.heartbeat_interval = 5  # seconds
        
        # Discover plugins on initialization
        self.plugin_manager.discover_plugins()
    
    async def execute_task_stream(
        self, 
        task: FilmetoTask
    ) -> AsyncIterator[Union[TaskProgress, TaskResult]]:
        """
        Execute task through appropriate plugin with streaming.
        
        Args:
            task: Task to execute
            
        Yields:
            TaskProgress: Progress updates during execution
            TaskResult: Final result (last item)
            
        Raises:
            ValidationError: If task validation fails
            PluginNotFoundError: If plugin not found
            PluginExecutionError: If plugin execution fails
            TaskTimeoutError: If task exceeds timeout
        """
        start_time = datetime.now()
        
        # Validate task
        is_valid, error_msg = task.validate()
        if not is_valid:
            raise ValidationError(error_msg, {"task_id": task.task_id})
        
        try:
            # Process resources
            yield TaskProgress(
                task_id=task.task_id,
                type=ProgressType.STARTED,
                percent=0,
                message="Processing resources..."
            )
            
            processed_resources = []
            for i, resource in enumerate(task.resources):
                try:
                    local_path = await self.resource_processor.process_resource(resource)
                    processed_resources.append(local_path)
                    
                    # Update progress
                    percent = (i + 1) / len(task.resources) * 10  # First 10% for resources
                    yield TaskProgress(
                        task_id=task.task_id,
                        type=ProgressType.PROGRESS,
                        percent=percent,
                        message=f"Processed resource {i+1}/{len(task.resources)}"
                    )
                except Exception as e:
                    raise ValidationError(
                        f"Failed to process resource {i}: {str(e)}",
                        {"task_id": task.task_id, "resource_index": i}
                    )
            
            # Update task with processed resource paths
            task.metadata['processed_resources'] = processed_resources
            
            # Get or start plugin
            yield TaskProgress(
                task_id=task.task_id,
                type=ProgressType.PROGRESS,
                percent=10,
                message=f"Starting plugin: {task.plugin_name}"
            )
            
            plugin = await self.plugin_manager.get_plugin(task.plugin_name)
            
            # Send task to plugin
            yield TaskProgress(
                task_id=task.task_id,
                type=ProgressType.PROGRESS,
                percent=15,
                message="Executing task..."
            )
            
            await plugin.send_task(task)
            
            # Create heartbeat task
            heartbeat_task = asyncio.create_task(
                self._send_heartbeats(task.task_id, plugin)
            )
            
            try:
                # Stream progress and results from plugin
                async for message in plugin.receive_messages():
                    method = message.get("method")
                    result = message.get("result")
                    
                    if method == "progress":
                        # Progress update from plugin
                        params = message.get("params", {})
                        
                        # Scale progress: 15-95% for plugin execution
                        plugin_percent = params.get("percent", 0)
                        scaled_percent = 15 + (plugin_percent * 0.8)
                        
                        yield TaskProgress(
                            task_id=task.task_id,
                            type=ProgressType(params.get("type", "progress")),
                            percent=scaled_percent,
                            message=params.get("message", ""),
                            data=params.get("data", {})
                        )
                    
                    elif method == "heartbeat":
                        # Heartbeat from plugin
                        yield TaskProgress(
                            task_id=task.task_id,
                            type=ProgressType.HEARTBEAT,
                            percent=0,
                            message="heartbeat"
                        )
                    
                    elif result:
                        # Final result from plugin
                        execution_time = (datetime.now() - start_time).total_seconds()
                        
                        task_result = TaskResult(
                            task_id=task.task_id,
                            status=result.get("status", "error"),
                            output_files=result.get("output_files", []),
                            output_resources=result.get("output_resources", []),
                            error_message=result.get("error_message", ""),
                            execution_time=execution_time,
                            metadata=result.get("metadata", {})
                        )
                        
                        yield task_result
                        break
                
            finally:
                # Cancel heartbeat task
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
        
        except asyncio.TimeoutError:
            raise TaskTimeoutError(task.task_id, task.timeout)
        
        except Exception as e:
            # Return error result
            execution_time = (datetime.now() - start_time).total_seconds()
            
            error_result = TaskResult(
                task_id=task.task_id,
                status="error",
                error_message=str(e),
                execution_time=execution_time
            )
            
            yield error_result
    
    async def _send_heartbeats(self, task_id: str, plugin):
        """
        Send periodic heartbeats while task is executing.
        
        Args:
            task_id: Task identifier
            plugin: Plugin process
        """
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                # Heartbeats are sent by the plugin itself
                # This is just to keep the connection alive on the service side
        except asyncio.CancelledError:
            pass
    
    async def get_task_status(self, task_id: str) -> dict:
        """
        Get current status of a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status dictionary
        """
        # TODO: Implement task status tracking
        return {
            "task_id": task_id,
            "status": "unknown"
        }
    
    def list_plugins(self) -> list:
        """
        List all available plugins.
        
        Returns:
            List of plugin info dictionaries
        """
        plugins = self.plugin_manager.list_plugins()
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "tool_type": p.tool_type,
                "engine": p.engine,
                "author": p.author
            }
            for p in plugins
        ]
    
    def list_tools(self) -> list:
        """
        List all available tools.
        
        Returns:
            List of tool info dictionaries
        """
        from server.api.types import ToolType
        
        return [
            {
                "name": tool.value,
                "display_name": tool.value.replace('2', ' to ').title()
            }
            for tool in ToolType
        ]
    
    async def cleanup(self):
        """
        Cleanup resources and stop all plugins.
        """
        await self.plugin_manager.stop_all_plugins()
        self.resource_processor.cleanup_cache()

