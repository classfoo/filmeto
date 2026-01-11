#!/usr/bin/env python
"""Test script to check if the UI setup still works properly."""

import time
import sys
import os
from unittest.mock import Mock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ui_setup():
    """Test that UI setup still works after our changes."""
    print("Testing UI setup after changes...")
    
    # Import the module
    from app.ui.panels.agent.agent_panel import AgentPanel
    
    # Create a mock workspace since we can't create a real one easily
    mock_workspace = Mock()
    mock_workspace.get_project.return_value = None  # No project initially
    
    # Create the panel
    panel = AgentPanel(mock_workspace)
    
    # Time the UI setup
    start_time = time.time()
    panel.setup_ui()
    setup_time = (time.time() - start_time) * 1000
    
    print(f"UI setup completed in {setup_time:.2f}ms")
    
    # Check that the widgets were created
    print(f"Chat history widget created: {hasattr(panel, 'chat_history_widget')}")
    print(f"Prompt input widget created: {hasattr(panel, 'prompt_input_widget')}")
    
    if hasattr(panel, 'chat_history_widget'):
        print(f"Chat history widget type: {type(panel.chat_history_widget)}")
        
    if hasattr(panel, 'prompt_input_widget'):
        print(f"Prompt input widget type: {type(panel.prompt_input_widget)}")
    
    print("UI setup test completed successfully!")

if __name__ == "__main__":
    test_ui_setup()