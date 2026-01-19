from PySide6.QtWidgets import QPushButton, QVBoxLayout
from PySide6.QtCore import Qt, Signal

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget


class MainWindowRightSideBar(BaseWidget):
    """Right sidebar with buttons for panel switching."""
    
    # Signal emitted when button is clicked (panel_name)
    button_clicked = Signal(str)

    def __init__(self, workspace: Workspace, parent):
        super(MainWindowRightSideBar, self).__init__(workspace)
        self.setObjectName("main_window_right_bar")
        self.parent = parent
        self.setFixedWidth(40)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 10, 0, 10)
        self.layout.setSpacing(20)
        
        # Map panel names to buttons for easy access
        self.button_map = {}
        
        # Agent button
        self.agent_button = QPushButton("\ue721", self)  # Agent icon
        self.agent_button.setFixedSize(30, 30)
        self.agent_button.setCheckable(True)  # Make button checkable
        self.agent_button.clicked.connect(lambda: self._on_button_clicked('agent'))
        self.layout.addWidget(self.agent_button, alignment=Qt.AlignCenter)
        self.button_map['agent'] = self.agent_button

        # Chat history button
        self.chat_history_button = QPushButton("\ue679", self)  # Chat history icon
        self.chat_history_button.setFixedSize(30, 30)
        self.chat_history_button.setCheckable(True)
        self.chat_history_button.clicked.connect(lambda: self._on_button_clicked('chat_history'))
        self.layout.addWidget(self.chat_history_button, alignment=Qt.AlignCenter)
        self.button_map['chat_history'] = self.chat_history_button

        # Skills button
        self.skills_button = QPushButton("\ue71f", self)  # Skills icon
        self.skills_button.setFixedSize(30, 30)
        self.skills_button.setCheckable(True)
        self.skills_button.clicked.connect(lambda: self._on_button_clicked('skills'))
        self.layout.addWidget(self.skills_button, alignment=Qt.AlignCenter)
        self.button_map['skills'] = self.skills_button

        # Soul Panel button
        self.souls_button = QPushButton("\ue7a1", self)  # Soul Panel icon
        self.souls_button.setFixedSize(30, 30)
        self.souls_button.setCheckable(True)
        self.souls_button.setToolTip("Soul Panel")  # Add tooltip for clarity
        self.souls_button.clicked.connect(lambda: self._on_button_clicked('souls'))
        self.layout.addWidget(self.souls_button, alignment=Qt.AlignCenter)
        self.button_map['souls'] = self.souls_button

        # Members button
        self.members_button = QPushButton("\ue89e", self)  # Members/users icon
        self.members_button.setFixedSize(30, 30)
        self.members_button.setCheckable(True)
        self.members_button.setToolTip("Members")  # Add tooltip for clarity
        self.members_button.clicked.connect(lambda: self._on_button_clicked('members'))
        self.layout.addWidget(self.members_button, alignment=Qt.AlignCenter)
        self.button_map['members'] = self.members_button

        # Screen Play button
        self.screenplay_button = QPushButton("\ue993", self)  # Text icon
        self.screenplay_button.setFixedSize(30, 30)
        self.screenplay_button.setCheckable(True)
        self.screenplay_button.setToolTip("Screen Play")  # Add tooltip for clarity
        self.screenplay_button.clicked.connect(lambda: self._on_button_clicked('screenplay'))
        self.layout.addWidget(self.screenplay_button, alignment=Qt.AlignCenter)
        self.button_map['screenplay'] = self.screenplay_button

        # Plan button
        self.plan_button = QPushButton("\ue8a5", self)  # Plan/Task icon
        self.plan_button.setFixedSize(30, 30)
        self.plan_button.setCheckable(True)
        self.plan_button.setToolTip("Plan Management")  # Add tooltip for clarity
        self.plan_button.clicked.connect(lambda: self._on_button_clicked('plan'))
        self.layout.addWidget(self.plan_button, alignment=Qt.AlignCenter)
        self.button_map['plan'] = self.plan_button

        self.layout.addStretch(0)

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

