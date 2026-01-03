from PySide6.QtWidgets import QHBoxLayout

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from .left_side_bar import MainWindowLeftSideBar
from .right_side_bar import MainWindowRightSideBar
from .workspace import MainWindowWorkspace


class MainWindowHLayout(BaseWidget):

    def __init__(self, parent, workspace: Workspace):
        super(MainWindowHLayout, self).__init__(workspace)
        self.setObjectName("main_window_h_layout")
        self.parent = parent
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.left_bar = MainWindowLeftSideBar(workspace, self)
        layout.addWidget(self.left_bar)
        self.workspace = MainWindowWorkspace(self, workspace)
        layout.addWidget(self.workspace, 1)
        self.right_bar = MainWindowRightSideBar(workspace, self)
        layout.addWidget(self.right_bar)
        
        # Connect left bar button clicks to panel switcher
        self.left_bar.button_clicked.connect(
            self.workspace.workspace_top.left.switch_to_panel
        )
        
        # Switch to resource panel by default
        self.workspace.workspace_top.left.switch_to_panel('resource')

