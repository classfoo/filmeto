"""
Message module for Filmeto agent system.
Defines the AgentMessage class and message types.
"""
from enum import Enum
from typing import Any, Dict, Optional
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary representation."""
        return {
            "message_id": self.message_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create an AgentMessage from a dictionary."""
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            content=data["content"],
            message_type=MessageType(data["message_type"]),
            sender_id=data["sender_id"],
            sender_name=data.get("sender_name", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now(),
            metadata=data.get("metadata", {})
        )