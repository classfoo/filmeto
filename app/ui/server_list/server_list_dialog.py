"""
Server List Dialog

DEPRECATED: Use UnifiedServerDialog instead.

This file is kept for backward compatibility and simply wraps the new
UnifiedServerDialog which provides a Mac-style unified interface.
"""

from PySide6.QtCore import Signal
from app.ui.server_list.unified_server_dialog import UnifiedServerDialog


class ServerListDialog(UnifiedServerDialog):
    """
    Backward compatible wrapper for UnifiedServerDialog.
    
    Simply inherits all functionality from the new unified dialog.
    """
    pass
