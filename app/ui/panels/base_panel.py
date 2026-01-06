"""Base panel class for workspace tool panels."""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize
from app.ui.base_widget import BaseWidget
from app.data.workspace import Workspace


class BasePanel(BaseWidget):
    """
    Abstract base class for workspace tool panels.
    
    All panels must inherit from this class and implement the required lifecycle methods.
    Provides consistent interface for panel switching and state management.
    """
    
    def __init__(self, workspace: Workspace, parent=None):
        """
        Initialize the panel with workspace context.
        
        Args:
            workspace: Workspace instance providing access to project and services
            parent: Optional parent widget
        """
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
            
        # Initialize UI structure
        self._init_base_ui()
        
        self._is_active = False
        self._data_loaded = False
        
        # Only setup UI framework, not data loading
        self.setup_ui()
        
    def _init_base_ui(self):
        """Initialize the base layout with toolbar and content area."""
        # Main vertical layout for the whole panel
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # Top toolbar
        self.toolbar = QWidget()
        self.toolbar.setObjectName("panelToolbar")
        self.toolbar.setFixedHeight(40)
        self.toolbar.setStyleSheet("""
            QWidget#panelToolbar {
                background-color: #2D2D2D;
                border-bottom: 1px solid #1E1E1E;
            }
            QLabel#panelTitle {
                color: #E0E0E0;
                font-weight: bold;
                font-size: 12px;
                margin-left: 8px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            QPushButton.toolbarButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: #A0A0A0;
                padding: 4px;
                font-family: "iconfont";
                font-size: 16px;
            }
            QPushButton.toolbarButton:hover {
                background-color: #3D3D3D;
                color: #FFFFFF;
            }
            QPushButton.toolbarButton:pressed {
                background-color: #4D4D4D;
            }
        """)
        
        self.toolbar_layout = QHBoxLayout(self.toolbar)
        self.toolbar_layout.setContentsMargins(8, 0, 8, 0)
        self.toolbar_layout.setSpacing(4)
        
        # Left side: Title
        self.title_label = QLabel()
        self.title_label.setObjectName("panelTitle")
        self.toolbar_layout.addWidget(self.title_label)
        
        # Middle: Spacer
        self.toolbar_layout.addStretch()
        
        # Right side: Actions
        self.actions_widget = QWidget()
        self.actions_layout = QHBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(4)
        self.toolbar_layout.addWidget(self.actions_widget)
        
        self._main_layout.addWidget(self.toolbar)
        
        # Content area
        self.content_widget = QWidget()
        self.content_widget.setObjectName("panelContent")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        self._main_layout.addWidget(self.content_widget, 1)

    def set_panel_title(self, title: str):
        """Set the panel title in the toolbar."""
        self.title_label.setText(title)
        
    def add_toolbar_button(self, icon_text: str, callback=None, tooltip: str = ""):
        """Add an icon button to the toolbar's right side."""
        button = QPushButton(icon_text)
        button.setProperty("class", "toolbarButton")
        button.setFixedSize(28, 28)
        if tooltip:
            button.setToolTip(tooltip)
        if callback:
            button.clicked.connect(callback)
        self.actions_layout.addWidget(button)
        return button

    def setup_ui(self):
        """
        Set up the panel UI framework (widgets, layouts, etc.).
        
        This method should create and configure UI widgets and layouts.
        Should NOT load business data - that should be done in load_data().
        Called during initialization.
        Subclasses must override this method.
        """
        raise NotImplementedError("Subclasses must implement setup_ui()")
    
    def load_data(self):
        """
        Load business data for the panel.
        
        This method should load data from managers, databases, etc.
        Called when panel is first activated or when data needs refresh.
        Override this method to load panel-specific data.
        """
        # Default implementation does nothing
        # Subclasses should override to load their data
        pass
    
    def on_activated(self):
        """
        Called when the panel becomes visible/active.
        
        Override this method to refresh data, reconnect signals,
        or perform any necessary updates when panel is shown.
        """
        self._is_active = True
        
        # Load data on first activation if not already loaded
        if not self._data_loaded:
            self.load_data()
            self._data_loaded = True
    
    def on_deactivated(self):
        """
        Called when the panel is hidden/deactivated.
        
        Override this method to disconnect signals, pause operations,
        or clean up resources when panel is hidden.
        """
        self._is_active = False
    
    def is_active(self) -> bool:
        """
        Check if panel is currently active.
        
        Returns:
            True if panel is active, False otherwise
        """
        return self._is_active
