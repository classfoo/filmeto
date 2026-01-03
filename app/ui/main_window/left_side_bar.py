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
        # buttons
        self.resource_button = QPushButton("\ue6b0", self)  # Play icon for resource
        self.resource_button.setFixedSize(30, 30)
        self.resource_button.clicked.connect(lambda: self.button_clicked.emit('resource'))
        self.layout.addWidget(self.resource_button, alignment=Qt.AlignCenter)

        self.model_button = QPushButton("\ue66e", self)  # Text2Img icon
        self.model_button.setFixedSize(30, 30)
        self.model_button.clicked.connect(lambda: self.button_clicked.emit('model'))
        self.layout.addWidget(self.model_button, alignment=Qt.AlignCenter)

        self.attach_button = QPushButton("\ue69d", self)  # Image edit icon
        self.attach_button.setFixedSize(30, 30)
        self.attach_button.clicked.connect(lambda: self.button_clicked.emit('attach'))
        self.layout.addWidget(self.attach_button, alignment=Qt.AlignCenter)

        self.layout.addStretch(0)
        self.timeline_button = QPushButton("\ue6b2", self)  # Image to video icon
        self.timeline_button.setFixedSize(30, 30)
        self.timeline_button.clicked.connect(lambda: self.button_clicked.emit('timeline'))
        self.layout.addWidget(self.timeline_button, alignment=Qt.AlignCenter)

        self.message_button = QPushButton("\ue707", self)  # Barrage icon for message
        self.message_button.setFixedSize(30, 30)
        self.message_button.clicked.connect(lambda: self.button_clicked.emit('message'))
        self.layout.addWidget(self.message_button, alignment=Qt.AlignCenter)

        self.video_button = QPushButton("\ue6de", self)  # Image to video icon
        self.video_button.setFixedSize(30, 30)
        self.video_button.clicked.connect(lambda: self.button_clicked.emit('video'))
        self.layout.addWidget(self.video_button, alignment=Qt.AlignCenter)

        self.camera_button = QPushButton("\ue6ce", self)  # Picture icon for camera
        self.camera_button.setFixedSize(30, 30)
        self.camera_button.clicked.connect(lambda: self.button_clicked.emit('camera'))
        self.layout.addWidget(self.camera_button, alignment=Qt.AlignCenter)

