from PySide6.QtWidgets import QHBoxLayout

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from app.ui.play_control import PlayControlWidget


class MainWindowBottomBar(BaseWidget):

    def __init__(self, workspace, parent):
        super(MainWindowBottomBar, self).__init__(workspace)
        self.setObjectName("main_window_bottom_bar")
        self.parent = parent
        self.setFixedHeight(28)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Add stretch to center the play control
        self.layout.addStretch()
        
        # Add play control widget (centered)
        self.play_control = PlayControlWidget(workspace, self)
        self.layout.addWidget(self.play_control)
        
        # Add stretch to center the play control
        self.layout.addStretch()
        
        # Connect signals (example - can be connected to actual playback logic later)
        self.play_control.previous_clicked.connect(self._on_previous_clicked)
        self.play_control.play_pause_clicked.connect(self._on_play_pause_clicked)
        self.play_control.next_clicked.connect(self._on_next_clicked)
    
    def _on_previous_clicked(self):
        """Handle previous segment button click."""
        # TODO: Implement navigation to previous segment
        print("Previous segment clicked")
    
    def _on_play_pause_clicked(self, is_playing: bool):
        """Handle play/pause button click."""
        print(f"Play/Pause clicked - Playing: {is_playing}")
    
    def _on_next_clicked(self):
        """Handle next segment button click."""
        # TODO: Implement navigation to next segment
        print("Next segment clicked")

