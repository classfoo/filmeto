from PySide6.QtWidgets import QHBoxLayout, QSplitter
from PySide6.QtCore import Qt

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from .workspace_top import MainWindowWorkspaceTop
from .workspace_bottom import MainWindowWorkspaceBottom


class MainWindowWorkspace(BaseWidget):

    def __init__(self, parent, workspace: Workspace):
        super(MainWindowWorkspace, self).__init__(workspace)
        self.setObjectName("main_window_workspace")
        self.parent = parent

        # 主布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setObjectName("main_window_workspace_splitter")
        self.splitter.setChildrenCollapsible(False)

        self.workspace_top = MainWindowWorkspaceTop(self, workspace)
        self.splitter.addWidget(self.workspace_top)

        self.workspace_bottom = MainWindowWorkspaceBottom(self, workspace)
        self.splitter.addWidget(self.workspace_bottom)

        # Set initial sizes and stretch factors
        # Top area should expand, bottom (timeline) should stay fixed
        self.splitter.setSizes([1200, 200])
        self.splitter.setStretchFactor(0, 1)  # Top: stretch
        self.splitter.setStretchFactor(1, 0)  # Bottom (timeline): don't stretch

        self.layout.addWidget(self.splitter)

