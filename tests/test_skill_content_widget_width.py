"""Test to verify the skill content widget width changes."""

import unittest
from unittest.mock import Mock
from PySide6.QtWidgets import QApplication
import sys

from app.ui.chat.message.skill_content_widget import SkillContentWidget
from agent.chat.agent_chat_message import StructureContent, ContentType


class TestSkillContentWidgetWidth(unittest.TestCase):
    """Test to verify the skill content widget width changes."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for testing."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def test_skill_content_widget_expands_horizontally(self):
        """Test that the skill content widget expands horizontally."""
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
        
        # Create the skill content widget
        widget = SkillContentWidget(structure_content)
        
        # Check that the container frame has expanding size policy
        from PySide6.QtWidgets import QSizePolicy
        self.assertEqual(
            widget.container_frame.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Expanding,
            "Container frame should have expanding horizontal policy"
        )

        # Check that the title label has expanding size policy
        self.assertEqual(
            widget.title_label.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Expanding,
            "Title label should have expanding horizontal policy"
        )

        # Check that the status label has expanding size policy
        self.assertEqual(
            widget.status_label.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Expanding,
            "Status label should have expanding horizontal policy"
        )

        # Check that the progress bar has expanding size policy
        self.assertEqual(
            widget.progress_bar.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Expanding,
            "Progress bar should have expanding horizontal policy"
        )
        
        print("✓ All size policies are correctly set to Expanding")
        
        # Clean up
        widget.deleteLater()


def run_tests():
    """Run the tests."""
    unittest.main()


if __name__ == '__main__':
    run_tests()