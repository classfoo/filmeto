"""Stream manager for handling multi-agent streaming sessions.

This module provides session management and message aggregation for
streaming multi-agent conversations.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import uuid
import asyncio
import logging

from agent.streaming.protocol import (
    StreamEvent,
    StreamEventType,
    StreamEventEmitter,
    AgentRole,
    StructuredContent,
    PlanContent,
    TaskContent,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """Aggregated message from an agent."""
    message_id: str
    agent_name: str
    agent_role: AgentRole
    content: str = ""
    structured_contents: List[StructuredContent] = field(default_factory=list)
    is_complete: bool = False
    is_thinking: bool = False
    thinking_content: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    task_id: Optional[str] = None
    plan_id: Optional[str] = None
    error: Optional[str] = None
    
    def append_content(self, content: str):
        """Append content to the message."""
        self.content += content
    
    def set_content(self, content: str):
        """Set content (replace)."""
        self.content = content
    
    def add_structured_content(self, structured: StructuredContent):
        """Add structured content."""
        self.structured_contents.append(structured)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "agent_name": self.agent_name,
            "agent_role": self.agent_role.value,
            "content": self.content,
            "structured_contents": [s.to_dict() for s in self.structured_contents],
            "is_complete": self.is_complete,
            "is_thinking": self.is_thinking,
            "thinking_content": self.thinking_content,
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "plan_id": self.plan_id,
            "error": self.error,
        }


@dataclass
class AgentStreamSession:
    """Session for a streaming multi-agent conversation."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: Dict[str, AgentMessage] = field(default_factory=dict)  # message_id -> AgentMessage
    message_order: List[str] = field(default_factory=list)  # Ordered list of message_ids
    agent_messages: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))  # agent_name -> message_ids
    current_plan: Optional[Dict[str, Any]] = None
    plan_id: Optional[str] = None
    is_active: bool = True
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    
    def get_message(self, message_id: str) -> Optional[AgentMessage]:
        """Get message by ID."""
        return self.messages.get(message_id)
    
    def get_or_create_message(
        self,
        message_id: str,
        agent_name: str,
        agent_role: AgentRole
    ) -> AgentMessage:
        """Get or create a message."""
        if message_id not in self.messages:
            message = AgentMessage(
                message_id=message_id,
                agent_name=agent_name,
                agent_role=agent_role,
            )
            self.messages[message_id] = message
            self.message_order.append(message_id)
            self.agent_messages[agent_name].append(message_id)
        return self.messages[message_id]
    
    def get_all_messages(self) -> List[AgentMessage]:
        """Get all messages in order."""
        return [self.messages[mid] for mid in self.message_order if mid in self.messages]
    
    def get_agent_messages(self, agent_name: str) -> List[AgentMessage]:
        """Get all messages from a specific agent."""
        message_ids = self.agent_messages.get(agent_name, [])
        return [self.messages[mid] for mid in message_ids if mid in self.messages]
    
    def get_active_agents(self) -> List[str]:
        """Get list of agents that have messages."""
        return list(self.agent_messages.keys())
    
    def set_plan(self, plan: Dict[str, Any], plan_id: str):
        """Set the current execution plan."""
        self.current_plan = plan
        self.plan_id = plan_id
    
    def end_session(self):
        """End the session."""
        self.is_active = False
        self.end_time = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.get_all_messages()],
            "current_plan": self.current_plan,
            "plan_id": self.plan_id,
            "is_active": self.is_active,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "active_agents": self.get_active_agents(),
        }


class AgentStreamManager:
    """Manager for streaming multi-agent conversations.
    
    This class:
    - Creates and manages stream sessions
    - Aggregates streaming events into messages
    - Provides callbacks for UI updates
    - Handles concurrent agent execution
    """
    
    def __init__(self):
        """Initialize stream manager."""
        self._sessions: Dict[str, AgentStreamSession] = {}
        self._emitters: Dict[str, StreamEventEmitter] = {}
        self._ui_callbacks: List[Callable[[StreamEvent, AgentStreamSession], None]] = []
        self._async_ui_callbacks: List[Callable[[StreamEvent, AgentStreamSession], Any]] = []
    
    def create_session(self) -> tuple[AgentStreamSession, StreamEventEmitter]:
        """Create a new streaming session with emitter."""
        session = AgentStreamSession()
        emitter = StreamEventEmitter(session_id=session.session_id)
        
        # Register internal event handler
        emitter.add_callback(lambda event: self._handle_event(event, session))
        
        self._sessions[session.session_id] = session
        self._emitters[session.session_id] = emitter
        
        return session, emitter
    
    def get_session(self, session_id: str) -> Optional[AgentStreamSession]:
        """Get session by ID."""
        return self._sessions.get(session_id)
    
    def get_emitter(self, session_id: str) -> Optional[StreamEventEmitter]:
        """Get emitter by session ID."""
        return self._emitters.get(session_id)
    
    def end_session(self, session_id: str):
        """End a session."""
        session = self._sessions.get(session_id)
        if session:
            session.end_session()
    
    def add_ui_callback(self, callback: Callable[[StreamEvent, AgentStreamSession], None]):
        """Add a UI callback for stream events."""
        self._ui_callbacks.append(callback)
    
    def add_async_ui_callback(self, callback: Callable[[StreamEvent, AgentStreamSession], Any]):
        """Add an async UI callback."""
        self._async_ui_callbacks.append(callback)
    
    def remove_ui_callback(self, callback: Callable):
        """Remove a UI callback."""
        if callback in self._ui_callbacks:
            self._ui_callbacks.remove(callback)
        if callback in self._async_ui_callbacks:
            self._async_ui_callbacks.remove(callback)
    
    def _handle_event(self, event: StreamEvent, session: AgentStreamSession):
        """Handle a streaming event and update session."""
        event_type = event.event_type
        
        # Handle session events
        if event_type == StreamEventType.SESSION_START:
            session.is_active = True
            
        elif event_type == StreamEventType.SESSION_END:
            session.end_session()
        
        # Handle agent events
        elif event_type == StreamEventType.AGENT_START:
            message = session.get_or_create_message(
                event.message_id,
                event.agent_name,
                event.agent_role
            )
            message.is_thinking = True
            
        elif event_type == StreamEventType.AGENT_THINKING:
            message = session.get_or_create_message(
                event.message_id,
                event.agent_name,
                event.agent_role
            )
            message.is_thinking = True
            if event.structured_content:
                message.thinking_content = event.structured_content.data.get("thinking_text", "")
                
        elif event_type == StreamEventType.AGENT_CONTENT:
            message = session.get_or_create_message(
                event.message_id,
                event.agent_name,
                event.agent_role
            )
            message.is_thinking = False
            
            # Handle content based on append flag
            if event.metadata.get("append", True):
                message.append_content(event.content)
            else:
                message.set_content(event.content)
            
            # Add structured content if present
            if event.structured_content:
                message.add_structured_content(event.structured_content)
                
        elif event_type == StreamEventType.CONTENT_TOKEN:
            message = session.get_or_create_message(
                event.message_id,
                event.agent_name,
                event.agent_role
            )
            message.is_thinking = False
            message.append_content(event.content)
            
        elif event_type == StreamEventType.AGENT_COMPLETE:
            message = session.get_message(event.message_id)
            if message:
                message.is_complete = True
                message.is_thinking = False
                if event.content:
                    message.set_content(event.content)
                    
        elif event_type == StreamEventType.AGENT_ERROR:
            message = session.get_or_create_message(
                event.message_id,
                event.agent_name,
                event.agent_role
            )
            message.error = event.content
            message.is_complete = True
            message.is_thinking = False
        
        # Handle plan events
        elif event_type == StreamEventType.PLAN_CREATED:
            if event.structured_content and isinstance(event.structured_content, PlanContent):
                session.set_plan(event.structured_content.data, event.plan_id)
            message = session.get_or_create_message(
                event.message_id,
                event.agent_name,
                event.agent_role
            )
            if event.structured_content:
                message.add_structured_content(event.structured_content)
            message.plan_id = event.plan_id
            
        elif event_type == StreamEventType.PLAN_TASK_START:
            message = session.get_or_create_message(
                event.message_id,
                event.agent_name,
                event.agent_role
            )
            message.task_id = str(event.task_id)
            message.plan_id = event.plan_id
            if event.structured_content:
                message.add_structured_content(event.structured_content)
                
        elif event_type == StreamEventType.PLAN_TASK_COMPLETE:
            message = session.get_or_create_message(
                event.message_id,
                event.agent_name,
                event.agent_role
            )
            message.is_complete = True
            if event.structured_content:
                message.add_structured_content(event.structured_content)
        
        # Handle media and reference events
        elif event_type == StreamEventType.CONTENT_MEDIA:
            message = session.get_or_create_message(
                event.message_id,
                event.agent_name,
                event.agent_role
            )
            if event.structured_content:
                message.add_structured_content(event.structured_content)
                
        elif event_type == StreamEventType.CONTENT_REFERENCE:
            message = session.get_or_create_message(
                event.message_id,
                event.agent_name,
                event.agent_role
            )
            if event.structured_content:
                message.add_structured_content(event.structured_content)
        
        # Call UI callbacks
        self._notify_ui(event, session)
    
    def _notify_ui(self, event: StreamEvent, session: AgentStreamSession):
        """Notify UI callbacks of an event."""
        for callback in self._ui_callbacks:
            try:
                callback(event, session)
            except Exception as e:
                logger.error(f"Error in UI callback: {e}")
    
    async def _notify_ui_async(self, event: StreamEvent, session: AgentStreamSession):
        """Notify async UI callbacks of an event."""
        # Call sync callbacks
        self._notify_ui(event, session)
        
        # Call async callbacks
        for callback in self._async_ui_callbacks:
            try:
                result = callback(event, session)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in async UI callback: {e}")


class DependencyGraph:
    """Dependency graph for task execution ordering.
    
    This class manages task dependencies and determines which tasks
    can be executed in parallel.
    """
    
    def __init__(self):
        """Initialize dependency graph."""
        self._tasks: Dict[str, Dict[str, Any]] = {}  # task_id -> task info
        self._dependencies: Dict[str, List[str]] = defaultdict(list)  # task_id -> list of dependencies
        self._dependents: Dict[str, List[str]] = defaultdict(list)  # task_id -> list of dependents
        self._completed: set = set()
        self._failed: set = set()
        self._running: set = set()
    
    def add_task(self, task_id: str, task_info: Dict[str, Any], dependencies: List[str] = None):
        """Add a task with its dependencies."""
        self._tasks[task_id] = task_info
        if dependencies:
            self._dependencies[task_id] = list(dependencies)
            for dep in dependencies:
                self._dependents[dep].append(task_id)
    
    def add_tasks_from_plan(self, plan: Dict[str, Any]):
        """Add tasks from an execution plan."""
        tasks = plan.get("tasks", [])
        for task in tasks:
            task_id = str(task.get("task_id", len(self._tasks)))
            dependencies = [str(d) for d in task.get("dependencies", [])]
            self.add_task(task_id, task, dependencies)
    
    def get_ready_tasks(self) -> List[str]:
        """Get tasks that are ready to execute (all dependencies met)."""
        ready = []
        for task_id in self._tasks:
            if task_id in self._completed or task_id in self._failed or task_id in self._running:
                continue
            
            deps = self._dependencies.get(task_id, [])
            if all(dep in self._completed for dep in deps):
                ready.append(task_id)
        
        return ready
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task info by ID."""
        return self._tasks.get(task_id)
    
    def mark_running(self, task_id: str):
        """Mark a task as running."""
        self._running.add(task_id)
    
    def mark_complete(self, task_id: str):
        """Mark a task as complete."""
        self._running.discard(task_id)
        self._completed.add(task_id)
    
    def mark_failed(self, task_id: str):
        """Mark a task as failed."""
        self._running.discard(task_id)
        self._failed.add(task_id)
    
    def is_complete(self) -> bool:
        """Check if all tasks are complete or failed."""
        return len(self._completed) + len(self._failed) == len(self._tasks)
    
    def get_completion_status(self) -> Dict[str, Any]:
        """Get completion status."""
        return {
            "total": len(self._tasks),
            "completed": len(self._completed),
            "failed": len(self._failed),
            "running": len(self._running),
            "pending": len(self._tasks) - len(self._completed) - len(self._failed) - len(self._running),
            "is_complete": self.is_complete(),
        }
    
    def get_parallel_groups(self) -> List[List[str]]:
        """Get groups of tasks that can be executed in parallel.
        
        Returns a list of groups, where each group contains tasks
        that can run in parallel (after previous groups complete).
        """
        groups = []
        remaining = set(self._tasks.keys())
        completed_for_grouping = set()
        
        while remaining:
            # Find tasks with all dependencies in completed_for_grouping
            group = []
            for task_id in list(remaining):
                deps = self._dependencies.get(task_id, [])
                if all(dep in completed_for_grouping for dep in deps):
                    group.append(task_id)
            
            if not group:
                # No more tasks can be scheduled (likely circular dependency)
                logger.warning(f"Could not schedule remaining tasks: {remaining}")
                break
            
            groups.append(group)
            for task_id in group:
                remaining.discard(task_id)
                completed_for_grouping.add(task_id)
        
        return groups
