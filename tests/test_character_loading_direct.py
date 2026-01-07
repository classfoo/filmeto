"""
Test script to reproduce the character loading issue without involving Qt components
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add the parent directory to sys.path to make app module accessible
sys.path.insert(0, str(project_root))

from app.data.character import CharacterManager


def test_character_loading_issue():
    """Test the character loading issue directly with CharacterManager"""

    # Define the project path (same as in the demo)
    # Need to go up one level from tests directory to get to project root
    actual_project_root = project_root.parent if project_root.name == "tests" else project_root
    project_path = os.path.join(actual_project_root, "workspace", "demo")

    # Create a character manager instance
    char_manager = CharacterManager(project_path, resource_manager=None)

    print(f"Project path: {char_manager.project_path}")
    print(f"Characters dir: {char_manager.characters_dir}")
    print(f"Config path: {char_manager.config_path}")
    print(f"Config file exists: {os.path.exists(char_manager.config_path)}")
    print(f"Characters dir exists: {os.path.exists(char_manager.characters_dir)}")

    # Check if characters are loaded initially
    print(f"Characters initially loaded: {char_manager._loaded}")

    # List characters (this should trigger loading)
    characters = char_manager.list_characters()
    print(f"Number of characters loaded: {len(characters)}")
    print(f"Characters loaded after access: {char_manager._loaded}")

    # Print character names
    for char in characters:
        print(f"  - {char.name}")

    # Try to get a specific character
    char = char_manager.get_character("fuli")
    if char:
        print(f"Found character 'fuli': {char.name}")
        print(f"Character description: {char.description}")
    else:
        print("Character 'fuli' not found!")

    # Check if the character config was loaded properly
    print("\nTesting character creation after loading:")
    new_char = char_manager.create_character("test_char", "A test character")
    if new_char:
        print(f"Created new character: {new_char.name}")
    else:
        print("Failed to create new character")

    # List characters again to see if the new one was added
    characters_after = char_manager.list_characters()
    print(f"Number of characters after creation: {len(characters_after)}")


if __name__ == "__main__":
    test_character_loading_issue()