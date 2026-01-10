from PySide6.QtWidgets import QHBoxLayout

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from app.ui.timeline.timeline_container import TimelineContainer


class MainWindowWorkspaceBottom(BaseWidget):

    def __init__(self, parent, workspace: Workspace):
        super(MainWindowWorkspaceBottom, self).__init__(workspace)
        self.setObjectName("main_window_workspace_bottom")
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        # Wrap the timeline in a container that draws the cursor line
        self.timeline_container = TimelineContainer(self, workspace)

        # Set fixed height for timeline to prevent it from expanding
        self.setMinimumHeight(220)  # Increased to accommodate additional timelines
        self.setMaximumHeight(260)  # Increased to accommodate additional timelines

        # Add the container (which contains the timeline) to the layout
        self.layout.addWidget(self.timeline_container)

