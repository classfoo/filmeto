"""
Test file for EditorWidget component
Demonstrates usage and integration
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Slot

from app.ui.editor import EditorWidget
from app.data.workspace import Workspace


class TestEditorWindow(QMainWindow):
    """Test window for EditorWidget"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Editor Component Test")
        self.resize(1200, 800)
        
        # Create workspace
        import tempfile
        workspace_path = tempfile.gettempdir()
        self.workspace = Workspace(workspace_path, "test_editor_project")
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create editor widget
        self.editor = EditorWidget(self.workspace)
        layout.addWidget(self.editor)
        
        # Connect signals
        self._connect_signals()
        
        # Apply dark theme
        self._apply_theme()
    
    def _connect_signals(self):
        """Connect editor signals"""
        # Mode change
        self.editor.mode_changed.connect(self._on_mode_changed)
        
        # Prompt submission
        self.editor.prompt_submitted.connect(self._on_prompt_submitted)
    
    @Slot(str)
    def _on_mode_changed(self, mode: str):
        """Handle mode change"""
        print(f"Mode changed to: {mode}")
    
    @Slot(str, str)
    def _on_prompt_submitted(self, mode: str, prompt: str):
        """Handle prompt submission"""
        print(f"\n{'='*60}")
        print(f"Mode: {mode}")
        print(f"Prompt: {prompt}")
        print(f"{'='*60}\n")
        
        # Simulate processing
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.editor.set_processing(False))
    
    def _apply_theme(self):
        """Apply dark theme"""
        # Load stylesheet if exists
        style_path = os.path.join(
            os.path.dirname(__file__), '..', 'style', 'dark_style.qss'
        )
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        
        # Set window background
        self.setStyleSheet(self.styleSheet() + """
            QMainWindow {
                background-color: #1e1f22;
            }
        """)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show window
    window = TestEditorWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
