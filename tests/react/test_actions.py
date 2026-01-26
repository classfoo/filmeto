"""Unit tests for React action classes."""
import pytest

from agent.react.actions import ActionType, ReactAction, ToolAction, FinalAction, ErrorAction
from agent.react.status import ReactStatus


class TestActionType:
    """Test cases for ActionType enum."""

    def test_action_type_values(self):
        """Test that ActionType has correct values."""
        assert ActionType.TOOL.value == "tool"
        assert ActionType.FINAL.value == "final"
        assert ActionType.ERROR.value == "error"

    def test_action_type_is_string_enum(self):
        """Test that ActionType is a string Enum."""
        assert isinstance(ActionType.TOOL, str)
        assert ActionType.TOOL == "tool"  # String enum compares directly


class TestReactAction:
    """Test cases for ReactAction base class."""

    def test_tool_action_type_detection(self):
        """Test is_tool() method."""
        action = ToolAction(tool_name="test", tool_args={})
        assert action.is_tool()
        assert not action.is_final()
        assert not action.is_error()

    def test_final_action_type_detection(self):
        """Test is_final() method."""
        action = FinalAction(final="Done")
        assert action.is_final()
        assert not action.is_tool()
        assert not action.is_error()

    def test_error_action_type_detection(self):
        """Test is_error() method."""
        action = ErrorAction(error="Failed")
        assert action.is_error()
        assert not action.is_tool()
        assert not action.is_final()

    def test_get_status_for_tool(self):
        """Test get_status_for returns RUNNING for tool actions."""
        action = ToolAction(tool_name="test", tool_args={})
        assert action.get_status_for() == "RUNNING"

    def test_get_status_for_final(self):
        """Test get_status_for returns FINAL for final actions."""
        action = FinalAction(final="Done")
        assert action.get_status_for() == "FINAL"

    def test_get_status_for_error(self):
        """Test get_status_for returns FAILED for error actions."""
        action = ErrorAction(error="Failed")
        assert action.get_status_for() == "FAILED"


class TestToolAction:
    """Test cases for ToolAction."""

    def test_tool_action_defaults(self):
        """Test ToolAction default values."""
        action = ToolAction()
        assert action.tool_name == ""
        assert action.tool_args == {}
        assert action.thinking is None

    def test_tool_action_with_values(self):
        """Test ToolAction with provided values."""
        action = ToolAction(
            tool_name="search",
            tool_args={"query": "test"},
            thinking="I need to search"
        )
        assert action.tool_name == "search"
        assert action.tool_args == {"query": "test"}
        assert action.thinking == "I need to search"

    def test_tool_action_none_args_converts_to_empty_dict(self):
        """Test that None tool_args converts to empty dict."""
        action = ToolAction(tool_name="test", tool_args=None)
        assert action.tool_args == {}

    def test_tool_action_to_start_payload(self):
        """Test to_start_payload method."""
        action = ToolAction(tool_name="test", tool_args={"key": "value"})
        payload = action.to_start_payload()
        assert payload["type"] == "tool"
        assert payload["tool_name"] == "test"
        assert payload["tool_args"] == {"key": "value"}

    def test_tool_action_to_end_payload_success(self):
        """Test to_end_payload with successful result."""
        action = ToolAction(tool_name="test")
        payload = action.to_end_payload(result="Success", ok=True)
        assert payload["tool_name"] == "test"
        assert payload["ok"] is True
        assert payload["result"] == "Success"

    def test_tool_action_to_end_payload_error(self):
        """Test to_end_payload with error."""
        action = ToolAction(tool_name="test")
        payload = action.to_end_payload(ok=False, error="Failed")
        assert payload["ok"] is False
        assert payload["error"] == "Failed"

    def test_tool_action_to_progress_payload(self):
        """Test to_progress_payload method."""
        action = ToolAction(tool_name="test")
        payload = action.to_progress_payload(progress=50)
        assert payload["tool_name"] == "test"
        assert payload["progress"] == 50

    def test_tool_action_get_summary(self):
        """Test get_summary returns tool name."""
        action = ToolAction(tool_name="search")
        assert "search" in action.get_summary()

    def test_tool_action_get_summary_no_name(self):
        """Test get_summary when no tool name."""
        action = ToolAction()
        assert action.get_summary() == "Executing tool"


class TestFinalAction:
    """Test cases for FinalAction."""

    def test_final_action_defaults(self):
        """Test FinalAction default values."""
        action = FinalAction()
        assert action.final == ""
        assert action.thinking is None
        assert action.stop_reason == "final_action"

    def test_final_action_with_values(self):
        """Test FinalAction with provided values."""
        action = FinalAction(
            final="Task complete",
            thinking="All done",
            stop_reason="user_interrupted"
        )
        assert action.final == "Task complete"
        assert action.thinking == "All done"
        assert action.stop_reason == "user_interrupted"

    def test_final_action_to_final_payload(self):
        """Test to_final_payload method."""
        action = FinalAction(final="Done", stop_reason="final_action")
        payload = action.to_final_payload(step=5, max_steps=10)
        assert payload["final_response"] == "Done"
        assert payload["stop_reason"] == "final_action"
        assert "summary" in payload

    def test_final_action_get_summary_max_steps(self):
        """Test get_summary when max steps reached."""
        action = FinalAction(stop_reason="max_steps_reached")
        assert "maximum" in action.get_summary().lower()

    def test_final_action_get_summary_user_interrupted(self):
        """Test get_summary when user interrupted."""
        action = FinalAction(stop_reason="user_interrupted")
        assert "interrupted" in action.get_summary().lower()

    def test_final_action_get_summary_normal(self):
        """Test get_summary for normal completion."""
        action = FinalAction(stop_reason="final_action")
        assert "completed" in action.get_summary().lower()


class TestErrorAction:
    """Test cases for ErrorAction."""

    def test_error_action_defaults(self):
        """Test ErrorAction default values."""
        action = ErrorAction()
        assert action.error == ""
        assert action.thinking is None
        assert action.raw_response == ""

    def test_error_action_with_values(self):
        """Test ErrorAction with provided values."""
        action = ErrorAction(
            error="Something went wrong",
            thinking="I tried but failed",
            raw_response="invalid json"
        )
        assert action.error == "Something went wrong"
        assert action.thinking == "I tried but failed"
        assert action.raw_response == "invalid json"

    def test_error_action_to_error_payload(self):
        """Test to_error_payload method."""
        action = ErrorAction(error="Failed")
        payload = action.to_error_payload(details="More details")
        assert payload["error"] == "Failed"
        assert payload["details"] == "More details"

    def test_error_action_to_error_payload_raw_response(self):
        """Test to_error_payload uses raw_response if no details."""
        action = ErrorAction(
            error="Failed",
            raw_response="A" * 600  # Longer than 500
        )
        payload = action.to_error_payload()
        assert payload["error"] == "Failed"
        assert len(payload["details"]) == 500  # Truncated

    def test_error_action_get_summary(self):
        """Test get_summary includes error message."""
        action = ErrorAction(error="Test error")
        assert "Test error" in action.get_summary()
