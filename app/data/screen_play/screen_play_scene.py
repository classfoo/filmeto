"""
Screenplay scene module for Filmeto.

This module defines the ScreenPlayScene class representing a single scene in a screenplay.
"""

from typing import Dict, Any


class ScreenPlayScene:
    """Represents a single scene in a screenplay."""

    def __init__(self, scene_id: str, title: str, content: str, metadata: Dict[str, Any]):
        self.scene_id = scene_id
        self.title = title
        self.content = content
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert the scene to a dictionary representation."""
        return {
            "scene_id": self.scene_id,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata
        }

    @staticmethod
    def format_hollywood_screenplay(
        scene_heading: str,
        action: str = "",
        character: str = "",
        dialogue: str = "",
        parenthetical: str = "",
        transition: str = ""
    ) -> str:
        """
        Format content according to Hollywood screenplay standards.

        Args:
            scene_heading: Scene heading (INT. or EXT. location - time of day)
            action: Action/description text
            character: Character name speaking
            dialogue: Dialogue spoken by character
            parenthetical: Direction for how dialogue is delivered
            transition: Transition between scenes

        Returns:
            Formatted screenplay content as a string
        """
        formatted_content = []

        # Scene heading (centered and in caps)
        if scene_heading:
            formatted_content.append(f"# {scene_heading.upper()}")
            formatted_content.append("")

        # Action/description
        if action:
            formatted_content.append(action)
            formatted_content.append("")

        # Character and dialogue
        if character and dialogue:
            formatted_content.append(f"**{character.upper()}**")
            if parenthetical:
                formatted_content.append(f"*{parenthetical}*")
            formatted_content.append(dialogue)
            formatted_content.append("")
        elif character:
            formatted_content.append(f"**{character.upper()}**")
            formatted_content.append("")

        # Transition
        if transition:
            formatted_content.append(f"_{transition}_")
            formatted_content.append("")

        return "\n".join(formatted_content).strip()