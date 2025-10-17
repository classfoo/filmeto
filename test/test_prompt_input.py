"""
Test file for Prompt Input Component
Demonstrates usage and verifies functionality
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt

from app.data.workspace import Workspace
from app.ui.prompt_input import PromptInputWidget


class TestWindow(QMainWindow):
    """Test window for Prompt Input Component"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prompt Input Component Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Create workspace
        workspace_path = "./workspace"
        project_name = "demo"
        self.workspace = Workspace(workspace_path, project_name)
        
        # Setup UI
        self._setup_ui()
        
        # Add some test templates
        self._add_test_templates()
    
    def _setup_ui(self):
        """Setup test UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Prompt Input Component Test")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #E1E1E1;")
        layout.addWidget(title)
        
        # Prompt Input Widget
        self.prompt_widget = PromptInputWidget(self.workspace)
        self.prompt_widget.prompt_submitted.connect(self._on_prompt_submitted)
        self.prompt_widget.prompt_changed.connect(self._on_prompt_changed)
        layout.addWidget(self.prompt_widget)
        
        # Status label
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Submitted prompt display
        self.submitted_label = QLabel("Last submitted: None")
        self.submitted_label.setStyleSheet("color: #E1E1E1; font-size: 14px; padding: 10px; background-color: #2b2d30; border-radius: 4px;")
        self.submitted_label.setWordWrap(True)
        layout.addWidget(self.submitted_label)
        
        # Clear button
        clear_button = QPushButton("Clear Input")
        clear_button.clicked.connect(self._on_clear_clicked)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3f4e;
                color: #E1E1E1;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4a4c5f;
            }
        """)
        layout.addWidget(clear_button)
        
        layout.addStretch()
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
            }
        """)
    
    def _add_test_templates(self):
        """Add some test templates"""
        prompt_manager = self.workspace.get_prompt_manager()
        
        test_templates = [
            ("textures/prompt_icons/text.png", "Generate a cinematic scene with dramatic lighting"),
            ("textures/prompt_icons/image.png", "Create a photorealistic portrait with soft focus"),
            ("textures/prompt_icons/video.png", "Produce a time-lapse of a sunset over mountains"),
            ("textures/prompt_icons/text.png", "Write a compelling story about adventure"),
            ("textures/prompt_icons/text.png", "Generate creative ideas for marketing campaign"),
        ]
        
        for icon, text in test_templates:
            prompt_manager.add_template(icon, text)
        
        print(f"Added {len(test_templates)} test templates")
    
    def _on_prompt_submitted(self, prompt: str):
        """Handle prompt submission"""
        self.status_label.setText(f"Status: Prompt submitted ({len(prompt)} characters)")
        self.submitted_label.setText(f"Last submitted: {prompt}")
        print(f"Prompt submitted: {prompt}")
        
        # Clear the input after submission
        self.prompt_widget.clear_prompt()
    
    def _on_prompt_changed(self, prompt: str):
        """Handle prompt change"""
        char_count = len(prompt)
        self.status_label.setText(f"Status: Editing ({char_count} characters)")
    
    def _on_clear_clicked(self):
        """Handle clear button click"""
        self.prompt_widget.clear_prompt()
        self.status_label.setText("Status: Input cleared")


def main():
    """Main test function"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
