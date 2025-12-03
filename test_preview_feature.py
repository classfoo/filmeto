"""
Test script for timeline preview playback feature.

This script tests the basic functionality of the CanvasPreview widget
and preloading system.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from app.data.workspace import Workspace
from app.ui.canvas.canvas_preview import CanvasPreview, PreviewPreloader
from app.ui.canvas.canvas import CanvasWidget


def test_preloader():
    """Test the PreviewPreloader component."""
    print("Testing PreviewPreloader...")
    
    preloader = PreviewPreloader()
    
    # Test initial state
    assert preloader.preload_status == "idle", "Initial status should be idle"
    assert preloader.preloaded_item_index is None, "Initial item index should be None"
    
    # Test clear
    preloader.clear()
    assert preloader.preload_status == "idle", "Status should be idle after clear"
    
    print("✓ PreviewPreloader tests passed!")


def test_canvas_preview_creation():
    """Test CanvasPreview widget creation."""
    print("Testing CanvasPreview creation...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create a minimal workspace for testing
    workspace_path = os.path.expanduser("~/filmeto_workspace")
    if not os.path.exists(workspace_path):
        print(f"Workspace not found at {workspace_path}, skipping widget tests")
        return
    
    workspace = Workspace(workspace_path)
    
    # Create CanvasWidget
    canvas = CanvasWidget(workspace)
    
    # Check that preview overlay was created
    preview = canvas.get_preview_overlay()
    assert preview is not None, "Preview overlay should be created"
    assert isinstance(preview, CanvasPreview), "Preview should be CanvasPreview instance"
    
    # Check initial state
    assert not preview.isVisible(), "Preview should be initially hidden"
    assert preview._current_item_index is None, "Current item should be None initially"
    
    print("✓ CanvasPreview creation tests passed!")


def test_position_to_item_mapping():
    """Test the position-to-item mapping algorithm."""
    print("Testing position-to-item mapping...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create a minimal workspace for testing
    workspace_path = os.path.expanduser("~/filmeto_workspace")
    if not os.path.exists(workspace_path):
        print(f"Workspace not found at {workspace_path}, skipping mapping tests")
        return
    
    workspace = Workspace(workspace_path)
    project = workspace.get_project()
    
    if not project:
        print("No project loaded, skipping mapping tests")
        return
    
    # Create canvas and preview
    canvas = CanvasWidget(workspace)
    preview = canvas.get_preview_overlay()
    
    # Test position mapping
    # Assuming we have at least one timeline item
    timeline = project.get_timeline()
    if timeline and timeline.get_item_count() > 0:
        # Test position at start
        item_index, item_offset = preview._position_to_item(0.0)
        assert item_index == 1, "Position 0.0 should map to item 1"
        assert item_offset == 0.0, "Offset at start should be 0.0"
        
        # Test position in middle of first item
        item_duration = project.get_item_duration(1)
        mid_position = item_duration / 2.0
        item_index, item_offset = preview._position_to_item(mid_position)
        assert item_index == 1, "Position in middle should still be item 1"
        assert 0.0 < item_offset < item_duration, "Offset should be within item duration"
        
        print("✓ Position-to-item mapping tests passed!")
    else:
        print("No timeline items found, skipping mapping tests")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Timeline Preview Feature Tests")
    print("=" * 60)
    print()
    
    try:
        test_preloader()
        print()
        test_canvas_preview_creation()
        print()
        test_position_to_item_mapping()
        print()
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"Test failed: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
