from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .tool_context import ToolContext


@dataclass
class ToolParameter:
    """
    Represents a parameter of a tool.

    Attributes:
        name: Parameter name
        description: Parameter description
        param_type: Parameter type (string, number, boolean, array, object, etc.)
        required: Whether the parameter is required
        default: Default value for the parameter (optional)
    """
    name: str
    description: str
    param_type: str
    required: bool = False
    default: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "name": self.name,
            "description": self.description,
            "type": self.param_type,
            "required": self.required
        }
        if self.default is not None:
            result["default"] = self.default
        return result


@dataclass
class ToolMetadata:
    """
    Metadata information for a tool.

    Attributes:
        name: Tool name
        description: Tool description
        parameters: List of tool parameters
        return_description: Description of the return value
    """
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    return_description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
            "return_description": self.return_description
        }


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    All tools must inherit from this class and implement the execute method.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, parameters: Dict[str, Any], context: Optional["ToolContext"] = None) -> Any:
        """
        Execute the tool with given parameters and context.

        Args:
            parameters: Dictionary of parameters for the tool
            context: Optional ToolContext object containing workspace, project_name, etc.

        Returns:
            Result of the tool execution
        """
        pass

    def metadata(self, lang: str = "en_US") -> ToolMetadata:
        """
        Get metadata information for the tool.

        Args:
            lang: Language code for localized metadata (e.g., "en_US", "zh_CN")

        Returns:
            ToolMetadata object containing the tool's metadata
        """
        # Default implementation returns basic metadata
        # Subclasses should override this to provide detailed metadata
        return ToolMetadata(
            name=self.name,
            description=self.description,
            parameters=[],
            return_description=""
        )