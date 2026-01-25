"""
React Service Module

Implements the ReactService class to manage React instances with reuse capability.
The service allows getting or creating React instances by react_type and project_name,
enabling instance reuse across different parts of the application.
"""
import asyncio
from typing import Dict, Optional, Callable, Any
from threading import Lock
from pathlib import Path

from .react import React


class ReactService:
    """
    Singleton service to manage React instances with reuse capability.

    This service handles:
    - Creating React instances by react_type and project_name
    - Returning existing instances if they already exist (reuse)
    - Managing the lifecycle of React instances
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ReactService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._instances: Dict[str, React] = {}
        self._initialized = True

    def _generate_instance_key(self, project_name: str, react_type: str) -> str:
        """
        Generate a unique key for identifying a React instance.
        
        Args:
            project_name: Name of the project
            react_type: Type of the React process
            
        Returns:
            Unique key combining project_name and react_type
        """
        return f"{project_name}:{react_type}"

    def get_or_create_react(
        self,
        project_name: str,
        react_type: str,
        build_prompt_function = None,
        react_tool_call_function: Callable[[str, Dict[str, Any]], Any] = None,
        *,
        workspace=None,
        llm_service=None,
        max_steps: int = 20,
    ) -> React:
        """
        Get an existing React instance or create a new one if it doesn't exist.

        Args:
            project_name: Name of the project
            react_type: Type of ReAct process
            build_prompt_function: Optional function to build the prompt dynamically
            react_tool_call_function: Async function to call tools (tool_name, tool_args) -> result
            workspace: Workspace instance to use for the React process
            llm_service: LlmService instance to use for LLM calls
            max_steps: Maximum number of ReAct steps to perform

        Returns:
            React instance for the given project and type
        """
        instance_key = self._generate_instance_key(project_name, react_type)

        # Check if an instance already exists for this project and type
        if instance_key in self._instances:
            return self._instances[instance_key]

        # Create a new React instance
        react_instance = React(
            project_name=project_name,
            react_type=react_type,
            build_prompt_function=build_prompt_function,
            react_tool_call_function=react_tool_call_function,
            workspace=workspace,
            llm_service=llm_service,
            max_steps=max_steps,
        )

        # Store the instance for reuse
        self._instances[instance_key] = react_instance

        return react_instance

    def get_react(self, project_name: str, react_type: str) -> Optional[React]:
        """
        Get an existing React instance by project_name and react_type.

        Args:
            project_name: Name of the project
            react_type: Type of ReAct process

        Returns:
            React instance if it exists, None otherwise
        """
        instance_key = self._generate_instance_key(project_name, react_type)
        return self._instances.get(instance_key)

    def remove_react(self, project_name: str, react_type: str) -> bool:
        """
        Remove a React instance from the service.

        Args:
            project_name: Name of the project
            react_type: Type of ReAct process

        Returns:
            True if the instance was removed, False if it didn't exist
        """
        instance_key = self._generate_instance_key(project_name, react_type)
        if instance_key in self._instances:
            del self._instances[instance_key]
            return True
        return False

    def clear_all_instances(self):
        """
        Clear all stored React instances.
        """
        self._instances.clear()

    def list_instances(self) -> Dict[str, React]:
        """
        Get a copy of all currently stored React instances.

        Returns:
            Dictionary mapping instance keys to React instances
        """
        return self._instances.copy()


# Global instance of the React service
react_service = ReactService()