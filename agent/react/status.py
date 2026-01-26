"""Status constants for ReAct process."""


class ReactStatus:
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
        return status in {cls.RUNNING, cls.WAITING}

    @classmethod
    def is_terminal(cls, status: str) -> bool:
        """Check if status indicates a terminal state."""
        return status in {cls.FINAL, cls.FAILED}

    @classmethod
    def is_interactive(cls, status: str) -> bool:
        """Check if status indicates an interactive/paused state."""
        return status in {cls.PAUSED, cls.AWAITING_INPUT}
