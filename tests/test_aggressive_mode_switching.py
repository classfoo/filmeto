"""
More aggressive test to reproduce the segfault issue when switching between startup and edit modes
"""

import os
import sys
from pathlib import Path
import time

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout
from PySide6.QtCore import QTimer
from app.data.workspace import Workspace
from app.ui.panels.actor.actor_panel import ActorPanel


class AggressiveTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aggressive Mode Switching Test")
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
        
        # Add actor panel to edit widget
        self.character_panel = ActorPanel(self.workspace, self.edit_widget)
        self.character_panel.setParent(self.edit_widget)
        
        edit_layout = QVBoxLayout(self.edit_widget)
        edit_layout.addWidget(self.character_panel)
        
        self.current_mode = "startup"  # startup or edit
        self.switch_count = 0
        self.max_switches = 50  # More switches to increase chance of triggering the issue
        self.switch_interval = 200  # Faster switching (200ms)
        
    def switch_mode(self):
        """Switch between startup and edit modes"""
        if self.current_mode == "startup":
            self.stacked_widget.setCurrentWidget(self.edit_widget)
            self.current_mode = "edit"
            print(f"Switched to edit mode (switch #{self.switch_count})")
            
            # Trigger some operations on the actor panel to increase background activity
            try:
                # This might trigger additional background operations
                self.character_panel.on_activated()
            except:
                pass
        else:
            self.stacked_widget.setCurrentWidget(self.startup_widget)
            self.current_mode = "startup"
            print(f"Switched to startup mode (switch #{self.switch_count})")
            
            try:
                # This might trigger deactivation and cleanup
                self.character_panel.on_deactivated()
            except:
                pass
        
        self.switch_count += 1
        
        if self.switch_count > self.max_switches:
            print("Aggressive test completed successfully without crash")
            QApplication.quit()


def test_aggressive_mode_switching():
    """Test aggressive switching between startup and edit modes"""
    print("Starting aggressive mode switching test...")
    print("This test will switch between startup and edit modes rapidly")
    print("It will also trigger panel activation/deactivation to increase background activity")
    print("If there's a segfault issue, it should occur during this test")
    
    app = QApplication([])
    
    main_window = AggressiveTestWindow()
    main_window.show()
    
    # Timer to switch modes rapidly
    switch_timer = QTimer()
    switch_timer.timeout.connect(main_window.switch_mode)
    switch_timer.start(main_window.switch_interval)  # Switch every 200ms
    
    print("Starting aggressive mode switching...")
    app.exec()


if __name__ == "__main__":
    test_aggressive_mode_switching()