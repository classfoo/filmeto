from PySide6.QtWidgets import QPushButton, QVBoxLayout
from PySide6.QtCore import Qt, Signal

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget


class MainWindowLeftSideBar(BaseWidget):
    """Left sidebar with buttons for panel switching."""
    
    # Signal emitted when button is clicked (panel_name)
    button_clicked = Signal(str)

    def __init__(self, workspace, parent):
        super(MainWindowLeftSideBar, self).__init__(workspace)
        self.setObjectName("main_window_left_bar")
        self.parent = parent
        self.setFixedWidth(40)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        # Map panel names to buttons for easy access
        self.button_map = {}
        
        # Character button (at the top)
        self.character_button = QPushButton("\ue60c", self)  # Character icon (role1)
        self.character_button.setFixedSize(30, 30)
        self.character_button.setCheckable(True)  # Make button checkable
        self.character_button.clicked.connect(lambda: self._on_button_clicked('character'))
        self.layout.addWidget(self.character_button, alignment=Qt.AlignCenter)
        self.button_map['character'] = self.character_button
        
        # buttons
        self.resource_button = QPushButton("\ue6b0", self)  # Play icon for resource
        self.resource_button.setFixedSize(30, 30)
        self.resource_button.setCheckable(True)  # Make button checkable
        self.resource_button.clicked.connect(lambda: self._on_button_clicked('resource'))
        self.layout.addWidget(self.resource_button, alignment=Qt.AlignCenter)
        self.button_map['resource'] = self.resource_button

        self.model_button = QPushButton("\ue66e", self)  # Text2Img icon
        self.model_button.setFixedSize(30, 30)
        self.model_button.setCheckable(True)
        self.model_button.clicked.connect(lambda: self._on_button_clicked('model'))
        self.layout.addWidget(self.model_button, alignment=Qt.AlignCenter)
        self.button_map['model'] = self.model_button

        self.attach_button = QPushButton("\ue69d", self)  # Image edit icon
        self.attach_button.setFixedSize(30, 30)
        self.attach_button.setCheckable(True)
        self.attach_button.clicked.connect(lambda: self._on_button_clicked('attach'))
        self.layout.addWidget(self.attach_button, alignment=Qt.AlignCenter)
        self.button_map['attach'] = self.attach_button

        self.layout.addStretch(0)
        self.timeline_button = QPushButton("\ue6b2", self)  # Image to video icon
        self.timeline_button.setFixedSize(30, 30)
        self.timeline_button.setCheckable(True)
        self.timeline_button.clicked.connect(lambda: self._on_button_clicked('timeline'))
        self.layout.addWidget(self.timeline_button, alignment=Qt.AlignCenter)
        self.button_map['timeline'] = self.timeline_button

        self.message_button = QPushButton("\ue707", self)  # Barrage icon for message
        self.message_button.setFixedSize(30, 30)
        self.message_button.setCheckable(True)
        self.message_button.clicked.connect(lambda: self._on_button_clicked('message'))
        self.layout.addWidget(self.message_button, alignment=Qt.AlignCenter)
        self.button_map['message'] = self.message_button

        self.video_button = QPushButton("\ue6de", self)  # Image to video icon
        self.video_button.setFixedSize(30, 30)
        self.video_button.setCheckable(True)
        self.video_button.clicked.connect(lambda: self._on_button_clicked('video'))
        self.layout.addWidget(self.video_button, alignment=Qt.AlignCenter)
        self.button_map['video'] = self.video_button

        self.camera_button = QPushButton("\ue6ce", self)  # Picture icon for camera
        self.camera_button.setFixedSize(30, 30)
        self.camera_button.setCheckable(True)
        self.camera_button.clicked.connect(lambda: self._on_button_clicked('camera'))
        self.layout.addWidget(self.camera_button, alignment=Qt.AlignCenter)
        self.button_map['camera'] = self.camera_button
        
        # Track current selected button
        self.current_selected_button = None
    
    def _on_button_clicked(self, panel_name: str):
        """Handle button click and update selected state."""
        # Set the clicked button as checked
        self.set_selected_button(panel_name)
        # Emit signal for panel switching
        self.button_clicked.emit(panel_name)
    
    def set_selected_button(self, panel_name: str):
        """
        Set the selected button state.
        
        Args:
            panel_name: Name of the panel to select
        """
        # Uncheck previous button if exists
        if self.current_selected_button:
            self.current_selected_button.setChecked(False)
        
        # Check the new button
        if panel_name in self.button_map:
            button = self.button_map[panel_name]
            button.setChecked(True)
            self.current_selected_button = button

