"""Checkpoint data structure for ReAct state persistence."""
from dataclasses import dataclass, field
from typing import Optional, Any, Dict
import time


@dataclass
class CheckpointData:
    """
    Data structure for saving and restoring ReAct state.

    Attributes:
        run_id: Current run identifier
        step_id: Current step in the run
        status: Current status (IDLE, RUNNING, FINAL, FAILED)
        messages: Conversation history
        pending_user_messages: Queue of user messages not yet processed
        last_tool_calls: Information about the last tool calls (optional)
        last_tool_results: Results from the last tool calls (optional)
        todo_state: Current TODO state (optional)
        todo_patches: Accumulated TODO patches for reference (optional)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    run_id: str
    step_id: int
    status: str
    messages: list
    pending_user_messages: list
    last_tool_calls: Optional[list] = None
    last_tool_results: Optional[list] = None
    todo_state: Optional[Dict[str, Any]] = None
    todo_patches: Optional[list] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "step_id": self.step_id,
            "status": self.status,
            "messages": self.messages,
            "pending_user_messages": self.pending_user_messages,
            "last_tool_calls": self.last_tool_calls,
            "last_tool_results": self.last_tool_results,
            "todo_state": self.todo_state,
            "todo_patches": self.todo_patches,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckpointData":
        """Create from dictionary for deserialization."""
        return cls(
            run_id=data["run_id"],
            step_id=data["step_id"],
            status=data["status"],
            messages=data["messages"],
            pending_user_messages=data["pending_user_messages"],
            last_tool_calls=data.get("last_tool_calls"),
            last_tool_results=data.get("last_tool_results"),
            todo_state=data.get("todo_state"),
            todo_patches=data.get("todo_patches"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )
