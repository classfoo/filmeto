from app.data.workspace import Workspace
from .right_side_bar import MainWindowRightSideBar


class RightBar:
    """Right bar component wrapper for better management."""
    
    def __init__(self, workspace: Workspace, parent):
        """
        Initialize the right bar component.
        
        Args:
            workspace: The workspace instance
            parent: The parent widget
        """
        self.workspace = workspace
        self.parent = parent
        self.bar = MainWindowRightSideBar(workspace, parent)
    
    def get_widget(self):
        """Get the actual widget instance."""
        return self.bar

