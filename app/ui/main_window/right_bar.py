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
        self.workspace_top_right = None
    
    def connect_signals(self, workspace_top_right):
        """
        Connect right bar signals to workspace panel switcher.
        
        Args:
            workspace_top_right: The workspace top right panel switcher instance
        """
        self.workspace_top_right = workspace_top_right
        # Connect button click to panel switching
        self.bar.button_clicked.connect(workspace_top_right.switch_to_panel)
        # Connect panel switched signal to update button state
        workspace_top_right.panel_switched.connect(self.bar.set_selected_button)
    
    def get_widget(self):
        """Get the actual widget instance."""
        return self.bar

