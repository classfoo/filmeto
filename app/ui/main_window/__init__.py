# Export all classes for backward compatibility
from .main_window import MainWindow
from .top_bar import MainWindowTopBar
from .bottom_bar import MainWindowBottomBar
from .left_bar import MainWindowLeftBar
from .right_bar import MainWindowRightBar
from .workspace_top import MainWindowWorkspaceTop
from .workspace_bottom import MainWindowWorkspaceBottom
from .workspace import MainWindowWorkspace
from .h_layout import MainWindowHLayout

__all__ = [
    'MainWindow',
    'MainWindowTopBar',
    'MainWindowBottomBar',
    'MainWindowLeftBar',
    'MainWindowRightBar',
    'MainWindowWorkspaceTop',
    'MainWindowWorkspaceBottom',
    'MainWindowWorkspace',
    'MainWindowHLayout',
]

