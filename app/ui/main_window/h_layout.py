from PySide6.QtWidgets import QHBoxLayout

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from .left_bar import LeftBar
from .right_bar import RightBar
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
        
        # Initialize left bar component
        self.left_bar = LeftBar(workspace, self)
        layout.addWidget(self.left_bar.get_widget())
        
        # Initialize workspace
        self.workspace = MainWindowWorkspace(self, workspace)
        layout.addWidget(self.workspace, 1)
        
        # Initialize right bar component
        self.right_bar = RightBar(workspace, self)
        layout.addWidget(self.right_bar.get_widget())
        
        # Connect left bar button clicks to panel switcher
        self.left_bar.connect_signals(self.workspace.workspace_top.left)
        
        # Connect right bar button clicks to panel switcher
        self.right_bar.connect_signals(self.workspace.workspace_top.right)
        
        # Switch to character panel by default (this will also update button state via signal)
        self.workspace.workspace_top.left.switch_to_panel('character')
        
        # Switch to agent panel by default for right side (this will also update button state via signal)
        self.workspace.workspace_top.right.switch_to_panel('agent')

