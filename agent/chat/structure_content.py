"""
Structure content module for Filmeto agent system.
Defines the StructureContent class for structured message content.
"""
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import uuid
from agent.chat.agent_chat_types import ContentType


@dataclass
class StructureContent:
    """
    Represents a structured piece of content within a message.
    Each StructureContent represents a specific type of content in a message card.
    """
    content_type: ContentType
    data: Union[str, Dict[str, Any], List[Any]]
    title: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    content_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert the StructureContent to a dictionary representation."""
        return {
            "content_id": self.content_id,
            "content_type": self.content_type.value,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StructureContent':
        """Create a StructureContent from a dictionary."""
        return cls(
            content_id=data.get("content_id", str(uuid.uuid4())),
            content_type=ContentType(data["content_type"]),
            title=data.get("title"),
            description=data.get("description"),
            data=data["data"],
            metadata=data.get("metadata", {})
        )
