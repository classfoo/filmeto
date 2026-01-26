"""Parser for React module."""
from typing import Any, Dict, Optional

from .action import ReactAction, ToolAction, FinalAction, ErrorAction
from .constants import ActionType
from .yaml_spec import YamlFormatSpec


class ReactActionParser:
    """
    Parser for converting YAML-formatted LLM responses into ReactAction objects.

    Only supports YAML format with 'thinking' as the first key.
    """

    # Stop reason constants
    STOP_REASON_FINAL_ACTION = "final_action"
    STOP_REASON_MAX_STEPS = "max_steps_reached"
    STOP_REASON_PARSE_ERROR = "parse_error"
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
    def get_format_instructions(cls) -> str:
        """Get the YAML format instructions for the LLM prompt."""
        return YamlFormatSpec.get_format_instructions()

    @classmethod
    def parse(cls, response_text: str) -> ReactAction:
        """
        Parse a YAML-formatted LLM response into a ReactAction.

        Args:
            response_text: The raw response text from the LLM (YAML format)

        Returns:
            A ReactAction subclass (ToolAction, FinalAction, or ErrorAction)

        Raises:
            ValueError: If the response cannot be parsed as valid YAML
        """
        action = cls._parse_yaml(response_text)
        if action:
            return action

        # If YAML parsing failed, create an error action
        return ErrorAction(
            error="Failed to parse response as valid YAML action",
            thinking=None,
            raw_response=response_text[:500]
        )

    @classmethod
    def _parse_yaml(cls, response_text: str) -> Optional[ReactAction]:
        """
        Parse a YAML-formatted response into a ReactAction.

        YAML format should have 'thinking' as the first key:
        ```yaml
        thinking: |
          Reasoning here...
        type: tool|final|error
        ...
        ```

        Args:
            response_text: The raw response text

        Returns:
            A ReactAction subclass or None if parsing fails
        """
        try:
            import yaml

            # Extract YAML content (handle code blocks)
            yaml_content = YamlFormatSpec.extract_yaml_block(response_text)

            # Parse YAML
            data = yaml.safe_load(yaml_content)
            if not isinstance(data, dict):
                return None

            # Extract thinking (should be first key)
            thinking = data.get(YamlFormatSpec.THINKING_KEY)

            # Extract action type
            action_type = data.get(YamlFormatSpec.TYPE_KEY, "")

            # Parse based on action type
            if action_type == ActionType.TOOL:
                return ToolAction(
                    tool_name=data.get("tool_name", ""),
                    tool_args=data.get("tool_args", {}),
                    thinking=thinking
                )
            elif action_type == ActionType.FINAL:
                return FinalAction(
                    final=data.get("final", ""),
                    thinking=thinking,
                    stop_reason=data.get("stop_reason", cls.STOP_REASON_FINAL_ACTION)
                )
            elif action_type == ActionType.ERROR:
                return ErrorAction(
                    error=data.get("error", ""),
                    thinking=thinking,
                    raw_response=response_text
                )
            else:
                # Unknown type, treat as parse error
                return ErrorAction(
                    error=f"Unknown action type: {action_type}",
                    thinking=thinking,
                    raw_response=response_text[:500]
                )
        except Exception:
            # YAML parsing failed
            return None
