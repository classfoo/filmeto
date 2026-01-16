# Export all classes for backward compatibility
from app.ui.window.edit.top_side_bar import MainWindowTopSideBar
from app.ui.window.edit.bottom_side_bar import MainWindowBottomSideBar
from app.ui.window.edit.left_side_bar import MainWindowLeftSideBar
from app.ui.window.edit.right_side_bar import MainWindowRightSideBar
from app.ui.window.edit.workspace_top import MainWindowWorkspaceTop
from app.ui.window.edit.workspace_bottom import MainWindowWorkspaceBottom
from app.ui.window.edit.workspace import MainWindowWorkspace
from app.ui.window.edit.h_layout import MainWindowHLayout
from app.ui.window.edit.edit_widget import EditWidget

# Startup mode components
from .startup import (
    ProjectStartupWidget,
    ProjectListWidget,
    ProjectInfoWidget,
)

# New window classes
from app.ui.window.startup.startup_window import StartupWindow
from app.ui.window.edit.edit_window import EditWindow
from .window_manager import WindowManager

__all__ = [
    'MainWindowTopSideBar',
    'MainWindowBottomSideBar',
    'MainWindowLeftSideBar',
    'MainWindowRightSideBar',
    'MainWindowWorkspaceTop',
    'MainWindowWorkspaceBottom',
    'MainWindowWorkspace',
    'MainWindowHLayout',
    'EditWidget',
    'ProjectStartupWidget',
    'ProjectListWidget',
    'ProjectInfoWidget',
    'StartupWindow',
    'EditWindow',
    'WindowManager',
]

