"""Models panel for AI model management."""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QWidget, QProgressBar, QTabWidget
)
from PySide6.QtCore import Qt
from app.ui.panels.base_panel import BasePanel
from app.data.workspace import Workspace


class ModelItemWidget(QWidget):
    """Widget for displaying a single model item."""
    
    def __init__(self, model_info, parent=None):
        super().__init__(parent)
        self.model_info = model_info
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the model item UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Model name
        name_label = QLabel(self.model_info.get('name', 'Unknown Model'), self)
        name_label.setStyleSheet("""
            QLabel {
                color: #E1E1E1;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        layout.addWidget(name_label)
        
        # Model info
        info_layout = QHBoxLayout()
        
        type_label = QLabel(f"Type: {self.model_info.get('type', 'N/A')}", self)
        type_label.setStyleSheet("color: #888888; font-size: 11px;")
        info_layout.addWidget(type_label)
        
        size_label = QLabel(f"Size: {self.model_info.get('size', 'N/A')}", self)
        size_label.setStyleSheet("color: #888888; font-size: 11px;")
        info_layout.addWidget(size_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Status
        status = self.model_info.get('status', 'available')
        status_label = QLabel(f"Status: {status.capitalize()}", self)
        status_label.setStyleSheet("""
            QLabel {
                color: #4a80b0;
                font-size: 11px;
            }
        """)
        layout.addWidget(status_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        if status == 'available':
            download_btn = QPushButton("Download", self)
            download_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3c3f41;
                    color: #bbbbbb;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 4px 12px;
                }
                QPushButton:hover {
                    background-color: #4a80b0;
                    color: #ffffff;
                }
            """)
            button_layout.addWidget(download_btn)
        elif status == 'installed':
            activate_btn = QPushButton("Activate", self)
            activate_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3c3f41;
                    color: #bbbbbb;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 4px 12px;
                }
                QPushButton:hover {
                    background-color: #4a80b0;
                    color: #ffffff;
                }
            """)
            button_layout.addWidget(activate_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)


class ModelsPanel(BasePanel):
    """
    Panel for managing AI models.
    
    Provides model catalog, download, installation, and version management.
    """
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the models panel."""
        super().__init__(workspace, parent)
    
    def setup_ui(self):
        """Set up the UI components."""
        self.set_panel_title("Models")
        
        # Container for content
        content_container = QWidget()
        layout = QVBoxLayout(content_container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Tab widget for Available/Installed
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3c3f41;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3f41;
                color: #bbbbbb;
                padding: 6px 12px;
                border: 1px solid #3c3f41;
            }
            QTabBar::tab:selected {
                background-color: #4a80b0;
                color: #ffffff;
            }
        """)
        
        # Available models tab
        self.available_list = QListWidget(self)
        self.available_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                border: none;
                outline: 0;
            }
            QListWidget::item {
                border-bottom: 1px solid #3c3f41;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #3a75c9;
            }
        """)
        self.tab_widget.addTab(self.available_list, "Available")
        
        # Installed models tab
        self.installed_list = QListWidget(self)
        self.installed_list.setStyleSheet(self.available_list.styleSheet())
        self.tab_widget.addTab(self.installed_list, "Installed")
        
        layout.addWidget(self.tab_widget, 1)
        
        # Storage info
        storage_layout = QHBoxLayout()
        self.storage_label = QLabel("Storage: Loading...", self)
        self.storage_label.setStyleSheet("color: #888888; font-size: 11px;")
        storage_layout.addWidget(self.storage_label)
        
        manage_storage_btn = QPushButton("Manage Storage", self)
        manage_storage_btn.setFixedWidth(120)
        manage_storage_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3f41;
                color: #bbbbbb;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #4a80b0;
                color: #ffffff;
            }
        """)
        storage_layout.addWidget(manage_storage_btn)
        
        layout.addLayout(storage_layout)
        
        self.content_layout.addWidget(content_container)
    
    def load_data(self):
        """Load models data when panel is first activated."""
        super().load_data()
        self._load_models()
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        # Refresh models when panel is activated (if data already loaded)
        if self._data_loaded:
            self._load_models()
        print("✅ Models panel activated")
    
    def on_deactivated(self):
        """Called when panel is hidden."""
        super().on_deactivated()
        print("⏸️ Models panel deactivated")
    
    def _load_models(self):
        """Load model catalog (mock data for now)."""
        # Mock available models
        available_models = [
            {
                'name': 'Stable Diffusion v1.5',
                'type': 'text2img',
                'size': '4.2 GB',
                'status': 'available',
                'description': 'Popular text-to-image model'
            },
            {
                'name': 'SDXL Base',
                'type': 'text2img',
                'size': '6.5 GB',
                'status': 'available',
                'description': 'High-resolution text-to-image model'
            },
            {
                'name': 'ControlNet',
                'type': 'img2img',
                'size': '2.8 GB',
                'status': 'available',
                'description': 'Image guidance model'
            },
        ]
        
        # Mock installed models
        installed_models = [
            {
                'name': 'Qwen Vision',
                'type': 'multimodal',
                'size': '3.5 GB',
                'status': 'installed',
                'description': 'Multimodal understanding model'
            },
        ]
        
        # Populate available models
        for model in available_models:
            item = QListWidgetItem(self.available_list)
            widget = ModelItemWidget(model, self.available_list)
            item.setSizeHint(widget.sizeHint())
            self.available_list.addItem(item)
            self.available_list.setItemWidget(item, widget)
        
        # Populate installed models
        for model in installed_models:
            item = QListWidgetItem(self.installed_list)
            widget = ModelItemWidget(model, self.installed_list)
            item.setSizeHint(widget.sizeHint())
            self.installed_list.addItem(item)
            self.installed_list.setItemWidget(item, widget)
        
        # Update storage info
        total_size = sum(float(m['size'].split()[0]) for m in available_models + installed_models if 'GB' in m['size'])
        self.storage_label.setText(f"Storage: {total_size:.1f} GB used / 100 GB")
