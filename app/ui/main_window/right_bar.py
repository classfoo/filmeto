from PySide6.QtWidgets import QHBoxLayout, QPushButton

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget


class MainWindowRightBar(BaseWidget):

    def __init__(self, workspace: Workspace, parent):
        super(MainWindowRightBar, self).__init__(workspace)
        self.setObjectName("main_window_right_bar")
        self.parent = parent
        self.setFixedWidth(40)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setting_button = QPushButton("S", self)
        self.setting_button.setObjectName("main_window_bottom_bar_button")
        self.setting_button.setFixedSize(45, 30)
        self.layout.addWidget(self.setting_button)

