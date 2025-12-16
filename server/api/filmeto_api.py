"""
Filmeto API

Unified API interface for AI model services.
Supports both web-based access and local in-app calls with streaming.
"""

from __future__ import annotations
from typing import AsyncIterator, Union, Optional

from server.api.types import FilmetoTask, TaskProgress, TaskResult, ValidationError


class FilmetoApi:
    """
    Unified API interface for Filmeto AI services.
    
    This class provides a clean interface for both web and local clients
    to execute tasks and receive streaming progress updates.
    """
    
    def __init__(self, plugins_dir: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize Filmeto API.

        Args:
            plugins_dir: Directory containing server plugins
            cache_dir: Directory for resource caching
        """
        # Import here to avoid circular import
        from server.service.filmeto_service import FilmetoService
        self.service = FilmetoService(plugins_dir, cache_dir)
    
    async def execute_task_stream(
        self, 
        task: FilmetoTask
    ) -> AsyncIterator[Union[TaskProgress, TaskResult]]:
        """
        Execute a task and stream progress updates.
        
        This is the main entry point for task execution. It validates the task,
        processes resources, routes to the appropriate plugin, and streams
        progress updates and the final result.
        
        Args:
            task: Task to execute
            
        Yields:
            TaskProgress: Progress updates during execution
            TaskResult: Final result (last item yielded)
            
        Raises:
            ValidationError: If task validation fails
            PluginNotFoundError: If specified plugin not found
            PluginExecutionError: If plugin execution fails
            TimeoutError: If task exceeds timeout
            
        Example:
            ```python
            api = FilmetoApi()
            task = FilmetoTask(
                tool_name=ToolType.TEXT2IMAGE,
                plugin_name="text2image_comfyui",
                parameters={"prompt": "a beautiful sunset"}
            )
            
            async for update in api.execute_task_stream(task):
                if isinstance(update, TaskProgress):
                    print(f"Progress: {update.percent}% - {update.message}")
                elif isinstance(update, TaskResult):
                    print(f"Result: {update.status}, files: {update.output_files}")
            ```
        """
        async for update in self.service.execute_task_stream(task):
            yield update
    
    def validate_task(self, task: FilmetoTask) -> tuple[bool, Optional[str]]:
        """
        Validate task structure and parameters.
        
        Args:
            task: Task to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Example:
            ```python
            api = FilmetoApi()
            task = FilmetoTask(...)
            is_valid, error = api.validate_task(task)
            if not is_valid:
                print(f"Validation error: {error}")
            ```
        """
        return task.validate()
    
    async def get_task_status(self, task_id: str) -> dict:
        """
        Get current status of a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status dictionary
            
        Example:
            ```python
            api = FilmetoApi()
            status = await api.get_task_status("task-123")
            print(f"Task status: {status}")
            ```
        """
        return await self.service.get_task_status(task_id)
    
    def list_tools(self) -> list[dict]:
        """
        List all available tools.
        
        Returns:
            List of tool information dictionaries
            
        Example:
            ```python
            api = FilmetoApi()
            tools = api.list_tools()
            for tool in tools:
                print(f"{tool['name']}: {tool['display_name']}")
            ```
        """
        return self.service.list_tools()
    
    def list_plugins(self) -> list[dict]:
        """
        List all available plugins.
        
        Returns:
            List of plugin information dictionaries
            
        Example:
            ```python
            api = FilmetoApi()
            plugins = api.list_plugins()
            for plugin in plugins:
                print(f"{plugin['name']} v{plugin['version']} - {plugin['tool_type']}")
            ```
        """
        return self.service.list_plugins()
    
    def get_plugins_by_tool(self, tool_name: str) -> list[dict]:
        """
        Get all plugins supporting a specific tool type.
        
        Args:
            tool_name: Tool type (e.g., "text2image")
            
        Returns:
            List of plugin information dictionaries
            
        Example:
            ```python
            api = FilmetoApi()
            plugins = api.get_plugins_by_tool("text2image")
            print(f"Found {len(plugins)} plugins for text2image")
            ```
        """
        plugin_infos = self.service.plugin_manager.get_plugins_by_tool(tool_name)
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "tool_type": p.tool_type,
                "engine": p.engine,
                "author": p.author
            }
            for p in plugin_infos
        ]
    
    async def cleanup(self):
        """
        Cleanup resources and stop all plugins.
        
        Should be called when shutting down the API.
        
        Example:
            ```python
            api = FilmetoApi()
            # ... use api ...
            await api.cleanup()
            ```
        """
        await self.service.cleanup()
