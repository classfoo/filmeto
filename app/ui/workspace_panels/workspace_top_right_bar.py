"""Main switcher component for workspace top right bar panels."""

from typing import Dict, Type, Optional
from PySide6.QtWidgets import QStackedWidget, QWidget
from PySide6.QtCore import Signal, Slot

from app.ui.base_widget import BaseWidget
from app.data.workspace import Workspace
from .base_panel import BasePanel


class MainWindowWorkspaceTopRightBar(BaseWidget):
    """
    Orchestrates panel switching and lifecycle management for the workspace right sidebar.
    
    Manages multiple tool panels and switches between them
    based on button clicks from MainWindowRightBar. Uses lazy loading to instantiate
    panels only when first accessed.
    """
    
    # Signal emitted when panel switches (panel_name)
    panel_switched = Signal(str)
    
    def __init__(self, workspace: Workspace, parent=None):
        """
        Initialize the panel switcher.
        
        Args:
            workspace: Workspace instance for data access
            parent: Optional parent widget
        """
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        
        # State management
        self.current_panel: Optional[BasePanel] = None
        self.panel_instances: Dict[str, BasePanel] = {}
        self.panel_registry: Dict[str, Type[BasePanel]] = {}
        
        # Setup UI
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setObjectName("workspace_panels_stack_right")
        
        # Register panels (lazy loading - classes only)
        self._register_panels()
        
        # Set up layout
        from PySide6.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.stacked_widget)
    
    def _register_panels(self):
        """
        Register panel classes in the registry.
        
        Panel instances are created lazily when first accessed.
        """
        # Import panel classes
        from .agent import AgentPanel
        from .chat_history import ChatHistoryPanel
        
        # Map button names to panel classes
        self.panel_registry = {
            'agent': AgentPanel,
            'chat_history': ChatHistoryPanel,
        }
    
    @Slot(str)
    def switch_to_panel(self, panel_name: str):
        """
        Switch to the specified panel.
        
        Handles lazy instantiation, panel lifecycle, and visibility management.
        
        Args:
            panel_name: Name of the panel to switch to (e.g., 'agent', 'chat_history')
        """
        if panel_name not in self.panel_registry:
            print(f"⚠️ Unknown right panel: {panel_name}")
            return
        
        # Deactivate current panel if exists
        if self.current_panel:
            self.current_panel.on_deactivated()
        
        # Check if panel instance exists in cache
        if panel_name not in self.panel_instances:
            # Lazy instantiation
            panel_class = self.panel_registry[panel_name]
            try:
                panel_instance = panel_class(self.workspace, self)
                self.panel_instances[panel_name] = panel_instance
                self.stacked_widget.addWidget(panel_instance)
                print(f"✅ Created right panel: {panel_name}")
            except Exception as e:
                print(f"❌ Error creating right panel {panel_name}: {e}")
                import traceback
                traceback.print_exc()
                return
        
        # Switch to panel
        panel = self.panel_instances[panel_name]
        self.stacked_widget.setCurrentWidget(panel)
        panel.on_activated()
        self.current_panel = panel
        
        # Emit signal
        self.panel_switched.emit(panel_name)
        print(f"🔄 Switched to right panel: {panel_name}")
    
    def get_current_panel(self) -> Optional[BasePanel]:
        """
        Get the currently active panel.
        
        Returns:
            Current panel instance or None
        """
        return self.current_panel
    
    def get_panel(self, panel_name: str) -> Optional[BasePanel]:
        """
        Get a panel instance by name.
        
        Args:
            panel_name: Name of the panel
            
        Returns:
            Panel instance if it has been instantiated, None otherwise
        """
        return self.panel_instances.get(panel_name)
