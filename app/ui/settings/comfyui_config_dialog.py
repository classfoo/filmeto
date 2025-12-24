"""
ComfyUI Configuration Dialog

Mac-style configuration dialog with sidebar navigation for ComfyUI server setup.
Includes service settings, workflow management, and marketplace.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QListWidget, QListWidgetItem, QStackedWidget,
    QFrame, QScrollArea, QFormLayout, QLineEdit, QSpinBox,
    QCheckBox, QMessageBox, QFileDialog, QTextEdit, QComboBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QCursor

from app.plugins.service_registry import ServiceRegistry
from app.ui.settings.field_widget_factory import FieldWidgetFactory
from app.spi.service import ConfigField


class ComfyUIConfigDialog(QDialog):
    """Mac-style configuration dialog for ComfyUI"""
    
    config_saved = Signal(str)  # service_id
    
    def __init__(self, service_id: str, service_registry: ServiceRegistry, workspace_path: str, parent=None):
        super().__init__(parent)
        
        self.service_id = service_id
        self.service_registry = service_registry
        self.workspace_path = workspace_path
        self.service_info = service_registry.get_service_info(service_id)
        self.config_manager = service_registry.get_config_manager()
        
        # Workflow storage path
        self.workflows_dir = Path(workspace_path) / "servers" / "comfyui" / "workflows"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        
        self.field_widgets: Dict[str, QWidget] = {}
        self.workflows: List[Dict[str, Any]] = []
        
        if not self.service_info:
            raise ValueError(f"Service not found: {service_id}")
        
        self._init_ui()
        self._load_config()
        self._load_workflows()
    
    def _init_ui(self):
        """Initialize the UI with sidebar layout"""
        self.setWindowTitle("ComfyUI Configuration")
        self.setMinimumSize(900, 700)
        self.setModal(True)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Create content area
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #1e1e1e;")
        
        # Create pages
        self.service_page = self._create_service_page()
        self.workflow_page = self._create_workflow_page()
        self.marketplace_page = self._create_marketplace_page()
        
        self.content_stack.addWidget(self.service_page)
        self.content_stack.addWidget(self.workflow_page)
        self.content_stack.addWidget(self.marketplace_page)
        
        main_layout.addWidget(self.content_stack, 1)
        
        # Apply styling
        self._apply_style()
    
    def _create_sidebar(self) -> QWidget:
        """Create Mac-style sidebar"""
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-right: 1px solid #3a3a3a;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with icon and info
        header = self._create_sidebar_header()
        layout.addWidget(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #3a3a3a;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # Menu list
        self.menu_list = QListWidget()
        self.menu_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
                padding: 8px 0;
            }
            QListWidget::item {
                padding: 12px 20px;
                color: #cccccc;
                font-size: 13px;
                border: none;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: #ffffff;
            }
        """)
        self.menu_list.setSpacing(2)
        
        # Add menu items
        menu_items = [
            ("Service", "\ue6a7"),  # Settings icon
            ("Workflows", "\ue6a8"),  # Workflow icon
            ("Marketplace", "\ue6a9")  # Market icon
        ]
        
        for text, icon in menu_items:
            item = QListWidgetItem(f"{icon}  {text}")
            font = QFont()
            font.setFamily("iconfont")
            font.setPointSize(12)
            item.setFont(font)
            self.menu_list.addItem(item)
        
        self.menu_list.setCurrentRow(0)
        self.menu_list.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        
        layout.addWidget(self.menu_list)
        layout.addStretch()
        
        # Footer with action buttons
        footer = self._create_sidebar_footer()
        layout.addWidget(footer)
        
        return sidebar
    
    def _create_sidebar_header(self) -> QWidget:
        """Create sidebar header with ComfyUI info"""
        header = QWidget()
        header.setFixedHeight(120)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel(self.service_info.icon)
        icon_font = QFont()
        icon_font.setFamily("iconfont")
        icon_font.setPointSize(32)
        icon_label.setFont(icon_font)
        icon_label.setStyleSheet("color: #3498db; border: none;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Service name
        name_label = QLabel(self.service_info.name)
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #ffffff; border: none;")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)
        
        # Version
        version_label = QLabel(f"Version {self.service_info.version}")
        version_label.setStyleSheet("color: #888888; font-size: 11px; border: none;")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        return header
    
    def _create_sidebar_footer(self) -> QWidget:
        """Create sidebar footer with action buttons"""
        footer = QWidget()
        footer.setFixedHeight(80)
        footer.setStyleSheet("border-top: 1px solid #3a3a3a; border-right: none;")
        
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Save button
        save_btn = QPushButton("Save Configuration")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._on_save_clicked)
        save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 16px;
                background-color: #3498db;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(save_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(32)
        close_btn.clicked.connect(self.reject)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 16px;
                background-color: transparent;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #cccccc;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)
        layout.addWidget(close_btn)
        
        return footer
    
    def _create_service_page(self) -> QWidget:
        """Create service configuration page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Page header
        header = self._create_page_header(
            "Service Configuration",
            "Configure ComfyUI server connection and basic settings"
        )
        layout.addWidget(header)
        
        # Scroll area for form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { background-color: #1e1e1e; border: none; }")
        
        # Form container
        form_container = QWidget()
        form_container.setStyleSheet("background-color: #1e1e1e;")
        container_layout = QVBoxLayout(form_container)
        container_layout.setContentsMargins(30, 20, 30, 20)
        container_layout.setSpacing(20)
        
        # Get config schema and create form
        service_class = self.service_info.service_class
        config_schema = service_class.get_config_schema()
        
        for group in config_schema.groups:
            if group.name != "workflows":  # Skip workflows group, handled separately
                group_widget = self._create_form_group(group)
                container_layout.addWidget(group_widget)
        
        container_layout.addStretch()
        
        scroll_area.setWidget(form_container)
        layout.addWidget(scroll_area, 1)
        
        return page
    
    def _create_workflow_page(self) -> QWidget:
        """Create workflow management page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Page header
        header = self._create_page_header(
            "Workflow Management",
            "Manage ComfyUI workflow files and configure node mappings"
        )
        layout.addWidget(header)
        
        # Content area
        content = QWidget()
        content.setStyleSheet("background-color: #1e1e1e;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(15)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        add_btn = QPushButton("+ Add Workflow")
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self._on_add_workflow)
        add_btn.setCursor(QCursor(Qt.PointingHandCursor))
        add_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 16px;
                background-color: #3498db;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
        """)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()
        
        content_layout.addLayout(toolbar)
        
        # Workflow list
        self.workflow_list = QListWidget()
        self.workflow_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 8px;
            }
            QListWidget::item {
                padding: 12px;
                margin: 4px 0;
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
                border-color: #3498db;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                border-color: #3498db;
            }
        """)
        self.workflow_list.itemDoubleClicked.connect(self._on_configure_workflow)
        content_layout.addWidget(self.workflow_list, 1)
        
        # Workflow actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        configure_btn = QPushButton("Configure")
        configure_btn.clicked.connect(self._on_configure_workflow)
        configure_btn.setCursor(QCursor(Qt.PointingHandCursor))
        configure_btn.setStyleSheet(self._get_action_button_style())
        actions_layout.addWidget(configure_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._on_remove_workflow)
        remove_btn.setCursor(QCursor(Qt.PointingHandCursor))
        remove_btn.setStyleSheet(self._get_action_button_style("#e74c3c", "#c0392b"))
        actions_layout.addWidget(remove_btn)
        
        actions_layout.addStretch()
        
        content_layout.addLayout(actions_layout)
        
        layout.addWidget(content, 1)
        
        return page
    
    def _create_marketplace_page(self) -> QWidget:
        """Create marketplace page for online workflows"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Page header
        header = self._create_page_header(
            "Workflow Marketplace",
            "Browse and download community workflows"
        )
        layout.addWidget(header)
        
        # Content area
        content = QWidget()
        content.setStyleSheet("background-color: #1e1e1e;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(15)
        
        # Marketplace list (placeholder)
        marketplace_list = QListWidget()
        marketplace_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 8px;
            }
            QListWidget::item {
                padding: 16px;
                margin: 6px 0;
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
                border-color: #3498db;
            }
        """)
        
        # Add sample marketplace items
        sample_workflows = [
            ("Text to Image - SDXL", "High quality text-to-image workflow using SDXL"),
            ("Image Upscale - 4x", "Upscale images using AI models"),
            ("Video Generation", "Generate videos from text prompts"),
            ("Style Transfer", "Apply artistic styles to images"),
        ]
        
        for name, desc in sample_workflows:
            item = QListWidgetItem(f"{name}\n{desc}")
            marketplace_list.addItem(item)
        
        content_layout.addWidget(marketplace_list, 1)
        
        # Download button
        download_btn = QPushButton("Download Selected")
        download_btn.setFixedHeight(36)
        download_btn.clicked.connect(self._on_download_workflow)
        download_btn.setCursor(QCursor(Qt.PointingHandCursor))
        download_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 24px;
                background-color: #27ae60;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        content_layout.addWidget(download_btn)
        
        layout.addWidget(content, 1)
        
        return page
    
    def _create_page_header(self, title: str, description: str) -> QWidget:
        """Create page header with title and description"""
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #252525; border-bottom: 1px solid #3a3a3a;")
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(4)
        
        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff; border: none;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #888888; font-size: 12px; border: none;")
        layout.addWidget(desc_label)
        
        return header
    
    def _create_form_group(self, group) -> QWidget:
        """Create a form group widget"""
        group_frame = QFrame()
        group_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
            }
        """)
        
        group_layout = QVBoxLayout(group_frame)
        group_layout.setContentsMargins(20, 15, 20, 15)
        group_layout.setSpacing(12)
        
        # Group label
        group_label = QLabel(group.label)
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        group_label.setFont(font)
        group_label.setStyleSheet("color: #ffffff; border: none;")
        group_layout.addWidget(group_label)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.setSpacing(12)
        form_layout.setHorizontalSpacing(15)
        
        # Add fields
        for field in group.fields:
            self._add_field_to_form(form_layout, group, field)
        
        group_layout.addLayout(form_layout)
        
        return group_frame
    
    def _add_field_to_form(self, form_layout: QFormLayout, group, field: ConfigField):
        """Add a field to the form"""
        # Create label
        label_text = field.label
        if field.required:
            label_text += " *"
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #cccccc; font-size: 12px;")
        label.setToolTip(field.description)
        
        # Get current value
        key = f"{group.name}.{field.name}"
        config = self.config_manager.get_config(self.service_id) or {}
        group_config = config.get(group.name, {})
        current_value = group_config.get(field.name, field.default)
        
        # Create widget
        widget = FieldWidgetFactory.create_widget(field, current_value)
        widget.setFixedWidth(400)
        
        # Store widget reference
        self.field_widgets[key] = widget
        
        # Create container for widget and description
        widget_container = QWidget()
        widget_layout = QVBoxLayout(widget_container)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(4)
        
        widget_layout.addWidget(widget)
        
        # Add description
        if field.description:
            desc_label = QLabel(field.description)
            desc_label.setStyleSheet("color: #666666; font-size: 10px;")
            desc_label.setWordWrap(True)
            desc_label.setMaximumWidth(400)
            widget_layout.addWidget(desc_label)
        
        # Add to form
        form_layout.addRow(label, widget_container)
    
    def _get_action_button_style(self, bg_color: str = "#555555", hover_color: str = "#666666") -> str:
        """Get action button stylesheet"""
        return f"""
            QPushButton {{
                padding: 6px 16px;
                background-color: {bg_color};
                border: none;
                border-radius: 4px;
                color: #ffffff;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """
    
    def _apply_style(self):
        """Apply overall dialog style"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
        """)
    
    def _load_config(self):
        """Load current configuration"""
        config = self.config_manager.get_config(self.service_id)
        if not config:
            return
        
        # Update widgets with current values
        service_class = self.service_info.service_class
        config_schema = service_class.get_config_schema()
        
        for group in config_schema.groups:
            group_config = config.get(group.name, {})
            
            for field in group.fields:
                key = f"{group.name}.{field.name}"
                if key in self.field_widgets:
                    value = group_config.get(field.name, field.default)
                    widget = self.field_widgets[key]
                    self._set_widget_value(widget, field.type, value)
    
    def _set_widget_value(self, widget: QWidget, field_type: str, value: Any):
        """Set widget value based on field type"""
        if field_type == 'text' or field_type == 'password':
            widget.setText(str(value))
        elif field_type == 'number':
            widget.setValue(int(value) if value is not None else 0)
        elif field_type == 'boolean':
            widget.setChecked(bool(value))
        elif field_type == 'select':
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)
    
    def _load_workflows(self):
        """Load workflows from workspace directory"""
        self.workflows = []
        self.workflow_list.clear()
        
        if not self.workflows_dir.exists():
            return
        
        # Load workflow metadata files
        for workflow_file in self.workflows_dir.glob("*.json"):
            try:
                import json
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                    
                # Check if it's a metadata file or actual workflow
                if "name" in workflow_data and "type" in workflow_data:
                    self.workflows.append(workflow_data)
                    
                    # Add to list
                    item_text = f"{workflow_data['name']}\nType: {workflow_data.get('type', 'Unknown')}"
                    if workflow_data.get('description'):
                        item_text += f"\n{workflow_data['description']}"
                    
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, workflow_data)
                    self.workflow_list.addItem(item)
            except Exception as e:
                print(f"Failed to load workflow {workflow_file}: {e}")
    
    def _on_add_workflow(self):
        """Handle add workflow button click"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Workflow File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Open workflow configuration dialog
        from app.ui.settings.workflow_config_dialog import WorkflowConfigDialog
        
        dialog = WorkflowConfigDialog(file_path, self.workflows_dir, self)
        if dialog.exec() == QDialog.Accepted:
            # Reload workflows
            self._load_workflows()
    
    def _on_configure_workflow(self):
        """Handle configure workflow button click"""
        current_item = self.workflow_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a workflow to configure.")
            return
        
        workflow_data = current_item.data(Qt.UserRole)
        workflow_file = self.workflows_dir / workflow_data.get('file', '')
        
        if not workflow_file.exists():
            QMessageBox.warning(self, "File Not Found", "Workflow file not found.")
            return
        
        # Open workflow configuration dialog
        from app.ui.settings.workflow_config_dialog import WorkflowConfigDialog
        
        dialog = WorkflowConfigDialog(str(workflow_file), self.workflows_dir, self, workflow_data)
        if dialog.exec() == QDialog.Accepted:
            # Reload workflows
            self._load_workflows()
    
    def _on_remove_workflow(self):
        """Handle remove workflow button click"""
        current_item = self.workflow_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a workflow to remove.")
            return
        
        workflow_data = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove the workflow '{workflow_data['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove workflow file
            workflow_file = self.workflows_dir / workflow_data.get('file', '')
            if workflow_file.exists():
                workflow_file.unlink()
            
            # Reload workflows
            self._load_workflows()
    
    def _on_download_workflow(self):
        """Handle download workflow from marketplace"""
        QMessageBox.information(
            self,
            "Coming Soon",
            "Marketplace functionality will be available in a future update."
        )
    
    def _on_save_clicked(self):
        """Handle save button click"""
        # Collect configuration from widgets
        service_class = self.service_info.service_class
        config_schema = service_class.get_config_schema()
        
        new_config = {}
        
        for group in config_schema.groups:
            if group.name == "workflows":
                continue  # Skip workflows group
                
            new_config[group.name] = {}
            
            for field in group.fields:
                key = f"{group.name}.{field.name}"
                if key in self.field_widgets:
                    widget = self.field_widgets[key]
                    value = FieldWidgetFactory.get_widget_value(widget, field.type)
                    new_config[group.name][field.name] = value
        
        # Validate configuration
        service = self.service_registry.get_service_by_id(self.service_id)
        if service and not service.validate_config(new_config):
            QMessageBox.warning(
                self,
                "Validation Error",
                "Configuration validation failed. Please check required fields."
            )
            return
        
        # Save configuration
        config_path = self.service_info.service_class.get_config_path()
        if self.config_manager.save_config(self.service_id, config_path, new_config):
            QMessageBox.information(
                self,
                "Success",
                f"{self.service_info.name} configuration saved successfully!"
            )
            self.config_saved.emit(self.service_id)
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to save configuration. Please try again."
            )

