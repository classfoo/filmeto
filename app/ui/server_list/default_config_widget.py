"""
Default configuration widget for plugins that don't implement custom init_ui.

This widget provides the standard form-based configuration UI that was
previously implemented in ServerConfigView._build_config_ui.
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QSpinBox, QFormLayout, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from utils.i18n_utils import tr


class DefaultConfigWidget(QWidget):
    """Default configuration widget for plugins."""
    
    # Signal emitted when configuration changes
    config_changed = Signal()

    def __init__(self, plugin_info, server_config=None, parent=None):
        super().__init__(parent)
        
        self.plugin_info = plugin_info
        self.server_config = server_config
        self.is_edit_mode = server_config is not None
        self.field_widgets = {}
        
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(16)

        # Scroll area for form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        
        # Form container
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(15)

        # Header
        header_label = QLabel(f"{tr('配置')} {self.plugin_info.name} {tr('服务器')}", self)
        header_font = QFont()
        header_font.setPointSize(13)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setStyleSheet("QLabel { color: #E1E1E1; }")
        form_layout.addWidget(header_label)

        # Description
        desc_label = QLabel(self.plugin_info.description or "", self)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("QLabel { color: #999999; font-size: 11px; }")
        form_layout.addWidget(desc_label)

        # Create form group frame
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
            }
        """)
        form_frame_layout = QVBoxLayout(form_frame)
        form_frame_layout.setContentsMargins(15, 12, 15, 12)
        form_frame_layout.setSpacing(10)

        # Form layout for fields
        fields_layout = QFormLayout()
        fields_layout.setSpacing(12)
        fields_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        fields_layout.setHorizontalSpacing(12)

        # Server name field
        self.name_field = QLineEdit(self)
        self.name_field.setPlaceholderText(tr("输入唯一的服务器名称"))
        self._style_line_edit(self.name_field)
        name_label = QLabel(tr("服务器名称") + " *", self)
        name_label.setStyleSheet("QLabel { color: #E1E1E1; }")
        fields_layout.addRow(name_label, self.name_field)

        # Pre-fill name if editing
        if self.is_edit_mode:
            self.name_field.setText(self.server_config.name)
            self.name_field.setEnabled(False)

        # Description field
        self.description_field = QLineEdit(self)
        self.description_field.setPlaceholderText(tr("输入服务器描述（可选）"))
        self._style_line_edit(self.description_field)
        desc_label = QLabel(tr("描述"), self)
        desc_label.setStyleSheet("QLabel { color: #E1E1E1; }")
        fields_layout.addRow(desc_label, self.description_field)

        # Pre-fill description if editing
        if self.is_edit_mode:
            self.description_field.setText(self.server_config.description or "")

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

            # Create widget
            widget = self._create_field_widget(field_type, default, placeholder)
            self.field_widgets[field_name] = {
                "widget": widget,
                "type": field_type,
                "required": required
            }

            # Pre-fill if editing
            if self.is_edit_mode:
                self._prefill_field(field_name, widget, field_type)

            # Connect change signal
            self._connect_widget_signal(widget)

            # Create label
            label_text = field_label
            if required:
                label_text += " *"
            label = QLabel(label_text, self)
            label.setStyleSheet("QLabel { color: #E1E1E1; }")
            if description:
                label.setToolTip(description)

            fields_layout.addRow(label, widget)

        form_frame_layout.addLayout(fields_layout)

        # Add form frame to layout
        form_layout.addWidget(form_frame)

        # Enabled checkbox
        self.enabled_checkbox = QCheckBox(tr("启用此服务器"), self)
        self.enabled_checkbox.setChecked(True if not self.is_edit_mode else self.server_config.enabled if self.server_config else True)
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
        # Connect checkbox change signal
        self.enabled_checkbox.stateChanged.connect(lambda: self.config_changed.emit())
        form_layout.addWidget(self.enabled_checkbox)

        # Add stretch to push content up
        form_layout.addStretch()

        scroll_area.setWidget(form_container)
        main_layout.addWidget(scroll_area)

    def _get_plugin_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema from plugin."""
        if hasattr(self.plugin_info, 'config') and 'config_schema' in self.plugin_info.config:
            return self.plugin_info.config['config_schema']

        # Default schema
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

    def _create_field_widget(self, field_type: str, default: Any, placeholder: str):
        """Create appropriate widget based on field type."""
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

        else:  # string, password, url
            widget = QLineEdit(self)
            if field_type == "password":
                widget.setEchoMode(QLineEdit.Password)
            if default:
                widget.setText(str(default))
            if placeholder:
                widget.setPlaceholderText(placeholder)
            self._style_line_edit(widget)
            return widget

    def _style_line_edit(self, widget: QLineEdit):
        """Apply consistent styling to line edit widgets."""
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

    def _connect_widget_signal(self, widget):
        """Connect appropriate signal for the widget to config_changed."""
        if hasattr(widget, 'textChanged'):
            widget.textChanged.connect(lambda: self.config_changed.emit())
        elif hasattr(widget, 'valueChanged'):
            widget.valueChanged.connect(lambda: self.config_changed.emit())
        elif hasattr(widget, 'stateChanged'):
            widget.stateChanged.connect(lambda: self.config_changed.emit())

    def _prefill_field(self, field_name: str, widget, field_type: str):
        """Pre-fill field with existing server config value."""
        if not self.server_config:
            return

        value = self.server_config.parameters.get(field_name)

        # Handle special fields
        if field_name == "endpoint" and self.server_config.endpoint:
            value = self.server_config.endpoint
        elif field_name == "api_key" and self.server_config.api_key:
            value = self.server_config.api_key

        if value is not None:
            if isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, QLineEdit):
                widget.setText(str(value))

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration from widgets."""
        config = {}

        # Get basic fields
        config['name'] = self.name_field.text().strip()
        config['description'] = self.description_field.text().strip()
        config['enabled'] = self.enabled_checkbox.isChecked()

        # Get plugin-specific fields
        for field_name, field_info in self.field_widgets.items():
            widget = field_info["widget"]

            if isinstance(widget, QCheckBox):
                config[field_name] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                config[field_name] = widget.value()
            elif isinstance(widget, QLineEdit):
                value = widget.text().strip()
                if value:  # Only add non-empty values
                    config[field_name] = value

        return config

    def validate_config(self) -> bool:
        """Validate the current configuration."""
        config = self.get_config()

        # Check required fields
        config_schema = self._get_plugin_config_schema()
        for field_config in config_schema.get("fields", []):
            field_name = field_config["name"]
            required = field_config.get("required", False)
            
            if required:
                value = config.get(field_name, "")
                if not value:
                    print(f"Field '{field_name}' is required but not provided")
                    return False

        return True