"""
Tool context module.

Provides the ToolContext class that carries runtime information
for tool execution, such as workspace, project_name, and services.
"""
from typing import Any, Dict, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from app.data.workspace import Workspace


class ToolContext:
    """
    Context object that carries runtime information for tool execution.

    This object is passed to tools when they are executed, providing access to:
    - workspace: The Workspace object containing project and workspace info
    - project_name: The current project name (string)
    - Additional services and runtime data

    Attributes:
        workspace: The Workspace object
        project_name: Name of the current project
        data: Additional context data as key-value pairs
    """

    def __init__(
        self,
        workspace: Optional["Workspace"] = None,
        project_name: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a ToolContext.

        Args:
            workspace: The Workspace object
            project_name: Name of the current project
            **kwargs: Additional context data (e.g., llm_service, skill_service)
        """
        self._workspace = workspace
        self._project_name = project_name
        self._data: Dict[str, Any] = kwargs

    @property
    def workspace(self) -> Optional["Workspace"]:
        """Get the Workspace object."""
        return self._workspace

    @workspace.setter
    def workspace(self, value: "Workspace"):
        """Set the Workspace object."""
        self._workspace = value

    @property
    def project_name(self) -> Optional[str]:
        """Get the project name."""
        return self._project_name

    @project_name.setter
    def project_name(self, value: str):
        """Set the project name."""
        self._project_name = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the context data.

        Args:
            key: The key to look up
            default: Default value if key is not found

        Returns:
            The value associated with the key, or default if not found
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set a value in the context data.

        Args:
            key: The key to set
            value: The value to associate with the key
        """
        self._data[key] = value

    def update(self, data: Dict[str, Any]):
        """
        Update the context data with multiple key-value pairs.

        Args:
            data: Dictionary of key-value pairs to add/update
        """
        self._data.update(data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary representation.

        Note: The workspace object is included directly in the dict.
        For serialization purposes, consider using workspace_path instead.

        Returns:
            Dictionary containing all context data including workspace and project_name
        """
        result = {
            "workspace": self._workspace,
            "project_name": self._project_name,
        }
        result.update(self._data)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolContext":
        """
        Create a ToolContext from a dictionary.

        Args:
            data: Dictionary containing context data.
                  'workspace' can be either a Workspace object or a string path.

        Returns:
            A new ToolContext instance
        """
        workspace = data.pop("workspace", None)
        project_name = data.pop("project_name", None)
        return cls(workspace=workspace, project_name=project_name, **data)

    def __repr__(self) -> str:
        """String representation of the context."""
        workspace_repr = (
            f"Workspace(path={self._workspace.workspace_path if self._workspace else None})"
            if self._workspace else None
        )
        return (
            f"ToolContext(workspace={workspace_repr}, "
            f"project_name={self._project_name!r}, "
            f"data={self._data!r})"
        )
