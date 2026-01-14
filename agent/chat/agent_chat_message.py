"""
Message module for Filmeto agent system.
Defines the AgentMessage class and message types.
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import uuid
from datetime import datetime


class MessageType(Enum):
    """Enumeration of different message types."""
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    COMMAND = "command"
    ERROR = "error"
    SYSTEM = "system"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"


class ContentType(Enum):
    """Enumeration of different structured content types."""
    TEXT = "text"
    CODE_BLOCK = "code_block"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE_ATTACHMENT = "file_attachment"
    TABLE = "table"
    CHART = "chart"
    LINK = "link"
    BUTTON = "button"
    FORM = "form"
    PROGRESS = "progress"
    METADATA = "metadata"


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
    content: str
    message_type: MessageType
    sender_id: str
    sender_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    structured_content: List[StructureContent] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary representation."""
        return {
            "message_id": self.message_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "structured_content": [item.to_dict() for item in self.structured_content]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create an AgentMessage from a dictionary."""
        structured_content = [
            StructureContent.from_dict(item)
            for item in data.get("structured_content", [])
        ]

        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            content=data["content"],
            message_type=MessageType(data["message_type"]),
            sender_id=data["sender_id"],
            sender_name=data.get("sender_name", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now(),
            metadata=data.get("metadata", {}),
            structured_content=structured_content
        )