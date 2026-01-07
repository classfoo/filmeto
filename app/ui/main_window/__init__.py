# Export all classes for backward compatibility
from .main_window import MainWindow, WindowMode
from .top_side_bar import MainWindowTopSideBar
from .bottom_side_bar import MainWindowBottomSideBar
from .left_side_bar import MainWindowLeftSideBar
from .right_side_bar import MainWindowRightSideBar
from .workspace_top import MainWindowWorkspaceTop
from .workspace_bottom import MainWindowWorkspaceBottom
from .workspace import MainWindowWorkspace
from .h_layout import MainWindowHLayout
from .edit_widget import EditWidget

# Startup mode components
from .startup import (
    StartupWidget,
    ProjectListWidget,
    ProjectInfoWidget,
    StartupPromptWidget,
)

__all__ = [
    'MainWindow',
    'WindowMode',
    'MainWindowTopSideBar',
    'MainWindowBottomSideBar',
    'MainWindowLeftSideBar',
    'MainWindowRightSideBar',
    'MainWindowWorkspaceTop',
    'MainWindowWorkspaceBottom',
    'MainWindowWorkspace',
    'MainWindowHLayout',
    'EditWidget',
    'StartupWidget',
    'ProjectListWidget',
    'ProjectInfoWidget',
    'StartupPromptWidget',
]

