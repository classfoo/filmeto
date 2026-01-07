"""
Test script to verify the character loading fix
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.data.workspace import Workspace


def test_character_loading_fix():
    """Test that the character loading fix works properly"""
    
    workspace_path = os.path.join(project_root, "workspace")
    demo_project_name = "demo"
    
    print("Testing workspace initialization with load_data=True...")
    
    # Initialize workspace with load_data=True (this should now load character data immediately)
    workspace = Workspace(workspace_path, demo_project_name, load_data=True, defer_heavy_init=False)
    
    # Get the character manager
    character_manager = workspace.get_project().get_character_manager()
    
    # Check if characters are loaded immediately
    print(f"Characters loaded flag: {character_manager._loaded}")
    
    # List characters
    characters = character_manager.list_characters()
    print(f"Number of characters loaded: {len(characters)}")
    
    # Print character names
    for char in characters:
        print(f"  - {char.name}")
    
    # Try to get a specific character
    char = character_manager.get_character("fuli")
    if char:
        print(f"Found character 'fuli': {char.name}")
    else:
        print("Character 'fuli' not found!")
    
    print("\n" + "="*50)
    print("Testing workspace initialization with load_data=False...")
    
    # Initialize workspace with load_data=False (as in the original App.py)
    workspace2 = Workspace(workspace_path, demo_project_name, load_data=False, defer_heavy_init=True)
    
    # Get the character manager
    character_manager2 = workspace2.get_project().get_character_manager()
    
    # Check if characters are loaded initially
    print(f"Characters loaded flag initially: {character_manager2._loaded}")
    
    # List characters (this should trigger loading)
    characters2 = character_manager2.list_characters()
    print(f"Number of characters loaded after access: {len(characters2)}")
    print(f"Characters loaded flag after access: {character_manager2._loaded}")
    
    # Try to get a specific character
    char2 = character_manager2.get_character("wegweg")
    if char2:
        print(f"Found character 'wegweg': {char2.name}")
    else:
        print("Character 'wegweg' not found!")
    
    print("\n✅ Character loading fix test completed!")


if __name__ == "__main__":
    test_character_loading_fix()