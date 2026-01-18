"""
Screenplay scene module for Filmeto.

This module defines the ScreenPlayScene class representing a single scene in a screenplay.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class ScreenPlayScene:
    """Represents a single scene in a screenplay."""

    scene_id: str
    title: str
    content: str

    # Define meta attributes directly as class properties
    scene_number: str = ""
    location: str = ""
    time_of_day: str = ""
    genre: str = ""
    logline: str = ""
    characters: List[str] = field(default_factory=list)
    story_beat: str = ""
    page_count: int = 0
    duration_minutes: int = 0
    tags: List[str] = field(default_factory=list)
    status: str = "draft"  # draft, revised, final
    revision_number: int = 1
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        """Post-initialization processing if needed."""
        # No longer needed since attributes are defined directly
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert the scene to a dictionary representation."""
        return {
            "scene_id": self.scene_id,
            "title": self.title,
            "content": self.content,
            "scene_number": self.scene_number,
            "location": self.location,
            "time_of_day": self.time_of_day,
            "genre": self.genre,
            "logline": self.logline,
            "characters": self.characters,
            "story_beat": self.story_beat,
            "page_count": self.page_count,
            "duration_minutes": self.duration_minutes,
            "tags": self.tags,
            "status": self.status,
            "revision_number": self.revision_number,
            "created_at": self.created_at,
            "updated_at": self.updated_at
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