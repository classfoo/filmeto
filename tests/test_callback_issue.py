"""
Test to reproduce the issue where _on_character_manager_loaded is not triggered
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


def test_character_manager_loaded_callback():
    """Test to reproduce the issue where _on_character_manager_loaded is not triggered"""
    
    # Create Qt application
    app = QApplication([])
    
    workspace_path = os.path.join(project_root, "workspace")
    demo_project_name = "demo"
    
    print("Testing CharacterPanel _on_character_manager_loaded callback...")
    
    # Initialize workspace with load_data=True
    workspace = Workspace(workspace_path, demo_project_name, load_data=True, defer_heavy_init=False)
    
    print("Creating CharacterPanel...")
    
    # Create CharacterPanel
    panel = CharacterPanel(workspace)
    
    print(f"Initial state - _data_loaded: {panel._data_loaded}")
    print(f"Initial state - character_manager: {panel.character_manager}")
    
    # Store original callbacks to check if they're called
    original_on_finished = panel._on_character_manager_loaded
    original_on_error = panel._on_load_error
    
    # Track if callbacks are called
    finished_called = []
    error_called = []
    
    # Wrap the callbacks to track when they're called
    def wrapped_on_finished(character_manager):
        print("✓ _on_character_manager_loaded was called!")
        finished_called.append(True)
        original_on_finished(character_manager)
    
    def wrapped_on_error(error_msg, exception):
        print(f"✓ _on_load_error was called! Error: {error_msg}, Exception: {exception}")
        error_called.append(True)
        original_on_error(error_msg, exception)
    
    # Replace the callbacks temporarily
    panel._on_character_manager_loaded = wrapped_on_finished
    panel._on_load_error = wrapped_on_error
    
    print("\nCalling load_data() to trigger background loading...")
    panel.load_data()
    
    # Wait a bit for async operations to complete
    import time
    start_time = time.time()
    timeout = 5  # 5 seconds timeout
    
    print("Waiting for callbacks to be triggered...")
    while time.time() - start_time < timeout:
        app.processEvents()
        time.sleep(0.1)
        if finished_called or error_called:
            break
    
    print(f"\nResults:")
    print(f"_on_character_manager_loaded called: {bool(finished_called)}")
    print(f"_on_load_error called: {bool(error_called)}")
    print(f"Character manager loaded: {panel.character_manager is not None}")
    print(f"Data loaded: {panel._data_loaded}")
    
    if not finished_called and not error_called:
        print("❌ ISSUE REPRODUCED: Neither callback was triggered!")
        print("This confirms the issue where _on_character_manager_loaded is not being called.")
    else:
        print("✅ Callbacks were triggered as expected.")


if __name__ == "__main__":
    test_character_manager_loaded_callback()