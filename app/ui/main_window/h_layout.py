from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtCore import QTimer

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
        
        # Immediately set default buttons as selected (before panel creation)
        # This provides instant visual feedback while panels load in background
        self.left_bar.bar.set_selected_button('character')
        self.right_bar.bar.set_selected_button('agent')
        
        # Switch to default panels immediately (panels will be created lazily)
        # Use minimal delay to ensure UI is ready but don't wait too long
        QTimer.singleShot(10, self._switch_to_default_panels)
    
    def _switch_to_default_panels(self):
        """Switch to default panels after UI is rendered."""
        # Switch to character panel by default (panel will be created lazily)
        self.workspace.workspace_top.left.switch_to_panel('character')
        
        # Switch to agent panel by default for right side (panel will be created lazily)
        self.workspace.workspace_top.right.switch_to_panel('agent')

