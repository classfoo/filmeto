"""Streaming message protocol for multi-agent communication.

This module defines the structured message format for streaming agent conversations,
enabling group-chat style presentation of multi-agent collaboration.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json


class StreamEventType(str, Enum):
    """Types of streaming events."""
    # Session events
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    
    # Agent lifecycle events
    AGENT_START = "agent_start"
    AGENT_THINKING = "agent_thinking"
    AGENT_CONTENT = "agent_content"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    
    # Plan events
    PLAN_CREATED = "plan_created"
    PLAN_UPDATED = "plan_updated"
    PLAN_TASK_START = "plan_task_start"
    PLAN_TASK_COMPLETE = "plan_task_complete"
    
    # Content events
    CONTENT_TOKEN = "content_token"
    CONTENT_CHUNK = "content_chunk"
    CONTENT_MEDIA = "content_media"
    CONTENT_REFERENCE = "content_reference"
    
    # Status events
    STATUS_UPDATE = "status_update"
    PROGRESS_UPDATE = "progress_update"


class AgentRole(str, Enum):
    """Agent roles in the film production team."""
    USER = "user"
    # Main agent roles (these should be aggregated as main agent messages)
    MAIN_AGENT = "main_agent"  # Virtual role for main agent aggregation
    COORDINATOR = "coordinator"
    PLANNER = "planner"
    QUESTION_UNDERSTANDING = "question_understanding"
    EXECUTOR = "executor"
    PLAN_REFINEMENT = "plan_refinement"
    RESPONSE = "response"
    # Sub-agent roles (these should be aggregated separately)
    PRODUCTION = "production"
    DIRECTOR = "director"
    SCREENWRITER = "screenwriter"
    ACTOR = "actor"
    MAKEUP_ARTIST = "makeup_artist"
    SUPERVISOR = "supervisor"
    SOUND_MIXER = "sound_mixer"
    EDITOR = "editor"
    # System roles
    REVIEWER = "reviewer"
    SYNTHESIZER = "synthesizer"
    SYSTEM = "system"
    
    @classmethod
    def from_agent_name(cls, name: str) -> 'AgentRole':
        """Convert agent name to role."""
        name_mapping = {
            # Main agent roles
            "Coordinator": cls.COORDINATOR,
            "Planner": cls.PLANNER,
            "QuestionUnderstanding": cls.QUESTION_UNDERSTANDING,
            "Executor": cls.EXECUTOR,
            "PlanRefinement": cls.PLAN_REFINEMENT,
            "Response": cls.RESPONSE,
            # Sub-agent roles
            "Production": cls.PRODUCTION,
            "Director": cls.DIRECTOR,
            "Screenwriter": cls.SCREENWRITER,
            "Actor": cls.ACTOR,
            "MakeupArtist": cls.MAKEUP_ARTIST,
            "Supervisor": cls.SUPERVISOR,
            "SoundMixer": cls.SOUND_MIXER,
            "Editor": cls.EDITOR,
            # System roles
            "Reviewer": cls.REVIEWER,
            "Synthesizer": cls.SYNTHESIZER,
        }
        return name_mapping.get(name, cls.SYSTEM)
    
    @classmethod
    def is_main_agent_role(cls, role: 'AgentRole') -> bool:
        """Check if a role belongs to main agent."""
        main_agent_roles = {
            cls.MAIN_AGENT,
            cls.COORDINATOR,
            cls.PLANNER,
            cls.QUESTION_UNDERSTANDING,
            cls.EXECUTOR,
            cls.PLAN_REFINEMENT,
            cls.RESPONSE,
            cls.REVIEWER,
            cls.SYNTHESIZER,
        }
        return role in main_agent_roles
    
    @classmethod
    def is_sub_agent_role(cls, role: 'AgentRole') -> bool:
        """Check if a role belongs to sub-agent."""
        sub_agent_roles = {
            cls.PRODUCTION,
            cls.DIRECTOR,
            cls.SCREENWRITER,
            cls.ACTOR,
            cls.MAKEUP_ARTIST,
            cls.SUPERVISOR,
            cls.SOUND_MIXER,
            cls.EDITOR,
        }
        return role in sub_agent_roles
    
    @property
    def display_name(self) -> str:
        """Get display name for the role."""
        display_names = {
            AgentRole.USER: "User",
            AgentRole.MAIN_AGENT: "Main Agent",
            AgentRole.COORDINATOR: "Coordinator",
            AgentRole.PLANNER: "Planner",
            AgentRole.QUESTION_UNDERSTANDING: "Question Understanding",
            AgentRole.EXECUTOR: "Executor",
            AgentRole.PLAN_REFINEMENT: "Plan Refinement",
            AgentRole.RESPONSE: "Response",
            AgentRole.PRODUCTION: "Producer",
            AgentRole.DIRECTOR: "Director",
            AgentRole.SCREENWRITER: "Screenwriter",
            AgentRole.ACTOR: "Actor",
            AgentRole.MAKEUP_ARTIST: "Makeup Artist",
            AgentRole.SUPERVISOR: "Supervisor",
            AgentRole.SOUND_MIXER: "Sound Mixer",
            AgentRole.EDITOR: "Editor",
            AgentRole.REVIEWER: "Reviewer",
            AgentRole.SYNTHESIZER: "Synthesizer",
            AgentRole.SYSTEM: "System",
        }
        return display_names.get(self, self.value.title())
    
    @property
    def icon_char(self) -> str:
        """Get icon character for the role."""
        # Unicode icons for each role
        icons = {
            AgentRole.USER: "\ue6b3",  # user icon
            AgentRole.MAIN_AGENT: "🤖",
            AgentRole.COORDINATOR: "C",
            AgentRole.PLANNER: "P",
            AgentRole.QUESTION_UNDERSTANDING: "Q",
            AgentRole.EXECUTOR: "E",
            AgentRole.PLAN_REFINEMENT: "R",
            AgentRole.RESPONSE: "💬",
            AgentRole.PRODUCTION: "🎬",
            AgentRole.DIRECTOR: "🎥",
            AgentRole.SCREENWRITER: "✍️",
            AgentRole.ACTOR: "🎭",
            AgentRole.MAKEUP_ARTIST: "💄",
            AgentRole.SUPERVISOR: "📋",
            AgentRole.SOUND_MIXER: "🎧",
            AgentRole.EDITOR: "✂️",
            AgentRole.REVIEWER: "👁️",
            AgentRole.SYNTHESIZER: "🔗",
            AgentRole.SYSTEM: "⚙️",
        }
        return icons.get(self, "A")
    
    @property
    def color(self) -> str:
        """Get color for the role."""
        colors = {
            AgentRole.USER: "#35373a",
            AgentRole.MAIN_AGENT: "#4a90d9",
            AgentRole.COORDINATOR: "#4a90d9",
            AgentRole.PLANNER: "#7c4dff",
            AgentRole.QUESTION_UNDERSTANDING: "#6c5ce7",
            AgentRole.EXECUTOR: "#a29bfe",
            AgentRole.PLAN_REFINEMENT: "#6c5ce7",
            AgentRole.RESPONSE: "#74b9ff",
            AgentRole.PRODUCTION: "#ff6b6b",
            AgentRole.DIRECTOR: "#4ecdc4",
            AgentRole.SCREENWRITER: "#f7dc6f",
            AgentRole.ACTOR: "#bb8fce",
            AgentRole.MAKEUP_ARTIST: "#f1948a",
            AgentRole.SUPERVISOR: "#85c1e9",
            AgentRole.SOUND_MIXER: "#82e0aa",
            AgentRole.EDITOR: "#f8b739",
            AgentRole.REVIEWER: "#fd79a8",
            AgentRole.SYNTHESIZER: "#fdcb6e",
            AgentRole.SYSTEM: "#7f8c8d",
        }
        return colors.get(self, "#3d3f4e")


class ContentType(str, Enum):
    """Types of content in messages."""
    TEXT = "text"
    MARKDOWN = "markdown"
    PLAN = "plan"
    TASK = "task"
    MEDIA = "media"
    REFERENCE = "reference"
    THINKING = "thinking"
    CODE = "code"
    ERROR = "error"


class StructuredContent:
    """Base class for structured content."""
    
    def __init__(self, content_type: ContentType, data: Any):
        """Initialize structured content."""
        self.content_type = content_type
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content_type": self.content_type.value,
            "data": self.data
        }


class PlanContent(StructuredContent):
    """Execution plan content."""
    
    def __init__(
        self,
        description: str = "",
        phase: str = "",
        tasks: List[Dict[str, Any]] = None,
        success_criteria: str = ""
    ):
        """Initialize plan content."""
        self.description = description
        self.phase = phase
        self.tasks = tasks or []
        self.success_criteria = success_criteria
        
        data = {
            "description": self.description,
            "phase": self.phase,
            "tasks": self.tasks,
            "success_criteria": self.success_criteria
        }
        super().__init__(ContentType.PLAN, data)
    
    def add_task(self, task: Dict[str, Any]):
        """Add a task to the plan."""
        self.tasks.append(task)
        self.data["tasks"] = self.tasks


class TaskContent(StructuredContent):
    """Task execution content."""
    
    def __init__(
        self,
        task_id: Union[str, int] = "",
        agent_name: str = "",
        skill_name: str = "",
        status: str = "pending",  # pending, running, success, failed
        message: str = "",
        quality_score: Optional[float] = None,
        output: Any = None
    ):
        """Initialize task content."""
        self.task_id = task_id
        self.agent_name = agent_name
        self.skill_name = skill_name
        self.status = status
        self.message = message
        self.quality_score = quality_score
        self.output = output
        
        data = {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "skill_name": self.skill_name,
            "status": self.status,
            "message": self.message,
            "quality_score": self.quality_score,
            "output": self.output
        }
        super().__init__(ContentType.TASK, data)


class MediaContent(StructuredContent):
    """Media content (images, videos, audio)."""
    
    def __init__(
        self,
        media_type: str = "image",  # image, video, audio
        url: str = "",
        thumbnail_url: Optional[str] = None,
        title: str = "",
        description: str = "",
        metadata: Dict[str, Any] = None
    ):
        """Initialize media content."""
        self.media_type = media_type
        self.url = url
        self.thumbnail_url = thumbnail_url
        self.title = title
        self.description = description
        self.metadata = metadata or {}
        
        data = {
            "media_type": self.media_type,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "title": self.title,
            "description": self.description,
            "metadata": self.metadata
        }
        super().__init__(ContentType.MEDIA, data)


class ReferenceContent(StructuredContent):
    """Reference to project elements."""
    
    def __init__(
        self,
        ref_type: str = "",  # timeline_item, task, character, resource
        ref_id: str = "",
        name: str = "",
        description: str = "",
        metadata: Dict[str, Any] = None
    ):
        """Initialize reference content."""
        self.ref_type = ref_type
        self.ref_id = ref_id
        self.name = name
        self.description = description
        self.metadata = metadata or {}
        
        data = {
            "ref_type": self.ref_type,
            "ref_id": self.ref_id,
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata
        }
        super().__init__(ContentType.REFERENCE, data)


class ThinkingContent(StructuredContent):
    """Agent thinking/reasoning content."""
    
    def __init__(
        self,
        thinking_text: str = "",
        is_complete: bool = False
    ):
        """Initialize thinking content."""
        self.thinking_text = thinking_text
        self.is_complete = is_complete
        
        data = {
            "thinking_text": self.thinking_text,
            "is_complete": self.is_complete
        }
        super().__init__(ContentType.THINKING, data)


@dataclass
class StreamEvent:
    """A streaming event in the agent conversation."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: StreamEventType = StreamEventType.CONTENT_TOKEN
    agent_role: AgentRole = AgentRole.SYSTEM
    agent_name: str = ""
    session_id: str = ""
    message_id: str = ""  # Groups content into messages
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Content fields
    content: str = ""  # For text content
    structured_content: Optional[StructuredContent] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Task/Plan context
    task_id: Optional[Union[str, int]] = None
    plan_id: Optional[str] = None
    
    # Progress
    progress: Optional[float] = None  # 0.0 - 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "agent_role": self.agent_role.value,
            "agent_name": self.agent_name,
            "session_id": self.session_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "content": self.content,
            "metadata": self.metadata,
        }
        
        if self.structured_content:
            result["structured_content"] = self.structured_content.to_dict()
        if self.task_id is not None:
            result["task_id"] = self.task_id
        if self.plan_id:
            result["plan_id"] = self.plan_id
        if self.progress is not None:
            result["progress"] = self.progress
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamEvent':
        """Create from dictionary."""
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=StreamEventType(data.get("event_type", "content_token")),
            agent_role=AgentRole(data.get("agent_role", "system")),
            agent_name=data.get("agent_name", ""),
            session_id=data.get("session_id", ""),
            message_id=data.get("message_id", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            task_id=data.get("task_id"),
            plan_id=data.get("plan_id"),
            progress=data.get("progress"),
        )


class StreamEventEmitter:
    """Emitter for streaming events with callback support."""
    
    def __init__(self, session_id: str = None):
        """Initialize emitter."""
        self.session_id = session_id or str(uuid.uuid4())
        self._callbacks: List[Callable[[StreamEvent], None]] = []
        self._async_callbacks: List[Callable[[StreamEvent], Any]] = []
        self._message_ids: Dict[str, str] = {}  # agent_name -> current message_id
        self._main_agent_message_id: Optional[str] = None  # Aggregated main agent message ID
    
    def add_callback(self, callback: Callable[[StreamEvent], None]):
        """Add a synchronous callback."""
        self._callbacks.append(callback)
    
    def add_async_callback(self, callback: Callable[[StreamEvent], Any]):
        """Add an async callback."""
        self._async_callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
        if callback in self._async_callbacks:
            self._async_callbacks.remove(callback)
    
    def _get_or_create_message_id(self, agent_name: str) -> str:
        """Get or create message ID for an agent."""
        if agent_name not in self._message_ids:
            self._message_ids[agent_name] = str(uuid.uuid4())
        return self._message_ids[agent_name]
    
    def _new_message_id(self, agent_name: str) -> str:
        """Create new message ID for an agent."""
        self._message_ids[agent_name] = str(uuid.uuid4())
        return self._message_ids[agent_name]
    
    def _get_main_agent_message_id(self) -> str:
        """Get or create the main agent aggregated message ID."""
        if self._main_agent_message_id is None:
            self._main_agent_message_id = str(uuid.uuid4())
        return self._main_agent_message_id
    
    def _reset_main_agent_message_id(self):
        """Reset main agent message ID for new message."""
        self._main_agent_message_id = str(uuid.uuid4())
    
    def emit(self, event: StreamEvent):
        """Emit an event synchronously."""
        event.session_id = self.session_id
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                import logging
                logging.error(f"Error in stream callback: {e}")
    
    async def emit_async(self, event: StreamEvent):
        """Emit an event asynchronously."""
        import asyncio
        event.session_id = self.session_id
        
        # Call sync callbacks
        self.emit(event)
        
        # Call async callbacks
        for callback in self._async_callbacks:
            try:
                result = callback(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                import logging
                logging.error(f"Error in async stream callback: {e}")
    
    # Convenience methods for common events
    
    def emit_session_start(self, metadata: Dict[str, Any] = None):
        """Emit session start event."""
        event = StreamEvent(
            event_type=StreamEventType.SESSION_START,
            agent_role=AgentRole.SYSTEM,
            metadata=metadata or {}
        )
        self.emit(event)
        return event
    
    def emit_session_end(self, metadata: Dict[str, Any] = None):
        """Emit session end event."""
        event = StreamEvent(
            event_type=StreamEventType.SESSION_END,
            agent_role=AgentRole.SYSTEM,
            metadata=metadata or {}
        )
        self.emit(event)
        return event
    
    def emit_agent_start(self, agent_name: str, agent_role: AgentRole = None):
        """Emit agent start event."""
        if agent_role is None:
            agent_role = AgentRole.from_agent_name(agent_name)
        
        # For main agent roles, use aggregated message ID
        if AgentRole.is_main_agent_role(agent_role):
            message_id = self._get_main_agent_message_id()
            # Override role to MAIN_AGENT for aggregation
            display_role = AgentRole.MAIN_AGENT
            display_name = "MainAgent"
        else:
            message_id = self._new_message_id(agent_name)
            display_role = agent_role
            display_name = agent_name
        
        event = StreamEvent(
            event_type=StreamEventType.AGENT_START,
            agent_role=display_role,
            agent_name=display_name,
            message_id=message_id,
            metadata={"original_role": agent_role.value, "original_name": agent_name}
        )
        self.emit(event)
        return event
    
    def emit_agent_thinking(self, agent_name: str, thinking_text: str, is_complete: bool = False):
        """Emit agent thinking event."""
        agent_role = AgentRole.from_agent_name(agent_name)
        
        # For main agent roles, use aggregated message ID
        if AgentRole.is_main_agent_role(agent_role):
            message_id = self._get_main_agent_message_id()
            display_role = AgentRole.MAIN_AGENT
            display_name = "MainAgent"
        else:
            message_id = self._get_or_create_message_id(agent_name)
            display_role = agent_role
            display_name = agent_name
        
        event = StreamEvent(
            event_type=StreamEventType.AGENT_THINKING,
            agent_role=display_role,
            agent_name=display_name,
            message_id=message_id,
            structured_content=ThinkingContent(
                thinking_text=thinking_text,
                is_complete=is_complete
            ),
            metadata={"original_role": agent_role.value, "original_name": agent_name}
        )
        self.emit(event)
        return event
    
    def emit_agent_content(
        self,
        agent_name: str,
        content: str = "",
        structured_content: StructuredContent = None,
        append: bool = True
    ):
        """Emit agent content event."""
        agent_role = AgentRole.from_agent_name(agent_name)
        
        # For main agent roles, use aggregated message ID
        if AgentRole.is_main_agent_role(agent_role):
            message_id = self._get_main_agent_message_id()
            display_role = AgentRole.MAIN_AGENT
            display_name = "MainAgent"
        else:
            message_id = self._get_or_create_message_id(agent_name)
            display_role = agent_role
            display_name = agent_name
        
        event = StreamEvent(
            event_type=StreamEventType.AGENT_CONTENT,
            agent_role=display_role,
            agent_name=display_name,
            message_id=message_id,
            content=content,
            structured_content=structured_content,
            metadata={"append": append, "original_role": agent_role.value, "original_name": agent_name}
        )
        self.emit(event)
        return event
    
    def emit_content_token(self, agent_name: str, token: str):
        """Emit a single content token."""
        agent_role = AgentRole.from_agent_name(agent_name)
        
        # For main agent roles, use aggregated message ID
        if AgentRole.is_main_agent_role(agent_role):
            message_id = self._get_main_agent_message_id()
            display_role = AgentRole.MAIN_AGENT
            display_name = "MainAgent"
        else:
            message_id = self._get_or_create_message_id(agent_name)
            display_role = agent_role
            display_name = agent_name
        
        event = StreamEvent(
            event_type=StreamEventType.CONTENT_TOKEN,
            agent_role=display_role,
            agent_name=display_name,
            message_id=message_id,
            content=token,
            metadata={"original_role": agent_role.value, "original_name": agent_name}
        )
        self.emit(event)
        return event
    
    def emit_agent_complete(self, agent_name: str, final_content: str = ""):
        """Emit agent complete event."""
        agent_role = AgentRole.from_agent_name(agent_name)
        
        # For main agent roles, use aggregated message ID
        if AgentRole.is_main_agent_role(agent_role):
            message_id = self._get_main_agent_message_id()
            display_role = AgentRole.MAIN_AGENT
            display_name = "MainAgent"
        else:
            message_id = self._get_or_create_message_id(agent_name)
            display_role = agent_role
            display_name = agent_name
        
        event = StreamEvent(
            event_type=StreamEventType.AGENT_COMPLETE,
            agent_role=display_role,
            agent_name=display_name,
            message_id=message_id,
            content=final_content,
            metadata={"original_role": agent_role.value, "original_name": agent_name}
        )
        self.emit(event)
        return event
    
    def emit_agent_error(self, agent_name: str, error_message: str):
        """Emit agent error event."""
        agent_role = AgentRole.from_agent_name(agent_name)
        
        # For main agent roles, use aggregated message ID
        if AgentRole.is_main_agent_role(agent_role):
            message_id = self._get_main_agent_message_id()
            display_role = AgentRole.MAIN_AGENT
            display_name = "MainAgent"
        else:
            message_id = self._get_or_create_message_id(agent_name)
            display_role = agent_role
            display_name = agent_name
        
        event = StreamEvent(
            event_type=StreamEventType.AGENT_ERROR,
            agent_role=display_role,
            agent_name=display_name,
            message_id=message_id,
            content=error_message,
            metadata={"original_role": agent_role.value, "original_name": agent_name}
        )
        self.emit(event)
        return event
    
    def emit_plan_created(self, plan: Dict[str, Any], agent_name: str = "Planner"):
        """Emit plan created event."""
        plan_id = str(uuid.uuid4())
        agent_role = AgentRole.PLANNER
        
        # Planner is a main agent role, use aggregated message ID
        message_id = self._get_main_agent_message_id()
        
        plan_content = PlanContent(
            description=plan.get("description", ""),
            phase=plan.get("phase", ""),
            tasks=plan.get("tasks", []),
            success_criteria=plan.get("success_criteria", "")
        )
        
        event = StreamEvent(
            event_type=StreamEventType.PLAN_CREATED,
            agent_role=AgentRole.MAIN_AGENT,
            agent_name="MainAgent",
            message_id=message_id,
            plan_id=plan_id,
            structured_content=plan_content,
            metadata={"original_role": agent_role.value, "original_name": agent_name}
        )
        self.emit(event)
        return event, plan_id
    
    def emit_task_start(
        self,
        task_id: Union[str, int],
        agent_name: str,
        skill_name: str,
        plan_id: str = None
    ):
        """Emit task start event."""
        message_id = self._new_message_id(agent_name)
        agent_role = AgentRole.from_agent_name(agent_name)
        
        task_content = TaskContent(
            task_id=task_id,
            agent_name=agent_name,
            skill_name=skill_name,
            status="running"
        )
        
        event = StreamEvent(
            event_type=StreamEventType.PLAN_TASK_START,
            agent_role=agent_role,
            agent_name=agent_name,
            message_id=message_id,
            task_id=task_id,
            plan_id=plan_id,
            structured_content=task_content,
        )
        self.emit(event)
        return event
    
    def emit_task_complete(
        self,
        task_id: Union[str, int],
        agent_name: str,
        skill_name: str,
        status: str,
        message: str,
        quality_score: float = None,
        output: Any = None,
        plan_id: str = None
    ):
        """Emit task complete event."""
        message_id = self._get_or_create_message_id(agent_name)
        agent_role = AgentRole.from_agent_name(agent_name)
        
        task_content = TaskContent(
            task_id=task_id,
            agent_name=agent_name,
            skill_name=skill_name,
            status=status,
            message=message,
            quality_score=quality_score,
            output=output
        )
        
        event = StreamEvent(
            event_type=StreamEventType.PLAN_TASK_COMPLETE,
            agent_role=agent_role,
            agent_name=agent_name,
            message_id=message_id,
            task_id=task_id,
            plan_id=plan_id,
            structured_content=task_content,
        )
        self.emit(event)
        return event
    
    def emit_media(
        self,
        agent_name: str,
        media_type: str,
        url: str,
        title: str = "",
        description: str = "",
        thumbnail_url: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Emit media content event."""
        message_id = self._get_or_create_message_id(agent_name)
        agent_role = AgentRole.from_agent_name(agent_name)
        
        media_content = MediaContent(
            media_type=media_type,
            url=url,
            thumbnail_url=thumbnail_url,
            title=title,
            description=description,
            metadata=metadata or {}
        )
        
        event = StreamEvent(
            event_type=StreamEventType.CONTENT_MEDIA,
            agent_role=agent_role,
            agent_name=agent_name,
            message_id=message_id,
            structured_content=media_content,
        )
        self.emit(event)
        return event
    
    def emit_reference(
        self,
        agent_name: str,
        ref_type: str,
        ref_id: str,
        name: str,
        description: str = "",
        metadata: Dict[str, Any] = None
    ):
        """Emit reference content event."""
        message_id = self._get_or_create_message_id(agent_name)
        agent_role = AgentRole.from_agent_name(agent_name)
        
        ref_content = ReferenceContent(
            ref_type=ref_type,
            ref_id=ref_id,
            name=name,
            description=description,
            metadata=metadata or {}
        )
        
        event = StreamEvent(
            event_type=StreamEventType.CONTENT_REFERENCE,
            agent_role=agent_role,
            agent_name=agent_name,
            message_id=message_id,
            structured_content=ref_content,
        )
        self.emit(event)
        return event
    
    def emit_progress(self, agent_name: str, progress: float, message: str = ""):
        """Emit progress update event."""
        message_id = self._get_or_create_message_id(agent_name)
        agent_role = AgentRole.from_agent_name(agent_name)
        
        event = StreamEvent(
            event_type=StreamEventType.PROGRESS_UPDATE,
            agent_role=agent_role,
            agent_name=agent_name,
            message_id=message_id,
            content=message,
            progress=progress,
        )
        self.emit(event)
        return event
