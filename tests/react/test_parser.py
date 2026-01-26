"""Unit tests for ReactActionParser."""
import pytest

from agent.react.parser import ReactActionParser
from agent.react.actions import ToolAction, FinalAction, ActionType
from agent.react.json_utils import JsonExtractor


class TestReactActionParser:
    """Test cases for ReactActionParser."""

    def test_parse_tool_action(self):
        """Test parsing a tool action from JSON."""
        response = '''```json
{
  "type": "tool",
  "thinking": "I need to search for information",
  "tool_name": "web_search",
  "tool_args": {"query": "test"}
}
```'''
        action = ReactActionParser.parse(response)
        assert isinstance(action, ToolAction)
        assert action.tool_name == "web_search"
        assert action.tool_args == {"query": "test"}
        assert action.thinking == "I need to search for information"

    def test_parse_final_action(self):
        """Test parsing a final action from JSON."""
        response = '{"type": "final", "thinking": "Task complete", "final": "Done"}'
        action = ReactActionParser.parse(response)
        assert isinstance(action, FinalAction)
        assert action.final == "Done"
        assert action.thinking == "Task complete"

    def test_parse_final_with_response_alias(self):
        """Test parsing final action with 'response' alias."""
        response = '{"type": "final", "response": "Complete"}'
        action = ReactActionParser.parse(response)
        assert isinstance(action, FinalAction)
        assert action.final == "Complete"

    def test_parse_no_json_treats_as_final(self):
        """Test that non-JSON text is treated as final response."""
        response = "This is just plain text, no JSON here"
        action = ReactActionParser.parse(response)
        assert isinstance(action, FinalAction)
        assert action.final == response

    def test_create_final_action_with_defaults(self):
        """Test creating a FinalAction with default stop reason."""
        action = ReactActionParser.create_final_action("Test response")
        assert action.final == "Test response"
        assert action.stop_reason == "final_action"

    def test_get_max_steps_stop_reason(self):
        """Test getting the max steps stop reason."""
        reason = ReactActionParser.get_max_steps_stop_reason()
        assert reason == "max_steps_reached"

    def test_get_default_stop_reason(self):
        """Test getting the default stop reason."""
        reason = ReactActionParser.get_default_stop_reason()
        assert reason == "final_action"


class TestJsonExtractor:
    """Test cases for JsonExtractor."""

    def test_extract_from_code_block(self):
        """Test extracting JSON from ```json code block."""
        text = '''```json
{"type": "tool", "tool_name": "test"}
```'''
        result = JsonExtractor.extract_json(text)
        assert result == {"type": "tool", "tool_name": "test"}

    def test_extract_from_braces(self):
        """Test extracting JSON from text wrapped in braces."""
        text = '{"type": "final", "final": "done"}'
        result = JsonExtractor.extract_json(text)
        assert result == {"type": "final", "final": "done"}

    def test_extract_from_mixed_text(self):
        """Test extracting JSON from text with other content."""
        text = 'Some text here {"type": "tool"} and more text'
        result = JsonExtractor.extract_json(text)
        assert result == {"type": "tool"}

    def test_safe_json_load_valid(self):
        """Test safe_json_load with valid JSON."""
        result = JsonExtractor.safe_json_load('{"key": "value"}')
        assert result == {"key": "value"}

    def test_safe_json_load_invalid(self):
        """Test safe_json_load with invalid JSON returns None."""
        result = JsonExtractor.safe_json_load('not json')
        assert result is None

    def test_safe_json_load_non_dict(self):
        """Test safe_json_load with JSON array returns None."""
        result = JsonExtractor.safe_json_load('["item1", "item2"]')
        assert result is None

    def test_find_balanced_json(self):
        """Test finding balanced JSON in text."""
        text = 'prefix {"inner": {"nested": true}} suffix'
        result = JsonExtractor.find_balanced_json(text)
        assert result == '{"inner": {"nested": true}}'

    def test_find_balanced_json_no_braces(self):
        """Test find_balanced_json returns None when no braces."""
        result = JsonExtractor.find_balanced_json("no braces here")
        assert result is None
