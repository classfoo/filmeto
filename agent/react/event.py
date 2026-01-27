"""Event types for ReAct pattern."""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Set


class ReactEventType(str, Enum):
    """Constants for ReAct event types."""
    LLM_THINKING = "llm_thinking"
    TOOL_START = "tool_start"
    TOOL_PROGRESS = "tool_progress"
    TOOL_END = "tool_end"
    LLM_OUTPUT = "llm_output"
    FINAL = "final"
    ERROR = "error"
    USER_MESSAGE = "user_message"
    PAUSE = "pause"
    RESUME = "resume"
    STATUS_CHANGE = "status_change"
    TODO_UPDATE = "todo_update"

    @classmethod
    def is_tool_event(cls, event_type: str) -> bool:
        """Check if event type is tool-related."""
        return event_type in {cls.TOOL_START.value, cls.TOOL_PROGRESS.value, cls.TOOL_END.value}

    @classmethod
    def is_terminal_event(cls, event_type: str) -> bool:
        """Check if event type indicates termination."""
        return event_type in {cls.FINAL.value, cls.ERROR.value}

    @classmethod
    def get_valid_types(cls) -> Set[str]:
        """Get all valid event type values."""
        return {e.value for e in cls}


@dataclass
class ReactEvent:
    """
    Represents an event in the ReAct process.

    Attributes:
        event_type: Type of event (llm_thinking, tool_start, tool_progress, tool_end, llm_output, final, error)
        project_name: Name of the project
        react_type: Type of ReAct process
        run_id: Unique identifier for the current run
        step_id: Step number in the current run
        payload: Event-specific data (must be JSON serializable)
    """
    event_type: str
    project_name: str
    react_type: str
    run_id: str
    step_id: int
    payload: Dict[str, Any]

    def __post_init__(self):
        """Validate event fields."""
        # Validate event_type
        valid_types = ReactEventType.get_valid_types()
        if self.event_type not in valid_types:
            raise ValueError(
                f"Invalid event_type: '{self.event_type}'. "
                f"Must be one of: {sorted(valid_types)}"
            )

        # Validate step_id
        if self.step_id < 0:
            raise ValueError(f"step_id must be >= 0, got {self.step_id}")

        # Validate payload is a dict
        if not isinstance(self.payload, dict):
            raise ValueError(f"payload must be a dict, got {type(self.payload).__name__}")
