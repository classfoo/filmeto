"""
Message module for Filmeto agent system.
Defines the AgentMessage class and message types.
"""
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import uuid
from datetime import datetime
from agent.chat.agent_chat_types import MessageType, ContentType


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


@dataclass
class AgentMessage:
    """
    Represents a message in the agent communication system.
    """
    message_type: MessageType
    sender_id: str
    sender_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    structured_content: List[StructureContent] = field(default_factory=list)
    
    def get_text_content(self) -> str:
        """
        Extract text content from structured_content for backward compatibility.
        Returns the first TEXT content found, or empty string if none exists.
        """
        if not self.structured_content:
            return ""
        for sc in self.structured_content:
            if sc.content_type == ContentType.TEXT and isinstance(sc.data, str):
                return sc.data
        return ""
    
    @property
    def content(self) -> str:
        """
        Property for backward compatibility - returns text content from structured_content.
        """
        return self.get_text_content()