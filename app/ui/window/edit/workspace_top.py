from PySide6.QtWidgets import QHBoxLayout, QSplitter
from PySide6.QtCore import Qt

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from app.ui.editor import MainEditorWidget


class MainWindowWorkspaceTop(BaseWidget):

    def __init__(self, parent, workspace):
        super(MainWindowWorkspaceTop, self).__init__(workspace)
        self.setObjectName("main_window_workspace_top")
        self.parent = parent
        # 主布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.splitter = QSplitter(Qt.Horizontal)
        self.setObjectName("main_window_workspace_top_splitter")
        # Disable stretching on splitter to maintain fixed sizes
        self.splitter.setChildrenCollapsible(False)

        # Left panel - switchable tool panels
        from app.ui.panels import MainWindowWorkspaceTopLeftBar
        self.left = MainWindowWorkspaceTopLeftBar(workspace, self)
        self.left.setObjectName("main_window_workspace_top_left")
        self.left.setMinimumWidth(240)
        self.left.setMaximumWidth(240)
        self.splitter.addWidget(self.left)

        # Center panel - preview (this should expand)
        self.center: MainEditorWidget = MainEditorWidget(workspace)
        self.splitter.addWidget(self.center)

        # Right panel - switchable tool panels
        from app.ui.panels.workspace_top_right_bar import MainWindowWorkspaceTopRightBar
        self.right = MainWindowWorkspaceTopRightBar(workspace, self)
        self.right.setObjectName("main_window_workspace_top_right")
        self.right.setMinimumWidth(100)
        self.right.setMaximumWidth(350)
        self.splitter.addWidget(self.right)

        # Set initial sizes and stretch factors
        # Left panel: 200px, Center: expand, Right panel: 300px
        self.splitter.setSizes([200, 1000, 350])
        self.splitter.setStretchFactor(0, 0)  # Left panel: don't stretch
        self.splitter.setStretchFactor(1, 1)  # Center panel: stretch
        self.splitter.setStretchFactor(2, 0)  # Right panel: don't stretch

        self.layout.addWidget(self.splitter)

