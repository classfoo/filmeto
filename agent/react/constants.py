"""Constants for React module."""


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


class ReactEventType:
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
    # Stream events
    LLM_STREAM_START = "llm_stream_start"
    LLM_STREAM_CHUNK = "llm_stream_chunk"
    LLM_STREAM_END = "llm_stream_end"
    LLM_THINKING_STREAM = "llm_thinking_stream"
    LLM_CONTENT_STREAM = "llm_content_stream"

    @classmethod
    def is_tool_event(cls, event_type: str) -> bool:
        """Check if event type is tool-related."""
        return event_type in {cls.TOOL_START, cls.TOOL_PROGRESS, cls.TOOL_END}

    @classmethod
    def is_terminal_event(cls, event_type: str) -> bool:
        """Check if event type indicates termination."""
        return event_type in {cls.FINAL, cls.ERROR}

    @classmethod
    def is_stream_event(cls, event_type: str) -> bool:
        """Check if event type is a streaming event."""
        return event_type in {
            cls.LLM_STREAM_START,
            cls.LLM_STREAM_CHUNK,
            cls.LLM_STREAM_END,
            cls.LLM_THINKING_STREAM,
            cls.LLM_CONTENT_STREAM,
        }


class ActionType:
    """Constants for ReAct action types."""
    TOOL = "tool"
    FINAL = "final"
    ERROR = "error"
