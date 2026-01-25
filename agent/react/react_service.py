"""
React Service Module

Manages React instances by project name and react type.
"""
from threading import Lock
from typing import Any, Callable, Dict, Optional

from .react import React


class ReactService:
    """
    Singleton service to manage React instances with reuse capability.
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
        return f"{project_name}:{react_type}"

    def get_or_create_react(
        self,
        project_name: str,
        react_type: str,
        build_prompt_function: Callable[[], str],
        tool_call_function: Callable[[str, Dict[str, Any]], Any],
        *,
        workspace=None,
        llm_service=None,
        max_steps: int = 20,
    ) -> React:
        instance_key = self._generate_instance_key(project_name, react_type)

        if instance_key in self._instances:
            return self._instances[instance_key]

        react_instance = React(
            workspace=workspace,
            project_name=project_name,
            react_type=react_type,
            build_prompt_function=build_prompt_function,
            tool_call_function=tool_call_function,
            llm_service=llm_service,
            max_steps=max_steps,
        )

        self._instances[instance_key] = react_instance
        return react_instance

    def get_react(self, project_name: str, react_type: str) -> Optional[React]:
        instance_key = self._generate_instance_key(project_name, react_type)
        return self._instances.get(instance_key)

    def remove_react(self, project_name: str, react_type: str) -> bool:
        instance_key = self._generate_instance_key(project_name, react_type)
        if instance_key in self._instances:
            del self._instances[instance_key]
            return True
        return False

    def clear_all_instances(self) -> None:
        self._instances.clear()

    def list_instances(self) -> Dict[str, React]:
        return self._instances.copy()


react_service = ReactService()
