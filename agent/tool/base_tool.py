from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    All tools must inherit from this class and implement the execute method.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Any:
        """
        Execute the tool with given parameters and context.
        
        Args:
            parameters: Dictionary of parameters for the tool
            context: Optional context information (workspace, project, etc.)
            
        Returns:
            Result of the tool execution
        """
        pass