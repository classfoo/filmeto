"""
Plugin Detail Dialog

Modal dialog for detailed service plugin configuration.
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFormLayout, QWidget, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from app.plugins.service_registry import ServiceRegistry, ServiceInfo
from app.spi.service import ConfigGroup, ConfigField
from app.ui.settings.field_widget_factory import FieldWidgetFactory


class PluginDetailDialog(QDialog):
    """Dialog for configuring a service plugin"""
    
    config_saved = Signal(str)  # service_id
    
    def __init__(self, service_id: str, service_registry: ServiceRegistry, parent=None):
        super().__init__(parent)
        
        self.service_id = service_id
        self.service_registry = service_registry
        self.service_info = service_registry.get_service_info(service_id)
        self.config_manager = service_registry.get_config_manager()
        
        self.field_widgets: Dict[str, QWidget] = {}
        self.original_values: Dict[str, Any] = {}
        
        if not self.service_info:
            raise ValueError(f"Service not found: {service_id}")
        
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle(f"{self.service_info.name} Configuration")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header
        self._create_header(main_layout)
        
        # Create info section
        self._create_info_section(main_layout)
        
        # Create config form
        self._create_config_form(main_layout)
        
        # Create footer
        self._create_footer(main_layout)
        
        # Apply styling
        self._apply_style()
    
    def _create_header(self, parent_layout: QVBoxLayout):
        """Create dialog header"""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #252525; border-bottom: 1px solid #333333;")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Icon
        icon_label = QLabel(self.service_info.icon)
        icon_font = QFont()
        icon_font.setFamily("iconfont")
        icon_font.setPointSize(24)
        icon_label.setFont(icon_font)
        icon_label.setStyleSheet("color: #3498db; border: none;")
        layout.addWidget(icon_label)
        
        # Title
        title = QLabel(f"{self.service_info.name} Configuration")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet("color: #ffffff; border: none;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(40, 40)
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e74c3c;
                border-radius: 20px;
            }
        """)
        layout.addWidget(close_btn)
        
        parent_layout.addWidget(header)
    
    def _create_info_section(self, parent_layout: QVBoxLayout):
        """Create service information section"""
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #333333;")
        
        layout = QVBoxLayout(info_widget)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        
        # Service name
        name_label = QLabel(f"Service: {self.service_info.name}")
        name_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold; border: none;")
        layout.addWidget(name_label)
        
        # Version
        version_label = QLabel(f"Version: {self.service_info.version}")
        version_label.setStyleSheet("color: #95a5a6; font-size: 11px; border: none;")
        layout.addWidget(version_label)
        
        # Capabilities
        cap_names = [cap.display_name for cap in self.service_info.capabilities]
        cap_text = ", ".join(cap_names)
        cap_label = QLabel(f"Capabilities: {cap_text}")
        cap_label.setStyleSheet("color: #95a5a6; font-size: 11px; border: none;")
        cap_label.setWordWrap(True)
        layout.addWidget(cap_label)
        
        # Description
        if self.service_info.description:
            desc_label = QLabel(self.service_info.description)
            desc_label.setStyleSheet("color: #95a5a6; font-size: 11px; border: none;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        parent_layout.addWidget(info_widget)
    
    def _create_config_form(self, parent_layout: QVBoxLayout):
        """Create configuration form"""
        # Scroll area for form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
        """)
        
        # Form container
        form_container = QWidget()
        form_container.setStyleSheet("background-color: #1e1e1e;")
        container_layout = QVBoxLayout(form_container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(20)
        
        # Get config schema
        service_class = self.service_info.service_class
        config_schema = service_class.get_config_schema()
        
        # Create form for each config group
        for group in config_schema.groups:
            self._create_group_section(container_layout, group)
        
        container_layout.addStretch()
        
        scroll_area.setWidget(form_container)
        parent_layout.addWidget(scroll_area, 1)
    
    def _create_group_section(self, parent_layout: QVBoxLayout, group: ConfigGroup):
        """Create a configuration group section"""
        # Group frame
        group_frame = QFrame()
        group_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
            }
        """)
        
        group_layout = QVBoxLayout(group_frame)
        group_layout.setContentsMargins(15, 15, 15, 15)
        group_layout.setSpacing(12)
        
        # Group label
        group_label = QLabel(group.label)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        group_label.setFont(font)
        group_label.setStyleSheet("color: #ffffff; border: none;")
        group_layout.addWidget(group_label)
        
        # Form layout for fields
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setSpacing(10)
        
        # Add fields
        for field in group.fields:
            self._add_field_to_form(form_layout, group, field)
        
        group_layout.addLayout(form_layout)
        parent_layout.addWidget(group_frame)
    
    def _add_field_to_form(self, form_layout: QFormLayout, group: ConfigGroup, field: ConfigField):
        """Add a field to the form"""
        # Create label
        label_text = field.label
        if field.required:
            label_text += " *"
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #ffffff; font-size: 11px;")
        label.setToolTip(field.description)
        
        # Get current value
        key = f"{group.name}.{field.name}"
        config = self.config_manager.get_config(self.service_id) or {}
        group_config = config.get(group.name, {})
        current_value = group_config.get(field.name, field.default)
        
        # Create widget
        widget = FieldWidgetFactory.create_widget(field, current_value)
        widget.setFixedWidth(350)
        
        # Store widget reference
        self.field_widgets[key] = widget
        self.original_values[key] = current_value
        
        # Create container for widget and description
        widget_container = QWidget()
        widget_layout = QVBoxLayout(widget_container)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(4)
        
        widget_layout.addWidget(widget)
        
        # Add description
        if field.description:
            desc_label = QLabel(field.description)
            desc_label.setStyleSheet("color: #888888; font-size: 10px;")
            desc_label.setWordWrap(True)
            desc_label.setMaximumWidth(350)
            widget_layout.addWidget(desc_label)
        
        # Add to form
        form_layout.addRow(label, widget_container)
    
    def _create_footer(self, parent_layout: QVBoxLayout):
        """Create dialog footer with action buttons"""
        footer = QWidget()
        footer.setFixedHeight(60)
        footer.setStyleSheet("background-color: #252525; border-top: 1px solid #333333;")
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(12)
        
        layout.addStretch()
        
        # Test Connection button (if applicable)
        # For now, skip this feature
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 20px;
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        layout.addWidget(cancel_btn)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._on_save_clicked)
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 24px;
                background-color: #3498db;
                border: 1px solid #2980b9;
                border-radius: 4px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
        """)
        layout.addWidget(save_btn)
        
        parent_layout.addWidget(footer)
    
    def _apply_style(self):
        """Apply overall dialog style"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
        """)
    
    def _load_config(self):
        """Load current configuration values"""
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
                    self.original_values[key] = value
    
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
    
    def _on_save_clicked(self):
        """Handle save button click"""
        # Collect configuration from widgets
        service_class = self.service_info.service_class
        config_schema = service_class.get_config_schema()
        
        new_config = {}
        
        for group in config_schema.groups:
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
