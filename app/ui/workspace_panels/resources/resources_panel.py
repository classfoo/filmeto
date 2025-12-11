"""Resources panel for managing project resources."""

import os
from pathlib import Path
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QSplitter, QFileIconProvider,
    QHeaderView, QMenu
)
from PySide6.QtCore import Qt, QSize, QFileInfo
from PySide6.QtGui import QIcon, QBrush, QColor

from app.ui.workspace_panels.base_panel import BasePanel
from app.data.workspace import Workspace
from .resource_preview import ResourcePreview


class ResourceTreeView(QTreeWidget):
    """Tree widget for displaying project resources."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resource_manager = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the tree view UI."""
        # Set columns
        self.setHeaderLabels(["Name", "Type", "Size"])
        self.setHeaderHidden(False)
        
        # Configure header
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # Set styling
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #2b2b2b;
                color: #bbbbbb;
                border: 1px solid #3c3f41;
                outline: 0;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #3c3f41;
            }
            QTreeWidget::item:selected {
                background-color: #3a75c9;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #3c3f41;
                color: #bbbbbb;
                padding: 4px;
                border: 1px solid #2b2b2b;
            }
        """)
        
        # Set properties
        self.setIconSize(QSize(16, 16))
        self.setAlternatingRowColors(True)
        self.setAnimated(True)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)
        
        # Icon provider
        self.icon_provider = QFileIconProvider()
        
    def set_resource_manager(self, resource_manager):
        """Set the resource manager and load resources."""
        self.resource_manager = resource_manager
        self.refresh()
        
    def refresh(self):
        """Refresh the tree view with current resources."""
        self.clear()
        
        if not self.resource_manager:
            return
            
        # Get all resources
        resources = self.resource_manager.get_all()
        
        if not resources:
            # Show empty state
            empty_item = QTreeWidgetItem(self)
            empty_item.setText(0, "No resources available")
            empty_item.setForeground(0, QBrush(QColor("#888888")))
            empty_item.setFlags(Qt.ItemIsEnabled)
            return
        
        # Group resources by media type
        resources_by_type = {}
        for resource in resources:
            media_type = resource.media_type
            if media_type not in resources_by_type:
                resources_by_type[media_type] = []
            resources_by_type[media_type].append(resource)
        
        # Create tree structure
        for media_type, type_resources in sorted(resources_by_type.items()):
            # Create category item
            category_item = QTreeWidgetItem(self)
            category_item.setText(0, f"{media_type}s ({len(type_resources)})")
            category_item.setText(1, "Folder")
            folder_icon = self.icon_provider.icon(QFileIconProvider.Folder)
            category_item.setIcon(0, folder_icon)
            category_item.setExpanded(True)
            
            # Add resources
            for resource in sorted(type_resources, key=lambda r: r.name):
                resource_item = QTreeWidgetItem(category_item)
                resource_item.setText(0, resource.name)
                resource_item.setText(1, media_type.capitalize())
                resource_item.setText(2, self._format_size(resource.file_size))
                resource_item.setToolTip(0, resource.get_absolute_path(
                    self.resource_manager.project_path))
                
                # Set icon based on file type
                file_info = QFileInfo(resource.name)
                icon = self.icon_provider.icon(file_info)
                resource_item.setIcon(0, icon)
                
                # Store resource data
                resource_item.setData(0, Qt.UserRole, resource)
    
    def _format_size(self, size_bytes):
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        return f"{size:.1f} {size_names[i]}"
    
    def filter_resources(self, filter_text):
        """Filter resources by name."""
        if not filter_text:
            # Show all items
            iterator = QTreeWidgetItemIterator(self)
            while iterator.value():
                item = iterator.value()
                item.setHidden(False)
                iterator += 1
            return
        
        filter_text = filter_text.lower()
        
        # Hide/show items based on filter
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            if item.parent():  # Only filter leaf items
                name = item.text(0).lower()
                item.setHidden(filter_text not in name)
            iterator += 1
        
        # Hide empty categories
        for i in range(self.topLevelItemCount()):
            category = self.topLevelItem(i)
            has_visible_children = False
            for j in range(category.childCount()):
                if not category.child(j).isHidden():
                    has_visible_children = True
                    break
            category.setHidden(not has_visible_children)


class ResourcesPanel(BasePanel):
    """
    Panel for browsing and managing project resources.
    
    Provides tree view of resources, search/filter, preview, and operations.
    """
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the resources panel."""
        self.resource_manager = None
        super().__init__(workspace, parent)
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Search resources...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #3c3f41;
                color: #bbbbbb;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QLineEdit:focus {
                border: 1px solid #4a80b0;
            }
        """)
        self.search_box.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_box)
        
        self.refresh_button = QPushButton("\u21bb", self)  # Refresh icon
        self.refresh_button.setFixedSize(28, 28)
        self.refresh_button.setToolTip("Refresh")
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        search_layout.addWidget(self.refresh_button)
        
        layout.addLayout(search_layout)
        
        # Splitter for tree and preview
        splitter = QSplitter(Qt.Vertical, self)
        
        # Resource tree
        self.tree_view = ResourceTreeView(self)
        self.tree_view.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.tree_view)
        
        # Preview widget
        self.preview_widget = ResourcePreview(self)
        splitter.addWidget(self.preview_widget)
        
        # Set initial splitter sizes (70% tree, 30% preview)
        splitter.setSizes([350, 150])
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter, 1)
        
        # Info label at bottom
        self.info_label = QLabel("", self)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                padding: 2px;
            }
        """)
        layout.addWidget(self.info_label)
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        self._load_resources()
        self._connect_signals()
        print("✅ Resources panel activated")
    
    def on_deactivated(self):
        """Called when panel is hidden."""
        super().on_deactivated()
        self._disconnect_signals()
        print("⏸️ Resources panel deactivated")
    
    def _load_resources(self):
        """Load resources from the resource manager."""
        try:
            # Get resource manager from project
            project = self.workspace.get_project()
            if not hasattr(project, 'get_resource_manager'):
                self.info_label.setText("Resource manager not available")
                return
            
            self.resource_manager = project.get_resource_manager()
            self.tree_view.set_resource_manager(self.resource_manager)
            
            # Update info
            resource_count = len(self.resource_manager.get_all())
            self.info_label.setText(f"{resource_count} resource(s)")
            
        except Exception as e:
            print(f"❌ Error loading resources: {e}")
            self.info_label.setText(f"Error: {str(e)}")
    
    def _connect_signals(self):
        """Connect to ResourceManager signals for auto-refresh."""
        if not self.resource_manager:
            return
        
        try:
            # Connect to resource manager signals
            self.resource_manager.resource_added.connect(self._on_resource_added)
            self.resource_manager.resource_updated.connect(self._on_resource_updated)
            self.resource_manager.resource_deleted.connect(self._on_resource_deleted)
            print("✅ Connected to ResourceManager signals")
        except Exception as e:
            print(f"⚠️ Could not connect to ResourceManager signals: {e}")
    
    def _disconnect_signals(self):
        """Disconnect from ResourceManager signals."""
        if not self.resource_manager:
            return
        
        try:
            # Disconnect from resource manager signals
            self.resource_manager.resource_added.disconnect(self._on_resource_added)
            self.resource_manager.resource_updated.disconnect(self._on_resource_updated)
            self.resource_manager.resource_deleted.disconnect(self._on_resource_deleted)
            print("✅ Disconnected from ResourceManager signals")
        except Exception as e:
            print(f"⚠️ Could not disconnect from ResourceManager signals: {e}")
    
    def _on_resource_added(self, resource):
        """Handle resource added signal."""
        print(f"📥 Resource added: {resource.name}")
        self._load_resources()
    
    def _on_resource_updated(self, resource):
        """Handle resource updated signal."""
        print(f"🔄 Resource updated: {resource.name}")
        self._load_resources()
    
    def _on_resource_deleted(self, resource_name):
        """Handle resource deleted signal."""
        print(f"🗑️ Resource deleted: {resource_name}")
        self._load_resources()
        # Clear preview if deleted resource was selected
        self.preview_widget.clear_preview()
    
    def _on_search_changed(self, text):
        """Handle search text changes."""
        self.tree_view.filter_resources(text)
    
    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        self._load_resources()
    
    def _on_selection_changed(self):
        """Handle tree selection changes."""
        selected_items = self.tree_view.selectedItems()
        if not selected_items:
            self.preview_widget.clear_preview()
            return
        
        item = selected_items[0]
        # Get resource from item data
        resource = item.data(0, Qt.UserRole)
        
        if resource:
            try:
                project = self.workspace.get_project()
                resource_manager = project.get_resource_manager()
                self.preview_widget.set_resource(resource, resource_manager.project_path)
            except Exception as e:
                print(f"❌ Error showing preview: {e}")
