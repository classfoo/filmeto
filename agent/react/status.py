"""Status constants for ReAct process."""
from enum import Enum


class ReactStatus(str, Enum):
    """Constants for ReAct status values."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    FINAL = "FINAL"
    FAILED = "FAILED"
    WAITING = "WAITING"
    PAUSED = "PAUSED"
    AWAITING_INPUT = "AWAITING_INPUT"

    @classmethod
    def is_active(cls, status: str) -> bool:
        """Check if status indicates an active/running state."""
        return status in {cls.RUNNING.value, cls.WAITING.value}

    @classmethod
    def is_terminal(cls, status: str) -> bool:
        """Check if status indicates a terminal state."""
        return status in {cls.FINAL.value, cls.FAILED.value}

    @classmethod
    def is_interactive(cls, status: str) -> bool:
        """Check if status indicates an interactive/paused state."""
        return status in {cls.PAUSED.value, cls.AWAITING_INPUT.value}
