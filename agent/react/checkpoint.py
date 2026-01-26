"""Checkpoint data structure for ReAct state persistence."""
from dataclasses import dataclass
from typing import Optional
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
    """
    run_id: str
    step_id: int
    status: str
    messages: list
    pending_user_messages: list
    last_tool_calls: Optional[list] = None
    last_tool_results: Optional[list] = None
    created_at: float = time.time()
    updated_at: float = time.time()
