"""JSON utility functions for extracting JSON from LLM responses."""
import json
import re
from typing import Any, Dict, Optional


class JsonExtractor:
    """Utility class for extracting JSON from LLM responses."""

    # Regex pattern for JSON code blocks
    JSON_BLOCK_PATTERN = r"```json\s*(\{.*?\})\s*```"

    @classmethod
    def extract_json(cls, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON payload from text using multiple strategies.

        Tries extraction in order:
        1. ```json ... ``` code blocks
        2. Top-level JSON object (text wrapped in braces)
        3. First balanced JSON object in text

        Args:
            text: The text to extract JSON from

        Returns:
            Parsed JSON dict, or None if no valid JSON found
        """
        # Strategy 1: Try ```json ... ``` code block
        json_block_match = re.search(cls.JSON_BLOCK_PATTERN, text, re.DOTALL)
        if json_block_match:
            candidate = json_block_match.group(1)
            result = cls.safe_json_load(candidate)
            if result is not None:
                return result

        # Strategy 2: Try text that starts and ends with braces
        candidate = text.strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            result = cls.safe_json_load(candidate)
            if result is not None:
                return result

        # Strategy 3: Try to find balanced JSON in text
        result = cls.find_balanced_json(text)
        if result:
            parsed = cls.safe_json_load(result)
            if parsed is not None:
                return parsed

        return None

    @classmethod
    def safe_json_load(cls, candidate: str) -> Optional[Dict[str, Any]]:
        """
        Safely parse JSON, returning None on failure.

        Args:
            candidate: String to parse as JSON

        Returns:
            Parsed dict if successful and result is a dict, None otherwise
        """
        try:
            payload = json.loads(candidate)
            return payload if isinstance(payload, dict) else None
        except (json.JSONDecodeError, ValueError, TypeError):
            return None

    @classmethod
    def find_balanced_json(cls, text: str) -> Optional[str]:
        """
        Find the first balanced JSON object in text.

        Args:
            text: Text to search for balanced JSON

        Returns:
            The balanced JSON string, or None if not found
        """
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


# Convenience function for backward compatibility
def extract_json_payload(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON payload from text.

    This is a convenience function that delegates to JsonExtractor.extract_json.
    """
    return JsonExtractor.extract_json(text)


def safe_json_load(candidate: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON, returning None on failure.

    This is a convenience function that delegates to JsonExtractor.safe_json_load.
    """
    return JsonExtractor.safe_json_load(candidate)
