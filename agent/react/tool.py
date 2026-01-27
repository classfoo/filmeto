"""
Tool definition for ReAct pattern.

This module defines the ReactTool class which encapsulates tool metadata
for use in ReAct processes.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ReactTool:
    """
    Represents a tool available in a ReAct process with its metadata.
    
    Attributes:
        name: The name of the tool
        description: A description of what the tool does
        args: A dictionary defining the arguments the tool accepts
    """
    name: str
    description: str
    args: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the tool to a dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "args": self.args
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReactTool':
        """Create a ReactTool from a dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            args=data.get("args", {})
        )