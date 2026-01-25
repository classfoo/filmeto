from dataclasses import dataclass
from typing import Any, Dict, Optional
import time


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
    event_type: str  # "llm_thinking" | "tool_start" | "tool_progress" | "tool_end" | "llm_output" | "final" | "error"
    project_name: str
    react_type: str
    run_id: str
    step_id: int
    payload: Dict[str, Any]


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
    """
    run_id: str
    step_id: int
    status: str  # "IDLE" | "RUNNING" | "FINAL" | "FAILED"
    messages: list
    pending_user_messages: list
    last_tool_calls: Optional[list] = None
    last_tool_results: Optional[list] = None
    created_at: float = time.time()
    updated_at: float = time.time()


class ReactStatus:
    """Constants for ReAct status values."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    FINAL = "FINAL"
    FAILED = "FAILED"


class ReactEventType:
    """Constants for ReAct event types."""
    LLM_THINKING = "llm_thinking"
    TOOL_START = "tool_start"
    TOOL_PROGRESS = "tool_progress"
    TOOL_END = "tool_end"
    LLM_OUTPUT = "llm_output"
    FINAL = "final"
    ERROR = "error"
