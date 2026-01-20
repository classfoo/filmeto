#!/usr/bin/env python3
"""
Test script to verify the fixed height functionality of AgentChatPlanWidget.
This script creates an instance of the widget and verifies that the fixed height properties are set correctly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from app.ui.chat.agent_chat_plan import AgentChatPlanWidget
from app.data.workspace import Workspace


def test_fixed_heights():
    """Test that the fixed height properties are correctly set."""
    print("Testing AgentChatPlanWidget fixed heights...")
    
    # Create a minimal workspace for testing
    workspace = Workspace("/tmp", "test_project")
    
    # Create the plan widget
    plan_widget = AgentChatPlanWidget(workspace)
    
    # Check that the fixed height properties exist and have correct values
    assert hasattr(plan_widget, '_collapsed_height'), "Missing _collapsed_height property"
    assert hasattr(plan_widget, '_expanded_height'), "Missing _expanded_height property"
    
    print(f"_collapsed_height: {plan_widget._collapsed_height}")
    print(f"_expanded_height: {plan_widget._expanded_height}")
    
    # Verify the values are reasonable
    assert plan_widget._collapsed_height == 40, f"Expected _collapsed_height to be 40, got {plan_widget._collapsed_height}"
    assert plan_widget._expanded_height == 260, f"Expected _expanded_height to be 260, got {plan_widget._expanded_height}"
    
    print("✓ Fixed height properties are correctly set")
    
    # Test initial state
    print(f"Initial _is_expanded state: {plan_widget._is_expanded}")
    assert plan_widget._is_expanded == False, "Initial state should be collapsed"
    
    # Test toggle functionality
    plan_widget.toggle_expanded()
    print(f"After first toggle, _is_expanded state: {plan_widget._is_expanded}")
    assert plan_widget._is_expanded == True, "State should be expanded after first toggle"
    
    plan_widget.toggle_expanded()
    print(f"After second toggle, _is_expanded state: {plan_widget._is_expanded}")
    assert plan_widget._is_expanded == False, "State should be collapsed after second toggle"
    
    print("✓ Toggle functionality works correctly")
    
    print("\nAll tests passed! The fixed height functionality is working as expected.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_fixed_heights()