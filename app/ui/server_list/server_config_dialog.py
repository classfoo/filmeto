"""
Server Configuration Dialog

Dialog for configuring a new server instance based on plugin schema.
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QCheckBox, QSpinBox, QFormLayout,
    QWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from app.ui.dialog.custom_dialog import CustomDialog
from utils.i18n_utils import tr
from typing import Dict, Any, Optional


class ServerConfigDialog(CustomDialog):
    """
    Dialog for configuring a new server instance.
    
    This dialog is dynamically generated based on the plugin's configuration schema.
    """
    
    # Signal emitted when server is created (server_name, config)
    server_created = Signal(str, object)
    
    def __init__(self, plugin_info, parent=None):
        """
        Initialize server configuration dialog.
        
        Args:
            plugin_info: PluginInfo object containing plugin metadata
            parent: Parent widget
        """
        super().__init__(parent)
        self.plugin_info = plugin_info
        self.field_widgets = {}
        
        # Setup dialog
        self.set_title(tr("添加服务器") + f" - {plugin_info.name}")
        self.setMinimumSize(500, 400)
        
        # Initialize UI
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        
        # Header
        header_label = QLabel(f"{tr('配置')} {self.plugin_info.name} {tr('服务器')}", self)
        header_font = QFont()
        header_font.setPointSize(13)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setStyleSheet("QLabel { color: #E1E1E1; }")
        layout.addWidget(header_label)
        
        # Description
        desc_label = QLabel(self.plugin_info.description, self)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("QLabel { color: #999999; font-size: 11px; }")
        layout.addWidget(desc_label)
        
        # Form layout for configuration fields
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Server name field (always required)
        self.name_field = QLineEdit(self)
        self.name_field.setPlaceholderText(tr("输入唯一的服务器名称"))
        self._style_line_edit(self.name_field)
        name_label = QLabel(tr("服务器名称") + " *", self)
        name_label.setStyleSheet("QLabel { color: #E1E1E1; }")
        form_layout.addRow(name_label, self.name_field)
        
        # Description field
        self.description_field = QLineEdit(self)
        self.description_field.setPlaceholderText(tr("输入服务器描述（可选）"))
        self._style_line_edit(self.description_field)
        desc_label = QLabel(tr("描述"), self)
        desc_label.setStyleSheet("QLabel { color: #E1E1E1; }")
        form_layout.addRow(desc_label, self.description_field)
        
        # Get config schema from plugin
        config_schema = self._get_plugin_config_schema()
        
        # Create fields based on schema
        for field_config in config_schema.get("fields", []):
            field_name = field_config["name"]
            field_label = field_config.get("label", field_name)
            field_type = field_config.get("type", "string")
            required = field_config.get("required", False)
            default = field_config.get("default", "")
            placeholder = field_config.get("placeholder", "")
            description = field_config.get("description", "")
            
            # Create appropriate widget based on type
            widget = self._create_field_widget(field_type, default, placeholder)
            self.field_widgets[field_name] = {
                "widget": widget,
                "type": field_type,
                "required": required
            }
            
            # Create label
            label_text = field_label
            if required:
                label_text += " *"
            label = QLabel(label_text, self)
            label.setStyleSheet("QLabel { color: #E1E1E1; }")
            if description:
                label.setToolTip(description)
            
            form_layout.addRow(label, widget)
        
        layout.addLayout(form_layout)
        
        # Enabled checkbox
        self.enabled_checkbox = QCheckBox(tr("启用此服务器"), self)
        self.enabled_checkbox.setChecked(True)
        self.enabled_checkbox.setStyleSheet("""
            QCheckBox {
                color: #E1E1E1;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        layout.addWidget(self.enabled_checkbox)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton(tr("取消"), self)
        cancel_button.setFixedWidth(100)
        cancel_button.clicked.connect(self.reject)
        self._style_button(cancel_button, "#555555")
        button_layout.addWidget(cancel_button)
        
        create_button = QPushButton(tr("创建"), self)
        create_button.setFixedWidth(100)
        create_button.clicked.connect(self._on_create)
        self._style_button(create_button, "#4CAF50")
        button_layout.addWidget(create_button)
        
        layout.addLayout(button_layout)
        
        # Set the layout
        self.setContentLayout(layout)
    
    def _get_plugin_config_schema(self) -> Dict[str, Any]:
        """
        Get configuration schema from plugin.
        
        Returns:
            Configuration schema dictionary
        """
        # Try to get schema from plugin config
        if hasattr(self.plugin_info, 'config') and 'config_schema' in self.plugin_info.config:
            return self.plugin_info.config['config_schema']
        
        # Return default schema
        return {
            "fields": [
                {
                    "name": "endpoint",
                    "label": tr("端点URL"),
                    "type": "url",
                    "required": False,
                    "default": "",
                    "description": tr("服务端点URL（如适用）"),
                    "placeholder": "http://localhost:8188"
                },
                {
                    "name": "api_key",
                    "label": tr("API密钥"),
                    "type": "password",
                    "required": False,
                    "default": "",
                    "description": tr("用于身份验证的API密钥（如需要）"),
                    "placeholder": tr("输入API密钥")
                }
            ]
        }
    
    def _create_field_widget(self, field_type: str, default: Any, placeholder: str) -> QWidget:
        """
        Create appropriate widget based on field type.
        
        Args:
            field_type: Type of field (string, integer, boolean, password, url)
            default: Default value
            placeholder: Placeholder text
            
        Returns:
            Widget for the field
        """
        if field_type == "boolean":
            widget = QCheckBox(self)
            widget.setChecked(bool(default))
            widget.setStyleSheet("""
                QCheckBox {
                    color: #E1E1E1;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
            """)
            return widget
        
        elif field_type == "integer":
            widget = QSpinBox(self)
            widget.setMinimum(-999999)
            widget.setMaximum(999999)
            widget.setValue(int(default) if default else 0)
            widget.setStyleSheet("""
                QSpinBox {
                    background-color: #2b2b2b;
                    color: #E1E1E1;
                    border: 1px solid #3c3c3c;
                    border-radius: 4px;
                    padding: 6px;
                }
                QSpinBox:focus {
                    border: 1px solid #4CAF50;
                }
            """)
            return widget
        
        elif field_type in ["password", "url", "string"]:
            widget = QLineEdit(self)
            if field_type == "password":
                widget.setEchoMode(QLineEdit.Password)
            if default:
                widget.setText(str(default))
            if placeholder:
                widget.setPlaceholderText(placeholder)
            self._style_line_edit(widget)
            return widget
        
        else:
            # Default to line edit
            widget = QLineEdit(self)
            if default:
                widget.setText(str(default))
            if placeholder:
                widget.setPlaceholderText(placeholder)
            self._style_line_edit(widget)
            return widget
    
    def _style_line_edit(self, widget: QLineEdit):
        """Apply consistent styling to line edit widgets"""
        widget.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #E1E1E1;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """)
    
    def _style_button(self, button: QPushButton, color: str):
        """Apply consistent button styling"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color)};
            }}
        """)
    
    def _lighten_color(self, color: str) -> str:
        """Lighten a hex color"""
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r = min(255, r + 20)
        g = min(255, g + 20)
        b = min(255, b + 20)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _darken_color(self, color: str) -> str:
        """Darken a hex color"""
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r = max(0, r - 20)
        g = max(0, g - 20)
        b = max(0, b - 20)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _on_create(self):
        """Handle create button click"""
        # Validate required fields
        server_name = self.name_field.text().strip()
        if not server_name:
            QMessageBox.warning(self, tr("验证错误"), tr("请输入服务器名称"))
            return
        
        # Validate field values
        for field_name, field_info in self.field_widgets.items():
            widget = field_info["widget"]
            required = field_info["required"]
            
            # Get value based on widget type
            if isinstance(widget, QLineEdit):
                value = widget.text().strip()
                if required and not value:
                    QMessageBox.warning(
                        self,
                        tr("验证错误"),
                        f"{tr('字段')} '{field_name}' {tr('是必填的')}"
                    )
                    return
        
        # Build configuration
        from server.server import ServerConfig
        from datetime import datetime
        
        # Collect parameters
        parameters = {}
        for field_name, field_info in self.field_widgets.items():
            widget = field_info["widget"]
            field_type = field_info["type"]
            
            if isinstance(widget, QCheckBox):
                parameters[field_name] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                parameters[field_name] = widget.value()
            elif isinstance(widget, QLineEdit):
                value = widget.text().strip()
                if value:  # Only add non-empty values
                    parameters[field_name] = value
        
        # Create server config
        config = ServerConfig(
            name=server_name,
            server_type=self.plugin_info.engine or "custom",
            plugin_name=self.plugin_info.name,
            description=self.description_field.text().strip(),
            enabled=self.enabled_checkbox.isChecked(),
            endpoint=parameters.get("endpoint"),
            api_key=parameters.get("api_key"),
            parameters=parameters,
            metadata={
                "plugin_version": self.plugin_info.version,
                "created_via": "ui"
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Emit signal
        self.server_created.emit(server_name, config)
        
        # Close dialog
        self.accept()

