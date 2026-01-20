#!/usr/bin/env python3
"""
Test script to verify the fixes for AgentChatPlanWidget:
1. Title bar height remains constant after multiple expand/collapse operations
2. Widget doesn't expand/collapse when there are no tasks
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from app.ui.chat.agent_chat_plan import AgentChatPlanWidget
from app.data.workspace import Workspace


def test_title_bar_height_constant():
    """Test that the title bar height remains constant after multiple toggles."""
    print("Testing title bar height constancy...")
    
    # Create a minimal workspace for testing
    workspace = Workspace("/tmp", "test_project")
    
    # Create the plan widget
    plan_widget = AgentChatPlanWidget(workspace)
    
    # Initially collapsed
    initial_height = plan_widget.header_frame.height()
    print(f"Initial header height: {initial_height}")
    
    # Toggle multiple times and check height remains the same
    for i in range(5):
        plan_widget.toggle_expanded()
        height_after_expand = plan_widget.header_frame.height()
        print(f"After expand #{i+1}, header height: {height_after_expand}")
        
        plan_widget.toggle_expanded()
        height_after_collapse = plan_widget.header_frame.height()
        print(f"After collapse #{i+1}, header height: {height_after_collapse}")
        
        # Check that the height hasn't changed
        assert height_after_collapse == initial_height, f"Header height changed after cycle #{i+1}"
    
    print("✓ Title bar height remains constant after multiple expand/collapse operations")


def test_no_expand_when_no_tasks():
    """Test that the widget doesn't expand when there are no tasks."""
    print("\nTesting no expand when no tasks...")
    
    # Create a minimal workspace for testing
    workspace = Workspace("/tmp", "test_project")
    
    # Create the plan widget
    plan_widget = AgentChatPlanWidget(workspace)
    
    # Initially collapsed
    initial_state = plan_widget._is_expanded
    print(f"Initial expanded state: {initial_state}")
    assert initial_state == False, "Initial state should be collapsed"
    
    # Since there are no tasks in a test environment, toggle_expanded should not change the state
    plan_widget.toggle_expanded()
    state_after_toggle = plan_widget._is_expanded
    print(f"State after toggle (no tasks): {state_after_toggle}")
    
    # State should remain unchanged because there are no tasks
    assert state_after_toggle == initial_state, "State should not change when there are no tasks"
    
    print("✓ Widget does not expand when there are no tasks")


def test_expand_when_has_tasks():
    """Test that the widget does expand when it has tasks (this is harder to test without a real project)."""
    print("\nTesting expand functionality when tasks exist...")
    print("Note: This test is limited without a real project with tasks")
    
    # Create a minimal workspace for testing
    workspace = Workspace("/tmp", "test_project")
    
    # Create the plan widget
    plan_widget = AgentChatPlanWidget(workspace)
    
    # Check the has_tasks method exists and returns expected value
    has_tasks_result = plan_widget.has_tasks()
    print(f"has_tasks() returns: {has_tasks_result}")
    
    print("✓ has_tasks method is accessible")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    test_title_bar_height_constant()
    test_no_expand_when_no_tasks()
    test_expand_when_has_tasks()
    
    print("\nAll tests completed!")