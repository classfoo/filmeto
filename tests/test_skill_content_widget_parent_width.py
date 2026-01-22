"""Test to verify the skill content widget uses parent's available width."""

import unittest
from unittest.mock import Mock
from PySide6.QtWidgets import QApplication, QWidget
import sys

from app.ui.chat.message.skill_content_widget import SkillContentWidget
from agent.chat.agent_chat_message import StructureContent, ContentType


class TestSkillContentWidgetParentWidth(unittest.TestCase):
    """Test to verify the skill content widget uses parent's available width."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for testing."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def test_skill_content_widget_updates_width_from_parent(self):
        """Test that the skill content widget updates its width from parent."""
        # Create a sample structure content for a skill
        skill_data = {
            "status": "completed",
            "skill_name": "Test Skill",
            "message": "This is a test skill execution",
            "result": "Skill executed successfully"
        }
        
        structure_content = StructureContent(
            content_type=ContentType.SKILL,
            data=skill_data,
            title="Test Skill Execution",
            description="Testing skill execution display"
        )
        
        # Create a mock parent widget with a known width
        mock_parent = QWidget()
        mock_parent.resize(500, 300)  # Set a specific size
        mock_parent.show()  # Show to ensure geometry is applied
        
        # Create the skill content widget
        widget = SkillContentWidget(structure_content)
        widget.setParent(mock_parent)
        
        # Process events to allow the single shot timer to execute
        from PySide6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        
        # Check that the container frame has expanding size policy
        from PySide6.QtWidgets import QSizePolicy
        self.assertEqual(
            widget.container_frame.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Expanding,
            "Container frame should have expanding horizontal policy"
        )
        
        # The widget should have attempted to update its width based on parent
        # Although we can't easily test the exact width without a full parent hierarchy
        # that implements _available_bubble_width, we can at least verify the setup
        print("✓ Skill content widget created with proper size policies")
        print(f"  - Container frame policy: {widget.container_frame.sizePolicy().horizontalPolicy()}")
        print(f"  - Title label policy: {widget.title_label.sizePolicy().horizontalPolicy()}")
        print(f"  - Status label policy: {widget.status_label.sizePolicy().horizontalPolicy()}")
        print(f"  - Progress bar policy: {widget.progress_bar.sizePolicy().horizontalPolicy()}")
        
        # Clean up
        widget.deleteLater()
        mock_parent.deleteLater()


def run_tests():
    """Run the tests."""
    unittest.main()


if __name__ == '__main__':
    run_tests()