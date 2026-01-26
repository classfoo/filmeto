"""Unit tests for React events and enums."""
import pytest

from agent.react.event import ReactEvent, ReactEventType
from agent.react.status import ReactStatus
from agent.react.actions import ActionType


class TestReactEventType:
    """Test cases for ReactEventType enum."""

    def test_event_type_values(self):
        """Test that ReactEventType has correct values."""
        assert ReactEventType.LLM_THINKING.value == "llm_thinking"
        assert ReactEventType.TOOL_START.value == "tool_start"
        assert ReactEventType.TOOL_PROGRESS.value == "tool_progress"
        assert ReactEventType.TOOL_END.value == "tool_end"
        assert ReactEventType.LLM_OUTPUT.value == "llm_output"
        assert ReactEventType.FINAL.value == "final"
        assert ReactEventType.ERROR.value == "error"

    def test_event_type_is_string_enum(self):
        """Test that ReactEventType is a string Enum."""
        assert isinstance(ReactEventType.LLM_THINKING, str)
        assert ReactEventType.LLM_THINKING == "llm_thinking"  # String enum compares directly

    def test_is_tool_event(self):
        """Test is_tool_event class method."""
        assert ReactEventType.is_tool_event("tool_start")
        assert ReactEventType.is_tool_event("tool_progress")
        assert ReactEventType.is_tool_event("tool_end")
        assert not ReactEventType.is_tool_event("llm_thinking")
        assert not ReactEventType.is_tool_event("final")

    def test_is_terminal_event(self):
        """Test is_terminal_event class method."""
        assert ReactEventType.is_terminal_event("final")
        assert ReactEventType.is_terminal_event("error")
        assert not ReactEventType.is_terminal_event("tool_start")
        assert not ReactEventType.is_terminal_event("llm_thinking")

    def test_get_valid_types(self):
        """Test get_valid_types returns all event type values."""
        valid_types = ReactEventType.get_valid_types()
        assert "llm_thinking" in valid_types
        assert "tool_start" in valid_types
        assert "final" in valid_types
        assert len(valid_types) > 0


class TestReactStatus:
    """Test cases for ReactStatus enum."""

    def test_status_values(self):
        """Test that ReactStatus has correct values."""
        assert ReactStatus.IDLE.value == "IDLE"
        assert ReactStatus.RUNNING.value == "RUNNING"
        assert ReactStatus.FINAL.value == "FINAL"
        assert ReactStatus.FAILED.value == "FAILED"
        assert ReactStatus.WAITING.value == "WAITING"
        assert ReactStatus.PAUSED.value == "PAUSED"
        assert ReactStatus.AWAITING_INPUT.value == "AWAITING_INPUT"

    def test_status_is_string_enum(self):
        """Test that ReactStatus is a string Enum."""
        assert isinstance(ReactStatus.RUNNING, str)
        assert ReactStatus.RUNNING == "RUNNING"  # String enum compares directly

    def test_is_active(self):
        """Test is_active class method."""
        assert ReactStatus.is_active("RUNNING")
        assert ReactStatus.is_active("WAITING")
        assert not ReactStatus.is_active("IDLE")
        assert not ReactStatus.is_active("FINAL")

    def test_is_terminal(self):
        """Test is_terminal class method."""
        assert ReactStatus.is_terminal("FINAL")
        assert ReactStatus.is_terminal("FAILED")
        assert not ReactStatus.is_terminal("RUNNING")
        assert not ReactStatus.is_terminal("IDLE")

    def test_is_interactive(self):
        """Test is_interactive class method."""
        assert ReactStatus.is_interactive("PAUSED")
        assert ReactStatus.is_interactive("AWAITING_INPUT")
        assert not ReactStatus.is_interactive("RUNNING")
        assert not ReactStatus.is_interactive("IDLE")


class TestReactEvent:
    """Test cases for ReactEvent dataclass."""

    def test_create_valid_event(self):
        """Test creating a valid ReactEvent."""
        event = ReactEvent(
            event_type="llm_thinking",
            project_name="test_project",
            react_type="test_type",
            run_id="run_123",
            step_id=1,
            payload={"message": "thinking..."}
        )
        assert event.event_type == "llm_thinking"
        assert event.project_name == "test_project"

    def test_event_validation_invalid_type(self):
        """Test that invalid event_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid event_type"):
            ReactEvent(
                event_type="invalid_type",
                project_name="test",
                react_type="test",
                run_id="run_123",
                step_id=0,
                payload={}
            )

    def test_event_validation_negative_step_id(self):
        """Test that negative step_id raises ValueError."""
        with pytest.raises(ValueError, match="step_id must be >= 0"):
            ReactEvent(
                event_type="llm_thinking",
                project_name="test",
                react_type="test",
                run_id="run_123",
                step_id=-1,
                payload={}
            )

    def test_event_validation_invalid_payload(self):
        """Test that non-dict payload raises ValueError."""
        with pytest.raises(ValueError, match="payload must be a dict"):
            ReactEvent(
                event_type="llm_thinking",
                project_name="test",
                react_type="test",
                run_id="run_123",
                step_id=0,
                payload="not a dict"  # type: ignore
            )

    def test_event_validation_zero_step_id(self):
        """Test that zero step_id is valid."""
        event = ReactEvent(
            event_type="llm_thinking",
            project_name="test",
            react_type="test",
            run_id="run_123",
            step_id=0,
            payload={}
        )
        assert event.step_id == 0

    def test_event_validation_empty_payload(self):
        """Test that empty dict payload is valid."""
        event = ReactEvent(
            event_type="llm_thinking",
            project_name="test",
            react_type="test",
            run_id="run_123",
            step_id=0,
            payload={}
        )
        assert event.payload == {}
