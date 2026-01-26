"""YAML format specification for React module."""
import re


class YamlFormatSpec:
    """
    YAML format specification for ReactAction responses.

    The LLM should respond in YAML format with 'thinking' as the first key.
    This enables streaming extraction of thinking content and stable multi-model adaptation.
    """

    # Format identifier
    FORMAT_NAME = "yaml"
    THINKING_KEY = "thinking"
    TYPE_KEY = "type"

    # YAML format templates
    TOOL_TEMPLATE = """thinking: |
  {thinking}
type: tool
tool_name: {tool_name}
tool_args:
  {args}
"""

    FINAL_TEMPLATE = """thinking: |
  {thinking}
type: final
final: {final}
"""

    ERROR_TEMPLATE = """thinking: |
  {thinking}
type: error
error: {error}
"""

    @classmethod
    def get_format_instructions(cls) -> str:
        """
        Get the format instructions for the LLM prompt.
        """
        return """Respond in YAML format with 'thinking' as the first field.

The response must follow this structure:
```yaml
thinking: |
  Your reasoning process here...
  Can be multiple lines.

type: tool|final|error
[additional fields based on type]
```

Tool action example:
```yaml
thinking: |
  I need to search for information about X.

type: tool
tool_name: search
tool_args:
  query: "search query"
```

Final action example:
```yaml
thinking: |
  I have completed the task. Here is the answer.

type: final
final: "The final answer here..."
```

Important notes:
- 'thinking' MUST be the first field
- Use | for multi-line thinking content
- type must be one of: tool, final, error
"""

    @classmethod
    def validate_yaml_structure(cls, text: str) -> bool:
        """
        Validate if the text looks like a valid YAML ReactAction response.

        Checks:
        1. Contains 'thinking:' as a top-level key (preferably first)
        2. Contains 'type:' key
        3. Has valid YAML structure

        Args:
            text: The text to validate

        Returns:
            True if looks like valid YAML format
        """
        # Remove leading whitespace and markdown code blocks
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Extract content from code block
            match = re.search(r"```(?:ya?ml)?\s*\n(.*?)\n```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
            else:
                # Try to find content after ```
                cleaned = cleaned.split("\n", 1)[-1].strip()

        # Check if it looks like YAML (has key: value pairs)
        if not re.search(r"^\w+\s*:", cleaned, re.MULTILINE):
            return False

        # Check for required keys
        has_thinking = bool(re.search(r"^\s*thinking\s*:", cleaned, re.MULTILINE))
        has_type = bool(re.search(r"^\s*type\s*:", cleaned, re.MULTILINE))

        return has_thinking and has_type

    @classmethod
    def is_likely_yaml(cls, text: str) -> bool:
        """
        Quick check if text is likely YAML format (vs JSON).

        Args:
            text: The text to check

        Returns:
            True if likely YAML format
        """
        cleaned = text.strip()

        # Check for YAML indicators (unquoted colons, pipe for multiline)
        yaml_indicators = [
            r"^\s*\w+\s*:\s*\|",  # Multiline string indicator
            r"^\s*thinking\s*:",   # thinking key (YAML style)
        ]

        # JSON starts with { or [
        if cleaned.startswith("{") or cleaned.startswith("["):
            # Could be JSON, check if it's actually YAML
            return cls.validate_yaml_structure(cleaned)

        # Check for YAML indicators
        for pattern in yaml_indicators:
            if re.search(pattern, cleaned, re.MULTILINE):
                return True

        return cls.validate_yaml_structure(cleaned)

    @classmethod
    def extract_yaml_block(cls, text: str) -> str:
        """
        Extract YAML content from text, handling markdown code blocks.

        Args:
            text: The text to extract YAML from

        Returns:
            Extracted YAML content
        """
        # Try to extract from ```yaml or ``` code blocks
        yaml_match = re.search(r"```(?:ya?ml)?\s*\n(.*?)\n```", text, re.DOTALL)
        if yaml_match:
            return yaml_match.group(1).strip()

        # Try to extract from first ``` to ```
        code_match = re.search(r"```\s*\n(.*?)\n```", text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # Return as-is if no code block found
        return text.strip()
