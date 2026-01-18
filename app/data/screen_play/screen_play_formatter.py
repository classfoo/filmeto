"""
Screenplay formatter module for Filmeto.

This module provides functionality to format screenplay content according to Hollywood standards.
"""

from typing import Dict, Any, List


class ScreenPlayFormatter:
    """Helper class for formatting screenplay content according to Hollywood standards."""

    @staticmethod
    def format_scene_content(
        scene_number: str,
        location: str,
        time_of_day: str,
        characters: List[str],
        scene_content: Dict[str, Any]
    ) -> str:
        """
        Format a complete scene according to Hollywood screenplay standards.

        Args:
            scene_number: Number of the scene
            location: Location of the scene
            time_of_day: Time of day for the scene
            characters: List of characters appearing in the scene
            scene_content: Dictionary containing scene elements

        Returns:
            Formatted screenplay content as a string
        """
        formatted_elements = []

        # Scene header
        scene_header = f"SCENE {scene_number}: {location} - {time_of_day.upper()}"
        formatted_elements.append(f"## {scene_header}")
        formatted_elements.append("")

        # Characters appearing in scene
        if characters:
            formatted_elements.append("**CHARACTERS PRESENT:**")
            formatted_elements.append(", ".join([char.upper() for char in characters]))
            formatted_elements.append("")

        # Scene elements
        for element_type, element_content in scene_content.items():
            if element_type == "scene_heading":
                formatted_elements.append(f"# {element_content.upper()}")
                formatted_elements.append("")
            elif element_type == "action":
                formatted_elements.append(element_content)
                formatted_elements.append("")
            elif element_type == "dialogue":
                for dialog_entry in element_content:
                    character = dialog_entry.get("character", "")
                    dialogue_text = dialog_entry.get("dialogue", "")
                    parenthetical = dialog_entry.get("parenthetical", "")

                    if character:
                        formatted_elements.append(f"**{character.upper()}**")
                    if parenthetical:
                        formatted_elements.append(f"*({parenthetical})*")
                    if dialogue_text:
                        formatted_elements.append(dialogue_text)
                    if character or parenthetical or dialogue_text:
                        formatted_elements.append("")
            elif element_type == "transition":
                formatted_elements.append(f"_{element_content}_")
                formatted_elements.append("")

        return "\n".join(formatted_elements).rstrip()