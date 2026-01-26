"""YAML stream parser for React module."""
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional


class YamlStreamParser:
    """
    Streaming YAML parser for ReactAction responses.

    Extracts thinking content in real-time from YAML streams where 'thinking' is the first key.
    Handles incremental parsing and provides both raw chunks and parsed structure.
    """

    def __init__(self):
        """Initialize the YAML stream parser."""
        self.buffer = ""
        self.thinking_buffer = ""
        self.action_buffer = ""
        self._full_content = ""
        self._state = "seeking_thinking"  # seeking_thinking, in_thinking, post_thinking, complete
        self._thinking_indent = 0
        self._yaml_data = {}

    def feed(self, chunk: str) -> "YamlStreamParser.ParseResult":
        """
        Feed a chunk of text to the parser.

        Args:
            chunk: A chunk of text from the LLM stream

        Returns:
            ParseResult containing extracted thinking/content
        """
        result = self.ParseResult()
        self.buffer += chunk
        self._full_content += chunk

        # Process buffer line by line
        while self.buffer:
            if self._state == "seeking_thinking":
                result = self._process_seeking_thinking(result)
            elif self._state == "in_thinking":
                result = self._process_in_thinking(result)
            elif self._state == "post_thinking":
                result = self._process_post_thinking(result)
            else:  # complete
                # Just accumulate content
                self.action_buffer += self.buffer
                result.content_delta = self.buffer
                result.action_complete = True
                self.buffer = ""
                break

            if not self.buffer:
                break

        return result

    def _process_seeking_thinking(self, result: "YamlStreamParser.ParseResult") -> "YamlStreamParser.ParseResult":
        """Process buffer while looking for the 'thinking:' key."""
        # Find the thinking key
        lines = self.buffer.split("\n", 1)
        if len(lines) == 1:
            # No newline yet, keep waiting
            return result

        first_line, rest = lines
        self.buffer = rest

        # Check if this line contains 'thinking:'
        if self._is_thinking_key_line(first_line):
            self._state = "in_thinking"
            # Check if it uses | for multiline
            if "|" in first_line:
                self._thinking_indent = len(first_line) - len(first_line.lstrip())
            else:
                # Single line thinking
                match = re.search(r"thinking:\s*(.+)", first_line)
                if match:
                    thinking_content = match.group(1).strip()
                    if thinking_content:
                        self.thinking_buffer += thinking_content
                        result.thinking_delta = thinking_content
                        result.thinking_complete = True
                self._state = "post_thinking"
        else:
            # Not a thinking line, might be content before or after
            self.action_buffer += first_line + "\n"

        return result

    def _process_in_thinking(self, result: "YamlStreamParser.ParseResult") -> "YamlStreamParser.ParseResult":
        """Process buffer while inside the thinking block."""
        lines = self.buffer.split("\n", 1)
        if len(lines) == 1:
            # No newline yet, add to thinking buffer (partial line)
            self.thinking_buffer += self.buffer
            result.thinking_delta = self.buffer
            self.buffer = ""
            return result

        line, rest = lines
        self.buffer = rest

        # Check if we're still in the thinking block
        line_stripped = line.rstrip()
        if not line_stripped:
            # Empty line, add to thinking
            self.thinking_buffer += "\n"
            result.thinking_delta = "\n"
            return result

        current_indent = len(line) - len(line.lstrip())

        # Check if this line is dedented (end of thinking block)
        if current_indent <= self._thinking_indent and line_stripped:
            # End of thinking block
            self._state = "post_thinking"
            result.thinking_complete = True
            # Put this line back for post_thinking processing
            self.buffer = line + "\n" + self.buffer
        else:
            # Still in thinking block
            self.thinking_buffer += line + "\n"
            result.thinking_delta = line + "\n"

        return result

    def _process_post_thinking(self, result: "YamlStreamParser.ParseResult") -> "YamlStreamParser.ParseResult":
        """Process buffer after thinking block."""
        # Everything after thinking is action data
        self.action_buffer += self.buffer
        result.content_delta = self.buffer

        # Try to parse the action
        try:
            action_data = self._parse_yaml_action(self.action_buffer)
            if action_data:
                self._yaml_data = action_data
                result.action_complete = True
                result.action_data = action_data
                self._state = "complete"
        except Exception:
            # Not yet complete, continue accumulating
            pass

        self.buffer = ""
        return result

    def _is_thinking_key_line(self, line: str) -> bool:
        """Check if a line is the 'thinking:' key line."""
        return bool(re.match(r"^\s*thinking\s*:\s*\|?", line.strip()))

    def _parse_yaml_action(self, yaml_text: str) -> Optional[Dict[str, Any]]:
        """Parse YAML action text."""
        try:
            import yaml
            data = yaml.safe_load(yaml_text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return None

    def finalize(self) -> "YamlStreamParser.ParseResult":
        """Finalize parsing and return any remaining content."""
        result = self.ParseResult()

        if self._state == "in_thinking":
            # Unclosed thinking block
            self.thinking_buffer += self.buffer
            result.thinking_delta = self.buffer
            result.thinking_complete = True
            self._state = "complete"
        elif self._state == "post_thinking" or self._state == "seeking_thinking":
            self.action_buffer += self.buffer
            result.content_delta = self.buffer

            # Try one more time to parse
            try:
                action_data = self._parse_yaml_action(self.action_buffer)
                if action_data:
                    self._yaml_data = action_data
                    result.action_complete = True
                    result.action_data = action_data
            except Exception:
                pass

        self.buffer = ""
        return result

    def get_thinking(self) -> str:
        """Get the accumulated thinking content."""
        return self.thinking_buffer

    def get_action_data(self) -> Dict[str, Any]:
        """Get the parsed action data."""
        return self._yaml_data

    def get_full_content(self) -> str:
        """Get the full content accumulated so far."""
        return self._full_content

    def is_complete(self) -> bool:
        """Check if parsing is complete."""
        return self._state == "complete" and bool(self._yaml_data)

    @dataclass
    class ParseResult:
        """Result of parsing a YAML stream chunk."""
        thinking_delta: str = ""
        content_delta: str = ""
        thinking_complete: bool = False
        action_complete: bool = False
        action_data: Optional[Dict[str, Any]] = None

        def has_thinking(self) -> bool:
            return bool(self.thinking_delta)

        def has_content(self) -> bool:
            return bool(self.content_delta)
