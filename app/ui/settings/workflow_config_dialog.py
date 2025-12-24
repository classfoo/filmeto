"""
Workflow Configuration Dialog

Dialog for configuring ComfyUI workflow node mappings.
Parses workflow JSON and allows selection of input, prompt, and output nodes.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFormLayout, QLineEdit, QComboBox, QTextEdit,
    QMessageBox, QFrame, QScrollArea, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor


class WorkflowConfigDialog(QDialog):
    """Dialog for configuring workflow node mappings"""
    
    def __init__(self, workflow_path: str, workflows_dir: Path, parent=None, existing_config: Optional[Dict] = None):
        super().__init__(parent)
        
        self.workflow_path = Path(workflow_path)
        self.workflows_dir = workflows_dir
        self.existing_config = existing_config
        self.workflow_data = None
        self.nodes = []
        
        self._load_workflow()
        self._init_ui()
        
        if existing_config:
            self._load_existing_config()
    
    def _load_workflow(self):
        """Load and parse workflow JSON"""
        try:
            with open(self.workflow_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Try to parse as JSON
                self.workflow_data = json.loads(content)
                
                # Extract nodes from workflow
                if isinstance(self.workflow_data, dict):
                    # Check for 'prompt' key (ComfyUI format)
                    if 'prompt' in self.workflow_data:
                        prompt_data = self.workflow_data['prompt']
                        if isinstance(prompt_data, dict):
                            self.nodes = [
                                {
                                    'id': node_id,
                                    'class_type': node_data.get('class_type', 'Unknown'),
                                    'inputs': node_data.get('inputs', {})
                                }
                                for node_id, node_data in prompt_data.items()
                            ]
                    else:
                        # Direct node format
                        self.nodes = [
                            {
                                'id': node_id,
                                'class_type': node_data.get('class_type', 'Unknown'),
                                'inputs': node_data.get('inputs', {})
                            }
                            for node_id, node_data in self.workflow_data.items()
                            if isinstance(node_data, dict)
                        ]
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Parse Error",
                f"Failed to parse workflow file:\n{str(e)}"
            )
            self.workflow_data = None
            self.nodes = []
    
    def _init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Configure Workflow")
        self.setMinimumSize(700, 800)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { background-color: #1e1e1e; border: none; }")
        
        # Content container
        content = QWidget()
        content.setStyleSheet("background-color: #1e1e1e;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(20)
        
        # Basic info section
        basic_info = self._create_basic_info_section()
        content_layout.addWidget(basic_info)
        
        # Node mapping section
        node_mapping = self._create_node_mapping_section()
        content_layout.addWidget(node_mapping)
        
        # Workflow preview section
        preview = self._create_preview_section()
        content_layout.addWidget(preview)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content)
        main_layout.addWidget(scroll_area, 1)
        
        # Footer
        footer = self._create_footer()
        main_layout.addWidget(footer)
        
        # Apply styling
        self._apply_style()
    
    def _create_header(self) -> QWidget:
        """Create dialog header"""
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: #252525; border-bottom: 1px solid #3a3a3a;")
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(4)
        
        # Title
        title = QLabel("Configure Workflow")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff; border: none;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel(f"File: {self.workflow_path.name}")
        subtitle.setStyleSheet("color: #888888; font-size: 11px; border: none;")
        layout.addWidget(subtitle)
        
        return header
    
    def _create_basic_info_section(self) -> QWidget:
        """Create basic information section"""
        group = QGroupBox("Basic Information")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
                font-size: 13px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        
        layout = QFormLayout(group)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Workflow name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter workflow name")
        self.name_input.setText(self.workflow_path.stem)
        self.name_input.setStyleSheet(self._get_input_style())
        layout.addRow(self._create_label("Name *"), self.name_input)
        
        # Description
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Enter workflow description")
        self.desc_input.setStyleSheet(self._get_input_style())
        layout.addRow(self._create_label("Description"), self.desc_input)
        
        # Tool type
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "text2image",
            "image_edit",
            "image2video",
            "video_edit",
            "upscale",
            "style_transfer",
            "custom"
        ])
        self.type_combo.setStyleSheet(self._get_combo_style())
        layout.addRow(self._create_label("Tool Type *"), self.type_combo)
        
        return group
    
    def _create_node_mapping_section(self) -> QWidget:
        """Create node mapping section"""
        group = QGroupBox("Node Mapping")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
                font-size: 13px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        
        layout = QFormLayout(group)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Create node options
        node_options = ["None"] + [f"{node['id']} - {node['class_type']}" for node in self.nodes]
        
        # Input node
        self.input_node_combo = QComboBox()
        self.input_node_combo.addItems(node_options)
        self.input_node_combo.setStyleSheet(self._get_combo_style())
        layout.addRow(
            self._create_label("Input Node"),
            self._create_field_with_hint(
                self.input_node_combo,
                "Node that receives input images/videos"
            )
        )
        
        # Prompt node
        self.prompt_node_combo = QComboBox()
        self.prompt_node_combo.addItems(node_options)
        self.prompt_node_combo.setStyleSheet(self._get_combo_style())
        layout.addRow(
            self._create_label("Prompt Node *"),
            self._create_field_with_hint(
                self.prompt_node_combo,
                "Node that receives text prompts"
            )
        )
        
        # Output node
        self.output_node_combo = QComboBox()
        self.output_node_combo.addItems(node_options)
        self.output_node_combo.setStyleSheet(self._get_combo_style())
        layout.addRow(
            self._create_label("Output Node *"),
            self._create_field_with_hint(
                self.output_node_combo,
                "Node that produces final output"
            )
        )
        
        # Seed node (optional)
        self.seed_node_combo = QComboBox()
        self.seed_node_combo.addItems(node_options)
        self.seed_node_combo.setStyleSheet(self._get_combo_style())
        layout.addRow(
            self._create_label("Seed Node"),
            self._create_field_with_hint(
                self.seed_node_combo,
                "Node that controls random seed (optional)"
            )
        )
        
        return group
    
    def _create_preview_section(self) -> QWidget:
        """Create workflow preview section"""
        group = QGroupBox("Workflow Preview")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
                font-size: 13px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Info label
        info_label = QLabel(f"Found {len(self.nodes)} nodes in workflow")
        info_label.setStyleSheet("color: #cccccc; font-size: 11px; font-weight: normal;")
        layout.addWidget(info_label)
        
        # Preview text
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #cccccc;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                padding: 8px;
            }
        """)
        
        # Show node list
        node_list = "\n".join([
            f"Node {node['id']}: {node['class_type']}"
            for node in self.nodes[:20]  # Limit to first 20
        ])
        if len(self.nodes) > 20:
            node_list += f"\n... and {len(self.nodes) - 20} more nodes"
        
        self.preview_text.setPlainText(node_list)
        layout.addWidget(self.preview_text)
        
        return group
    
    def _create_footer(self) -> QWidget:
        """Create dialog footer"""
        footer = QWidget()
        footer.setFixedHeight(70)
        footer.setStyleSheet("background-color: #252525; border-top: 1px solid #3a3a3a;")
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(12)
        
        layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 24px;
                background-color: #555555;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)
        layout.addWidget(cancel_btn)
        
        # Save button
        save_btn = QPushButton("Save Workflow")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._on_save)
        save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 24px;
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
        
        return footer
    
    def _create_label(self, text: str) -> QLabel:
        """Create a form label"""
        label = QLabel(text)
        label.setStyleSheet("color: #cccccc; font-size: 12px; font-weight: normal;")
        return label
    
    def _create_field_with_hint(self, widget: QWidget, hint: str) -> QWidget:
        """Create field container with hint"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        layout.addWidget(widget)
        
        hint_label = QLabel(hint)
        hint_label.setStyleSheet("color: #666666; font-size: 10px; font-weight: normal;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        
        return container
    
    def _get_input_style(self) -> str:
        """Get input field stylesheet"""
        return """
            QLineEdit {
                padding: 8px 12px;
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """
    
    def _get_combo_style(self) -> str:
        """Get combobox stylesheet"""
        return """
            QComboBox {
                padding: 8px 12px;
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #ffffff;
                font-size: 12px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #cccccc;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                selection-background-color: #3498db;
                color: #ffffff;
            }
        """
    
    def _apply_style(self):
        """Apply overall dialog style"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
        """)
    
    def _load_existing_config(self):
        """Load existing workflow configuration"""
        if not self.existing_config:
            return
        
        # Load basic info
        self.name_input.setText(self.existing_config.get('name', ''))
        self.desc_input.setText(self.existing_config.get('description', ''))
        
        # Load type
        tool_type = self.existing_config.get('type', 'text2image')
        index = self.type_combo.findText(tool_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        
        # Load node mappings
        node_mapping = self.existing_config.get('node_mapping', {})
        
        if 'input_node' in node_mapping:
            self._select_node_in_combo(self.input_node_combo, node_mapping['input_node'])
        
        if 'prompt_node' in node_mapping:
            self._select_node_in_combo(self.prompt_node_combo, node_mapping['prompt_node'])
        
        if 'output_node' in node_mapping:
            self._select_node_in_combo(self.output_node_combo, node_mapping['output_node'])
        
        if 'seed_node' in node_mapping:
            self._select_node_in_combo(self.seed_node_combo, node_mapping['seed_node'])
    
    def _select_node_in_combo(self, combo: QComboBox, node_id: str):
        """Select node in combobox by ID"""
        for i in range(combo.count()):
            text = combo.itemText(i)
            if text.startswith(f"{node_id} -"):
                combo.setCurrentIndex(i)
                break
    
    def _extract_node_id(self, combo_text: str) -> Optional[str]:
        """Extract node ID from combo text"""
        if combo_text == "None" or not combo_text:
            return None
        
        # Format: "node_id - class_type"
        parts = combo_text.split(" - ")
        if parts:
            return parts[0].strip()
        return None
    
    def _on_save(self):
        """Handle save button click"""
        # Validate required fields
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a workflow name.")
            return
        
        prompt_node = self._extract_node_id(self.prompt_node_combo.currentText())
        output_node = self._extract_node_id(self.output_node_combo.currentText())
        
        if not prompt_node or not output_node:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select both prompt node and output node."
            )
            return
        
        # Collect configuration
        config = {
            'name': name,
            'description': self.desc_input.text().strip(),
            'type': self.type_combo.currentText(),
            'file': f"{name.replace(' ', '_').lower()}_workflow.json",
            'node_mapping': {
                'prompt_node': prompt_node,
                'output_node': output_node
            }
        }
        
        # Optional nodes
        input_node = self._extract_node_id(self.input_node_combo.currentText())
        if input_node:
            config['node_mapping']['input_node'] = input_node
        
        seed_node = self._extract_node_id(self.seed_node_combo.currentText())
        if seed_node:
            config['node_mapping']['seed_node'] = seed_node
        
        # Save workflow file
        try:
            safe_name = name.replace(' ', '_').lower()
            
            # Copy original workflow to workflows directory
            workflow_file = self.workflows_dir / f"{safe_name}_workflow.json"
            
            # If this is a new workflow, copy the file
            if not self.existing_config or self.workflow_path != workflow_file:
                import shutil
                shutil.copy2(self.workflow_path, workflow_file)
            
            # Create a single combined metadata+workflow reference file
            # This matches what the ComfyUIConfigDialog expects
            combined_file = self.workflows_dir / f"{safe_name}.json"
            with open(combined_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            QMessageBox.information(
                self,
                "Success",
                f"Workflow '{name}' saved successfully!"
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save workflow:\n{str(e)}"
            )

