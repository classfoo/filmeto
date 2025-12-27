"""
Workflow JSON Editor Dialog

Dialog for editing workflow JSON content directly.
"""

import json
from pathlib import Path
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QFont

from app.ui.dialog.custom_dialog import CustomDialog


class WorkflowJsonEditorDialog(CustomDialog):
    """Dialog for editing workflow JSON content"""
    
    def __init__(self, workflow_path: Path, parent=None):
        super().__init__(parent)
        
        self.workflow_path = workflow_path
        self.original_content = ""
        
        self._init_ui()
        self._load_workflow()
    
    def _init_ui(self):
        """Initialize the UI"""
        self.set_title("Edit Workflow JSON")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        # Content layout
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        
        # Header info
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        
        title_label = QLabel(f"Editing: {self.workflow_path.name}")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff; border: none;")
        header_layout.addWidget(title_label)
        
        info_label = QLabel("Edit the JSON content below. Make sure it's valid JSON format.")
        info_label.setStyleSheet("color: #888888; font-size: 11px; border: none;")
        header_layout.addWidget(info_label)
        
        content_layout.addWidget(header_widget)
        
        # JSON editor
        self.json_editor = QTextEdit()
        self.json_editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #ffffff;
                font-family: 'Courier New', 'Monaco', 'Consolas', monospace;
                font-size: 12px;
                padding: 12px;
            }
            QTextEdit:focus {
                border-color: #3498db;
            }
        """)
        content_layout.addWidget(self.json_editor, 1)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888888; font-size: 10px; border: none;")
        content_layout.addWidget(self.status_label)
        
        self.setContentLayout(content_layout)
        
        # Buttons
        self.add_button("Cancel", self.reject, "reject")
        self.add_button("Save", self._on_save, "accept")
    
    def _load_workflow(self):
        """Load workflow content"""
        try:
            if self.workflow_path.exists():
                with open(self.workflow_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.original_content = content
                    
                    # Try to parse and format JSON
                    try:
                        data = json.loads(content)
                        formatted = json.dumps(data, indent=2, ensure_ascii=False)
                        self.json_editor.setPlainText(formatted)
                        self.status_label.setText("✓ Valid JSON format")
                        self.status_label.setStyleSheet("color: #27ae60; font-size: 10px; border: none;")
                    except json.JSONDecodeError:
                        # Not valid JSON, show as-is
                        self.json_editor.setPlainText(content)
                        self.status_label.setText("⚠ Invalid JSON format - please fix")
                        self.status_label.setStyleSheet("color: #e74c3c; font-size: 10px; border: none;")
            else:
                # Create empty workflow
                empty_workflow = {
                    "prompt": {},
                    "extra": {}
                }
                formatted = json.dumps(empty_workflow, indent=2, ensure_ascii=False)
                self.json_editor.setPlainText(formatted)
                self.status_label.setText("New workflow - empty template")
                self.status_label.setStyleSheet("color: #f39c12; font-size: 10px; border: none;")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load workflow file:\n{str(e)}"
            )
            self.reject()
    
    def _validate_json(self) -> tuple[bool, str]:
        """Validate JSON content"""
        content = self.json_editor.toPlainText().strip()
        if not content:
            return False, "JSON content cannot be empty"
        
        try:
            json.loads(content)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
    
    def _on_save(self):
        """Handle save button click"""
        # Validate JSON
        is_valid, error_msg = self._validate_json()
        if not is_valid:
            QMessageBox.warning(
                self,
                "Validation Error",
                f"Please fix JSON errors before saving:\n\n{error_msg}"
            )
            return
        
        # Save workflow
        try:
            content = self.json_editor.toPlainText().strip()
            
            # Ensure directory exists
            self.workflow_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(self.workflow_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            QMessageBox.information(
                self,
                "Success",
                f"Workflow '{self.workflow_path.name}' saved successfully!"
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save workflow file:\n{str(e)}"
            )

