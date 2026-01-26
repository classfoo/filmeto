"""Parser for converting LLM responses into ReactAction objects."""
from typing import Any, Dict, Optional
import json
import re

from .actions import ActionType, ReactAction, ToolAction, FinalAction, ErrorAction


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
