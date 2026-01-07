"""
Test to reproduce the segfault issue when switching between startup and edit modes
"""

import os
import sys
from pathlib import Path
import time
import threading

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget
from PySide6.QtCore import QTimer
from app.data.workspace import Workspace
from app.ui.panels.character.character_panel import CharacterPanel


class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Startup/Edit Mode Switching")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create stacked widget for mode switching
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create workspace
        workspace_path = os.path.join(Path(__file__).parent.parent, "workspace")
        self.workspace = Workspace(workspace_path, "demo", load_data=True, defer_heavy_init=False)
        
        # Create startup and edit mode widgets
        self.startup_widget = QWidget()
        self.edit_widget = QWidget()
        
        self.stacked_widget.addWidget(self.startup_widget)
        self.stacked_widget.addWidget(self.edit_widget)
        
        # Add character panel to edit widget
        self.character_panel = CharacterPanel(self.workspace, self.edit_widget)
        self.character_panel.setParent(self.edit_widget)
        
        from PySide6.QtWidgets import QVBoxLayout
        edit_layout = QVBoxLayout(self.edit_widget)
        edit_layout.addWidget(self.character_panel)
        
        self.current_mode = "startup"  # startup or edit
        self.switch_count = 0
        self.max_switches = 10  # Number of switches to test
        
    def switch_mode(self):
        """Switch between startup and edit modes"""
        if self.current_mode == "startup":
            self.stacked_widget.setCurrentWidget(self.edit_widget)
            self.current_mode = "edit"
            print(f"Switched to edit mode (switch #{self.switch_count})")
        else:
            self.stacked_widget.setCurrentWidget(self.startup_widget)
            self.current_mode = "startup"
            print(f"Switched to startup mode (switch #{self.switch_count})")
        
        self.switch_count += 1
        
        if self.switch_count > self.max_switches:
            print("Test completed successfully without crash")
            QApplication.quit()


def test_mode_switching():
    """Test frequent switching between startup and edit modes"""
    print("Starting mode switching test...")
    print("This test will switch between startup and edit modes multiple times")
    print("If there's a segfault issue, it should occur during this test")
    
    app = QApplication([])
    
    main_window = TestMainWindow()
    main_window.show()
    
    # Timer to switch modes
    switch_timer = QTimer()
    switch_timer.timeout.connect(main_window.switch_mode)
    switch_timer.start(500)  # Switch every 500ms
    
    print("Starting mode switching...")
    app.exec()


if __name__ == "__main__":
    test_mode_switching()