"""Parser for converting LLM responses into ReactAction objects."""
from typing import Any, Dict, Optional

from .actions import ActionType, ReactAction, ToolAction, FinalAction, ErrorAction
from .constants import StopReason, ReactConfig
from .json_utils import JsonExtractor
from .todo import TodoPatch


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
    TODO_PATCH_ALIASES = ["todo_patch", "todo", "plan_update"]

    @classmethod
    def get_default_stop_reason(cls) -> str:
        """Get the default stop reason for final actions."""
        return StopReason.FINAL_ACTION.value

    @classmethod
    def get_max_steps_stop_reason(cls) -> str:
        """Get the stop reason when max steps is reached."""
        return StopReason.MAX_STEPS.value

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
        stop_reason: Optional[str] = None,
        todo_patch: Optional[TodoPatch] = None
    ) -> FinalAction:
        """Create a FinalAction with default values."""
        return FinalAction(
            final=final,
            thinking=thinking,
            stop_reason=stop_reason or StopReason.FINAL_ACTION.value,
            todo_patch=todo_patch
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
                stop_reason=StopReason.NO_JSON.value
            )

        action_type = cls._get_field(payload, cls.TYPE_ALIASES)

        # Parse todo_patch if present
        todo_patch = cls._parse_todo_patch(payload)

        if action_type == ActionType.TOOL.value:
            return cls._parse_tool_action(payload, todo_patch)
        elif action_type == ActionType.FINAL.value:
            return cls._parse_final_action(payload, response_text, todo_patch=todo_patch)
        else:
            # Unknown or missing action type, default to final
            return cls._parse_final_action(payload, response_text, stop_reason=StopReason.UNKNOWN_TYPE.value, todo_patch=todo_patch)

    @classmethod
    def _parse_tool_action(cls, payload: Dict[str, Any], todo_patch: Optional[TodoPatch] = None) -> ToolAction:
        """Parse a tool action from the payload."""
        tool_name = cls._get_field(payload, cls.TOOL_NAME_ALIASES, default="")
        tool_args = cls._get_field(payload, cls.TOOL_ARGS_ALIASES, default={})
        thinking = cls._get_field(payload, cls.THINKING_ALIASES)

        if not isinstance(tool_args, dict):
            tool_args = {}

        return ToolAction(
            tool_name=tool_name or "",
            tool_args=tool_args,
            thinking=thinking,
            todo_patch=todo_patch
        )

    @classmethod
    def _parse_final_action(
        cls,
        payload: Dict[str, Any],
        response_text: str,
        stop_reason: str = "final_action",
        todo_patch: Optional[TodoPatch] = None
    ) -> FinalAction:
        """Parse a final action from the payload."""
        final = cls._get_field(payload, cls.FINAL_ALIASES)
        thinking = cls._get_field(payload, cls.THINKING_ALIASES)

        if not final:
            final = response_text

        return FinalAction(
            final=final,
            thinking=thinking,
            stop_reason=stop_reason,
            todo_patch=todo_patch
        )

    @classmethod
    def _parse_todo_patch(cls, payload: Dict[str, Any]) -> Optional[TodoPatch]:
        """Parse a TODO patch from the payload."""
        todo_data = cls._get_field(payload, cls.TODO_PATCH_ALIASES)

        if not todo_data:
            return None

        # If it's already a TodoPatch, return it
        if isinstance(todo_data, TodoPatch):
            return todo_data

        # If it's a dict, try to parse it
        if isinstance(todo_data, dict):
            try:
                return TodoPatch.from_dict(todo_data)
            except (KeyError, ValueError):
                # Invalid patch format, ignore
                return None

        return None

    @classmethod
    def _get_field(cls, payload: Dict[str, Any], aliases: list, default: Any = None) -> Any:
        """Get a field value from payload using a list of possible aliases."""
        for alias in aliases:
            if alias in payload and payload[alias] is not None:
                return payload[alias]
        return default

    @classmethod
    def _extract_json_payload(cls, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON payload from text using JsonExtractor."""
        return JsonExtractor.extract_json(text)
