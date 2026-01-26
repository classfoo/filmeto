from abc import ABC, abstractmethod
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

    @classmethod
    def is_tool_event(cls, event_type: str) -> bool:
        """Check if event type is tool-related."""
        return event_type in {cls.TOOL_START, cls.TOOL_PROGRESS, cls.TOOL_END}

    @classmethod
    def is_terminal_event(cls, event_type: str) -> bool:
        """Check if event type indicates termination."""
        return event_type in {cls.FINAL, cls.ERROR}


class ActionType:
    """Constants for ReAct action types."""
    TOOL = "tool"
    FINAL = "final"
    ERROR = "error"


@dataclass(frozen=True)
class ReactAction(ABC):
    """
    Base class for ReAct actions. Immutable for safety.

    Each action represents a decision made by the LLM during the ReAct loop.
    """
    type: str

    @abstractmethod
    def get_thinking(self) -> Optional[str]:
        """Get the thinking/reasoning for this action."""
        pass

    def is_tool(self) -> bool:
        """Check if this is a tool action."""
        return self.type == ActionType.TOOL

    def is_final(self) -> bool:
        """Check if this is a final action."""
        return self.type == ActionType.FINAL

    def is_error(self) -> bool:
        """Check if this is an error action."""
        return self.type == ActionType.ERROR

    def get_status_for(self) -> str:
        """Get the React status associated with this action."""
        if self.is_tool():
            return ReactStatus.RUNNING
        elif self.is_final():
            return ReactStatus.FINAL
        elif self.is_error():
            return ReactStatus.FAILED
        return ReactStatus.RUNNING

    def to_event_payload(self, **kwargs) -> Dict[str, Any]:
        """Build event payload for this action. Subclasses can override."""
        payload = {"type": self.type}
        thinking = self.get_thinking()
        if thinking:
            payload["thinking"] = thinking
        payload.update(kwargs)
        return payload

    def get_summary(self) -> str:
        """Get a summary description of this action."""
        if self.is_final():
            return "ReAct process completed"
        elif self.is_error():
            return "ReAct process encountered an error"
        elif self.is_tool():
            return "Executing tool"
        return "Processing action"


@dataclass(frozen=True)
class ToolAction(ReactAction):
    """
    Action that invokes a tool/function.

    Attributes:
        tool_name: Name of the tool to invoke
        tool_args: Arguments to pass to the tool
        thinking: The agent's thinking process
    """
    type: str = ActionType.TOOL
    tool_name: str = ""
    tool_args: Dict[str, Any] = None
    thinking: Optional[str] = None

    def __post_init__(self):
        if self.tool_args is None:
            object.__setattr__(self, 'tool_args', {})

    def get_thinking(self) -> Optional[str]:
        return self.thinking

    def to_event_payload(self, **kwargs) -> Dict[str, Any]:
        """Build event payload for tool action."""
        payload = super().to_event_payload(**kwargs)
        payload.update({
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
        })
        return payload

    def get_summary(self) -> str:
        """Get summary for tool action."""
        if self.tool_name:
            return f"Executing tool: {self.tool_name}"
        return "Executing tool"

    def to_start_payload(self) -> Dict[str, Any]:
        """Build payload for tool start event."""
        return self.to_event_payload()

    def to_end_payload(self, result: Any = None, ok: bool = True, error: Optional[str] = None) -> Dict[str, Any]:
        """Build payload for tool end event."""
        payload = {
            "tool_name": self.tool_name,
            "ok": ok,
        }
        if ok and result is not None:
            payload["result"] = result
        if not ok and error:
            payload["error"] = error
        return payload

    def to_progress_payload(self, progress: Any) -> Dict[str, Any]:
        """Build payload for tool progress event."""
        return {
            "tool_name": self.tool_name,
            "progress": progress,
        }


@dataclass(frozen=True)
class FinalAction(ReactAction):
    """
    Action that completes the ReAct loop with a final response.

    Attributes:
        final: The final response content
        thinking: The agent's thinking process
        stop_reason: Reason for stopping (final_action, max_steps_reached, etc.)
    """
    type: str = ActionType.FINAL
    final: str = ""
    thinking: Optional[str] = None
    stop_reason: str = "final_action"

    def get_thinking(self) -> Optional[str]:
        return self.thinking

    def to_event_payload(self, **kwargs) -> Dict[str, Any]:
        """Build event payload for final action."""
        payload = super().to_event_payload(**kwargs)
        payload.update({
            "final_response": self.final,
            "stop_reason": self.stop_reason,
        })
        return payload

    def get_summary(self) -> str:
        """Get summary for final action."""
        if self.stop_reason == "max_steps_reached":
            return "ReAct process stopped after reaching maximum steps"
        elif self.stop_reason == "user_interrupted":
            return "ReAct process interrupted by user"
        return "ReAct process completed successfully"

    def to_final_payload(self, step: int = 0, max_steps: int = 0) -> Dict[str, Any]:
        """Build payload for final event."""
        return {
            "final_response": self.final,
            "stop_reason": self.stop_reason,
            "summary": self.get_summary(),
        }


@dataclass(frozen=True)
class ErrorAction(ReactAction):
    """
    Action representing an error during action parsing or execution.

    Attributes:
        error: Error message
        thinking: The agent's thinking process (if available)
        raw_response: The raw LLM response that caused the error
    """
    type: str = ActionType.ERROR
    error: str = ""
    thinking: Optional[str] = None
    raw_response: str = ""

    def get_thinking(self) -> Optional[str]:
        return self.thinking

    def to_event_payload(self, **kwargs) -> Dict[str, Any]:
        """Build event payload for error action."""
        payload = super().to_event_payload(**kwargs)
        payload.update({
            "error": self.error,
        })
        if self.raw_response:
            payload["raw_response"] = self.raw_response
        payload.update(kwargs)
        return payload

    def get_summary(self) -> str:
        """Get summary for error action."""
        return f"ReAct process encountered an error: {self.error}"

    def to_error_payload(self, details: Optional[str] = None) -> Dict[str, Any]:
        """Build payload for error event."""
        payload = {
            "error": self.error,
        }
        if details:
            payload["details"] = details
        elif self.raw_response:
            payload["details"] = self.raw_response[:500]  # Truncate if too long
        return payload


class ReactActionParser:
    """
    Parser for converting LLM responses into ReactAction objects.

    Handles multiple response formats and provides robust parsing with fallbacks.
    """

    # Aliases for different field names that might appear in LLM responses
    TYPE_ALIASES = ["type", "action"]
    TOOL_NAME_ALIASES = ["tool_name", "name", "tool"]
    TOOL_ARGS_ALIASES = ["tool_args", "arguments", "args", "input"]
    FINAL_ALIASES = ["final", "response", "answer", "output"]
    THINKING_ALIASES = ["thinking", "thought", "reasoning", "reasoning"]

    # Default stop reason constants
    STOP_REASON_FINAL_ACTION = "final_action"
    STOP_REASON_MAX_STEPS = "max_steps_reached"
    STOP_REASON_NO_JSON = "no_json_payload"
    STOP_REASON_UNKNOWN_TYPE = "unknown_action_type"
    STOP_REASON_USER_INTERRUPTED = "user_interrupted"

    @classmethod
    def get_default_stop_reason(cls) -> str:
        """Get the default stop reason for final actions."""
        return cls.STOP_REASON_FINAL_ACTION

    @classmethod
    def get_max_steps_stop_reason(cls) -> str:
        """Get the stop reason when max steps is reached."""
        return cls.STOP_REASON_MAX_STEPS

    @classmethod
    def get_error_summary(cls, error: Exception) -> str:
        """Get a standardized error summary from an exception."""
        error_type = type(error).__name__
        error_msg = str(error)
        if error_msg:
            return f"{error_type}: {error_msg}"
        return error_type

    @classmethod
    def get_thinking_message(cls, action: ReactAction, step: int, max_steps: int) -> str:
        """Get the thinking message for LLM thinking event."""
        thinking = action.get_thinking()
        if thinking:
            return thinking
        return f"Processing step {step}/{max_steps}"

    @classmethod
    def get_tool_result_payload(
        cls,
        tool_name: str,
        result: Any = None,
        ok: bool = True,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build standardized tool result payload."""
        payload = {
            "tool_name": tool_name,
            "ok": ok,
        }
        if ok and result is not None:
            payload["result"] = result
        if not ok and error:
            payload["error"] = error
        return payload

    @classmethod
    def create_final_action(
        cls,
        final: str,
        thinking: Optional[str] = None,
        stop_reason: Optional[str] = None
    ) -> FinalAction:
        """Create a FinalAction with default values."""
        return FinalAction(
            final=final,
            thinking=thinking,
            stop_reason=stop_reason or cls.STOP_REASON_FINAL_ACTION
        )

    @classmethod
    def parse(cls, response_text: str, payload: Optional[Dict[str, Any]] = None) -> ReactAction:
        """
        Parse an LLM response into a ReactAction.

        Args:
            response_text: The raw response text from the LLM
            payload: Optional pre-extracted JSON payload (will be extracted if not provided)

        Returns:
            A ReactAction subclass (ToolAction, FinalAction, or ErrorAction)
        """
        if payload is None:
            payload = cls._extract_json_payload(response_text)

        if not payload:
            # No valid JSON found, treat as final response
            return cls.create_final_action(
                final=response_text,
                thinking=None,
                stop_reason=cls.STOP_REASON_NO_JSON
            )

        action_type = cls._get_field(payload, cls.TYPE_ALIASES)

        if action_type == ActionType.TOOL:
            return cls._parse_tool_action(payload)
        elif action_type == ActionType.FINAL:
            return cls._parse_final_action(payload, response_text)
        else:
            # Unknown or missing action type, default to final
            return cls._parse_final_action(payload, response_text, stop_reason=cls.STOP_REASON_UNKNOWN_TYPE)

    @classmethod
    def _parse_tool_action(cls, payload: Dict[str, Any]) -> ToolAction:
        """Parse a tool action from the payload."""
        tool_name = cls._get_field(payload, cls.TOOL_NAME_ALIASES, default="")
        tool_args = cls._get_field(payload, cls.TOOL_ARGS_ALIASES, default={})
        thinking = cls._get_field(payload, cls.THINKING_ALIASES)

        if not isinstance(tool_args, dict):
            tool_args = {}

        return ToolAction(
            tool_name=tool_name or "",
            tool_args=tool_args,
            thinking=thinking
        )

    @classmethod
    def _parse_final_action(
        cls,
        payload: Dict[str, Any],
        response_text: str,
        stop_reason: str = "final_action"
    ) -> FinalAction:
        """Parse a final action from the payload."""
        final = cls._get_field(payload, cls.FINAL_ALIASES)
        thinking = cls._get_field(payload, cls.THINKING_ALIASES)

        if not final:
            final = response_text

        return FinalAction(
            final=final,
            thinking=thinking,
            stop_reason=stop_reason
        )

    @classmethod
    def _get_field(cls, payload: Dict[str, Any], aliases: list, default: Any = None) -> Any:
        """Get a field value from payload using a list of possible aliases."""
        for alias in aliases:
            if alias in payload and payload[alias] is not None:
                return payload[alias]
        return default

    @classmethod
    def _extract_json_payload(cls, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON payload from text.

        Looks for JSON in:
        1. ```json ... ``` code blocks
        2. Top-level JSON object
        3. First balanced JSON object in text
        """
        import json
        import re

        # Try ```json ... ``` code block
        json_block_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_block_match:
            candidate = json_block_match.group(1)
            result = cls._safe_json_load(candidate)
            if result is not None:
                return result

        # Try text that starts and ends with braces
        candidate = text.strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            result = cls._safe_json_load(candidate)
            if result is not None:
                return result

        # Try to find balanced JSON in text
        result = cls._find_balanced_json(text)
        if result:
            parsed = cls._safe_json_load(result)
            if parsed is not None:
                return parsed

        return None

    @classmethod
    def _safe_json_load(cls, candidate: str) -> Optional[Dict[str, Any]]:
        """Safely parse JSON, returning None on failure."""
        try:
            import json
            payload = json.loads(candidate)
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None

    @classmethod
    def _find_balanced_json(cls, text: str) -> Optional[str]:
        """Find the first balanced JSON object in text."""
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        for idx in range(start, len(text)):
            if text[idx] == "{":
                depth += 1
            elif text[idx] == "}":
                depth -= 1
                if depth == 0:
                    return text[start : idx + 1]
        return None
