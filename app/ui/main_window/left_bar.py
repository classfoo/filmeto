from app.data.workspace import Workspace
from .left_side_bar import MainWindowLeftSideBar


class LeftBar:
    """Left bar component wrapper for better management."""
    
    def __init__(self, workspace: Workspace, parent):
        """
        Initialize the left bar component.
        
        Args:
            workspace: The workspace instance
            parent: The parent widget
        """
        self.workspace = workspace
        self.parent = parent
        self.bar = MainWindowLeftSideBar(workspace, parent)
        self.workspace_top_left = None
    
    def connect_signals(self, workspace_top_left):
        """
        Connect left bar signals to workspace panel switcher.
        
        Args:
            workspace_top_left: The workspace top left panel switcher instance
        """
        self.workspace_top_left = workspace_top_left
        # Connect button click to panel switching
        self.bar.button_clicked.connect(workspace_top_left.switch_to_panel)
        # Connect panel switched signal to update button state
        workspace_top_left.panel_switched.connect(self.bar.set_selected_button)
    
    def get_widget(self):
        """Get the actual widget instance."""
        return self.bar

