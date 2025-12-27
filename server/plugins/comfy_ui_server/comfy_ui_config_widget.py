"""
ComfyUI Server Configuration Widget

Custom configuration UI for ComfyUI server with workflow management.
Designed to be embedded in the server_list dialog's ServerConfigView.
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QStackedWidget, QFrame,
    QScrollArea, QFormLayout, QLineEdit, QSpinBox, QCheckBox,
    QMessageBox, QFileDialog, QComboBox, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor


class ComfyUIConfigWidget(QWidget):
    """Custom configuration widget for ComfyUI server"""
    
    # Signal emitted when configuration changes
    config_changed = Signal()
    
    def __init__(self, workspace_path: str, server_config: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        
        self.workspace_path = workspace_path
        self.server_config = server_config or {}
        self.server_name = server_config.get('name', '') if server_config else ''
        
        # Workflow storage path
        self.workflows_dir = Path(workspace_path) / "servers" / self.server_name / "workflows" if self.server_name else None
        if self.workflows_dir:
            self.workflows_dir.mkdir(parents=True, exist_ok=True)
        
        self.field_widgets: Dict[str, QWidget] = {}
        self.workflows = []
        
        self._init_ui()
        self._load_config()
        if self.workflows_dir:
            self._load_workflows()
    
    def _init_ui(self):
        """Initialize the UI with tab layout"""
        # Main layout - vertical to accommodate tabs at top
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3a3a3a;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 8px 16px;
                border: 1px solid #3a3a3a;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                color: #ffffff;
                border-bottom: 2px solid #1e1e1e;
                border-bottom-color: #1e1e1e;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3a3a3a;
            }
        """)

        # Create pages
        self.service_page = self._create_service_page()
        self.workflow_page = self._create_workflow_page()

        # Add tabs
        self.tab_widget.addTab(self.service_page, "⚙ Service")
        self.tab_widget.addTab(self.workflow_page, "⚡ Workflows")

        main_layout.addWidget(self.tab_widget)
    
    
    def _create_service_page(self) -> QWidget:
        """Create service configuration page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 5, 10, 5)  # Reduced margins from 20,10,20,10 to 10,5,10,5
        layout.setSpacing(8)

        # Scroll area for form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { background-color: #1e1e1e; border: none; }")

        # Form container
        form_container = QWidget()
        form_container.setStyleSheet("background-color: #1e1e1e;")
        container_layout = QVBoxLayout(form_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)
        
        # Connection settings group
        conn_group = self._create_form_group("Connection Settings", [
            ("server_url", "Server URL", "text", "http://192.168.1.100", True, "ComfyUI server address"),
            ("port", "Port", "number", 3000, True, "ComfyUI server port"),
            ("timeout", "Timeout (seconds)", "number", 120, False, "Request timeout in seconds"),
            ("enable_ssl", "Enable SSL", "boolean", False, False, "Use HTTPS connection")
        ])
        container_layout.addWidget(conn_group)
        
        # Authentication group
        auth_group = self._create_form_group("Authentication", [
            ("api_key", "API Key", "password", "", False, "Optional API key for authentication")
        ])
        container_layout.addWidget(auth_group)
        
        # Performance group
        perf_group = self._create_form_group("Performance", [
            ("max_concurrent_jobs", "Max Concurrent Jobs", "number", 1, False, "Maximum number of concurrent jobs"),
            ("queue_timeout", "Queue Timeout (seconds)", "number", 3200, False, "Maximum time to wait in queue")
        ])
        container_layout.addWidget(perf_group)
        
        container_layout.addStretch()
        
        scroll_area.setWidget(form_container)
        layout.addWidget(scroll_area, 1)
        
        return page
    
    def _create_workflow_page(self) -> QWidget:
        """Create workflow management page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 5, 10, 5)  # Reduced margins from 20,10,20,10 to 10,5,10,5
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        add_btn = QPushButton("+ Add Workflow")
        add_btn.setFixedHeight(26)
        add_btn.clicked.connect(self._on_add_workflow)
        add_btn.setCursor(QCursor(Qt.PointingHandCursor))
        add_btn.setStyleSheet("""
            QPushButton {
                padding: 3px 10px;
                background-color: #3498db;
                border: none;
                border-radius: 3px;
                color: #ffffff;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
        """)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # Workflow list
        self.workflow_list = QListWidget()
        self.workflow_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 3px;
            }
            QListWidget::item {
                padding: 6px;
                margin: 2px 0;
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
                border-color: #3498db;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                border-color: #3498db;
                color: #ffffff;
            }
        """)
        self.workflow_list.itemDoubleClicked.connect(self._on_configure_workflow)
        layout.addWidget(self.workflow_list, 1)

        # Workflow actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)

        configure_btn = QPushButton("Configure")
        configure_btn.setFixedHeight(24)
        configure_btn.clicked.connect(self._on_configure_workflow)
        configure_btn.setCursor(QCursor(Qt.PointingHandCursor))
        configure_btn.setStyleSheet(self._get_action_button_style())
        actions_layout.addWidget(configure_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.setFixedHeight(24)
        remove_btn.clicked.connect(self._on_remove_workflow)
        remove_btn.setCursor(QCursor(Qt.PointingHandCursor))
        remove_btn.setStyleSheet(self._get_action_button_style("#e74c3c", "#c0392b"))
        actions_layout.addWidget(remove_btn)

        actions_layout.addStretch()

        layout.addLayout(actions_layout)

        return page
    
    def _create_form_group(self, title: str, fields: list) -> QWidget:
        """Create a form group widget"""
        group_frame = QFrame()
        group_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
            }
        """)

        group_layout = QVBoxLayout(group_frame)
        group_layout.setContentsMargins(10, 8, 10, 8)  # Reduced margins from 15,12,15,12 to 10,8,10,8
        group_layout.setSpacing(6)

        # Group label
        group_label = QLabel(title)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        group_label.setFont(font)
        group_label.setStyleSheet("color: #ffffff; border: none;")
        group_layout.addWidget(group_label)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.setSpacing(5)
        form_layout.setHorizontalSpacing(8)

        # Add fields
        for field_name, label, field_type, default, required, description in fields:
            self._add_field_to_form(form_layout, field_name, label, field_type, default, required, description)

        group_layout.addLayout(form_layout)

        return group_frame
    
    def _add_field_to_form(self, form_layout: QFormLayout, field_name: str, label: str, 
                           field_type: str, default: Any, required: bool, description: str):
        """Add a field to the form"""
        # Create label
        label_text = label + (" *" if required else "")
        label_widget = QLabel(label_text)
        label_widget.setStyleSheet("color: #cccccc; font-size: 11px;")
        label_widget.setToolTip(description)
        
        # Create widget based on type
        if field_type == "text":
            widget = QLineEdit()
            widget.setText(str(default))
            widget.setStyleSheet(self._get_input_style())
        elif field_type == "password":
            widget = QLineEdit()
            widget.setEchoMode(QLineEdit.Password)
            widget.setText(str(default))
            widget.setStyleSheet(self._get_input_style())
        elif field_type == "number":
            widget = QSpinBox()
            widget.setRange(0, 99999)
            widget.setValue(int(default))
            widget.setStyleSheet(self._get_input_style())
        elif field_type == "boolean":
            widget = QCheckBox()
            widget.setChecked(bool(default))
            widget.setStyleSheet("color: #ffffff;")
        else:
            widget = QLineEdit()
            widget.setText(str(default))
            widget.setStyleSheet(self._get_input_style())
        
        widget.setFixedWidth(240)

        # Store widget reference
        self.field_widgets[field_name] = widget

        # Create container
        widget_container = QWidget()
        widget_layout = QVBoxLayout(widget_container)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(2)

        widget_layout.addWidget(widget)

        # Add description
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #FFFFFF; font-size: 8px;")  # Reduced font size from 9px to 8px
            desc_label.setWordWrap(True)
            desc_label.setMaximumWidth(240)
            widget_layout.addWidget(desc_label)
        
        # Add to form
        form_layout.addRow(label_widget, widget_container)
        
        # Connect change signal
        if hasattr(widget, 'textChanged'):
            widget.textChanged.connect(lambda: self.config_changed.emit())
        elif hasattr(widget, 'valueChanged'):
            widget.valueChanged.connect(lambda: self.config_changed.emit())
        elif hasattr(widget, 'stateChanged'):
            widget.stateChanged.connect(lambda: self.config_changed.emit())
    
    def _get_input_style(self) -> str:
        """Get input field stylesheet"""
        return """
            QLineEdit, QSpinBox {
                padding: 4px 8px;
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                color: #ffffff;
                font-size: 10px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #3498db;
            }
        """
    
    def _get_action_button_style(self, bg_color: str = "#555555", hover_color: str = "#666666") -> str:
        """Get action button stylesheet"""
        return f"""
            QPushButton {{
                padding: 4px 10px;
                background-color: {bg_color};
                border: none;
                border-radius: 3px;
                color: #ffffff;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """
    
    def _load_config(self):
        """Load current configuration"""
        if not self.server_config:
            return
        
        config = self.server_config.get('config', {})
        
        for field_name, widget in self.field_widgets.items():
            value = config.get(field_name)
            if value is not None:
                if isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(value))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
    
    def _load_workflows(self):
        """Load workflows from workspace directory"""
        self.workflows = []
        self.workflow_list.clear()
        
        if not self.workflows_dir or not self.workflows_dir.exists():
            return
        
        # Load workflow metadata files
        for workflow_file in self.workflows_dir.glob("*.json"):
            if workflow_file.name.endswith('_workflow.json'):
                continue
            
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                    
                if "name" in workflow_data and "type" in workflow_data:
                    self.workflows.append(workflow_data)
                    
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
        if not self.workflows_dir:
            QMessageBox.warning(self, "No Server", "Please save the server configuration first.")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Workflow File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Import workflow configuration dialog
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
            from app.ui.settings.workflow_config_dialog import WorkflowConfigDialog
            
            dialog = WorkflowConfigDialog(file_path, self.workflows_dir, self)
            if dialog.exec() == dialog.Accepted:
                self._load_workflows()
                self.config_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open workflow configuration: {e}")
    
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
        
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
            from app.ui.settings.workflow_config_dialog import WorkflowConfigDialog
            
            dialog = WorkflowConfigDialog(str(workflow_file), self.workflows_dir, self, workflow_data)
            if dialog.exec() == dialog.Accepted:
                self._load_workflows()
                self.config_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open workflow configuration: {e}")
    
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
            
            # Remove metadata file
            safe_name = workflow_data['name'].replace(' ', '_').lower()
            metadata_file = self.workflows_dir / f"{safe_name}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            self._load_workflows()
            self.config_changed.emit()
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration from widgets"""
        config = {}
        
        for field_name, widget in self.field_widgets.items():
            if isinstance(widget, QLineEdit):
                config[field_name] = widget.text()
            elif isinstance(widget, QSpinBox):
                config[field_name] = widget.value()
            elif isinstance(widget, QCheckBox):
                config[field_name] = widget.isChecked()
        
        return config
    
    def validate_config(self) -> bool:
        """Validate current configuration"""
        config = self.get_config()
        
        # Check required fields
        if not config.get('server_url'):
            QMessageBox.warning(self, "Validation Error", "Server URL is required.")
            return False
        
        if not config.get('port'):
            QMessageBox.warning(self, "Validation Error", "Port is required.")
            return False
        
        return True

