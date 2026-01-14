"""
Protocol definitions for the Filmeto agent streaming system.
Defines the core data structures and enums used in the streaming protocol.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import uuid
from datetime import datetime


class AgentRole(Enum):
    """Enumeration of different agent roles."""
    WRITER = "writer"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    EDITOR = "editor"
    DIRECTOR = "director"
    PRODUCER = "producer"
    ASSISTANT = "assistant"


class ContentType(Enum):
    """Enumeration of different content types."""
    TEXT = "text"
    PLAN = "plan"
    TASK = "task"
    MEDIA = "media"
    REFERENCE = "reference"
    THINKING = "thinking"
    CODE = "code"
    DATA = "data"
    ERROR = "error"
    SYSTEM = "system"


@dataclass
class StructuredContent:
    """Base class for structured content in agent messages."""
    content_type: ContentType
    data: Any
    metadata: Optional[Dict[str, Any]] = None
    id: str = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())


@dataclass
class PlanContent(StructuredContent):
    """Content representing a plan or outline."""
    content_type: ContentType = ContentType.PLAN
    title: str = ""
    steps: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.id is None:
            self.id = str(uuid.uuid4())


@dataclass
class TaskContent(StructuredContent):
    """Content representing a task or action item."""
    content_type: ContentType = ContentType.TASK
    title: str = ""
    description: str = ""
    status: str = "pending"  # pending, in_progress, completed, failed
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())


@dataclass
class MediaContent(StructuredContent):
    """Content representing media (images, videos, etc.)."""
    content_type: ContentType = ContentType.MEDIA
    media_type: str = ""  # image, video, audio, document
    url: str = ""
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())


@dataclass
class ReferenceContent(StructuredContent):
    """Content representing a reference or citation."""
    content_type: ContentType = ContentType.REFERENCE
    title: str = ""
    url: str = ""
    source_type: str = ""  # web, book, article, video, etc.
    snippet: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())


@dataclass
class ThinkingContent(StructuredContent):
    """Content representing the agent's thought process."""
    content_type: ContentType = ContentType.THINKING
    thoughts: List[str] = None

    def __post_init__(self):
        if self.thoughts is None:
            self.thoughts = []
        if self.id is None:
            self.id = str(uuid.uuid4())