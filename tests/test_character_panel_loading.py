"""
Test script to verify CharacterPanel loading behavior
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from app.data.workspace import Workspace
from app.ui.panels.character.character_panel import CharacterPanel


def test_character_panel_loading():
    """Test CharacterPanel loading behavior"""
    
    # Create Qt application
    app = QApplication([])
    
    workspace_path = os.path.join(project_root, "workspace")
    demo_project_name = "demo"
    
    # Initialize workspace 
    workspace = Workspace(workspace_path, demo_project_name, load_data=True, defer_heavy_init=False)
    
    print("Creating CharacterPanel...")
    
    # Create CharacterPanel
    panel = CharacterPanel(workspace)
    
    print(f"Panel _data_loaded: {panel._data_loaded}")
    print(f"Panel _is_active: {panel._is_active}")
    print(f"Panel character_manager: {panel.character_manager}")
    
    # Simulate activation
    print("\nSimulating panel activation...")
    panel.on_activated()
    
    print(f"After activation - _data_loaded: {panel._data_loaded}")
    print(f"After activation - _is_active: {panel._is_active}")
    print(f"After activation - character_manager: {panel.character_manager}")
    
    # Wait a bit for async operations to complete
    import time
    start_time = time.time()
    while time.time() - start_time < 2:  # Wait up to 2 seconds
        app.processEvents()
        time.sleep(0.1)
        if panel.character_manager is not None:
            print(f"Character manager loaded after activation: {panel.character_manager is not None}")
            break
    
    print(f"Final - character_manager: {panel.character_manager}")
    
    if panel.character_manager:
        print("Character manager successfully loaded!")
        # Try to list characters
        try:
            chars = panel.character_manager.list_characters()
            print(f"Number of characters loaded: {len(chars)}")
            for char in chars[:3]:  # Print first 3 characters
                print(f"  - {char.name}")
        except Exception as e:
            print(f"Error listing characters: {e}")
    else:
        print("Character manager is still None - loading failed!")


if __name__ == "__main__":
    test_character_panel_loading()