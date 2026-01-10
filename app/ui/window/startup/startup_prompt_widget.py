# -*- coding: utf-8 -*-
"""
Startup Prompt Widget

This widget provides a prompt input with context management for the startup mode.
It uses AgentPromptWidget for prompt input and context management, and adds model selection.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QComboBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from app.ui.prompt.agent_prompt_widget import AgentPromptWidget
from utils.i18n_utils import tr


class StartupPromptWidget(BaseWidget):
    """
    Prompt input widget for startup mode.
    
    Uses AgentPromptWidget for prompt input and context management,
    and adds model selection functionality.
    """
    
    prompt_submitted = Signal(str, list, str)  # prompt, contexts, model
    
    def __init__(self, workspace: Workspace, parent=None):
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        
        self.setObjectName("startup_prompt_widget")
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container frame for styling
        container = QFrame()
        container.setObjectName("prompt_container")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(12, 8, 12, 8)
        container_layout.setSpacing(8)
        
        # Use AgentPromptWidget for prompt input and context management
        self.prompt_widget = AgentPromptWidget(self.workspace)
        self.prompt_widget.set_placeholder(tr("请输入您的需求或问题..."))
        self.prompt_widget.prompt_submitted.connect(self._on_prompt_submitted)
        # Connect add context button to handle file selection
        self.prompt_widget.add_context_requested.connect(self._on_add_context)
        container_layout.addWidget(self.prompt_widget)
        
        # Bottom: Model selection
        bottom_area = QWidget()
        bottom_layout = QHBoxLayout(bottom_area)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)
        
        # Model selection
        model_label = QLabel(tr("模型:"))
        model_label.setStyleSheet("color: #888888; font-size: 12px;")
        bottom_layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setFixedWidth(150)
        self._load_models()
        bottom_layout.addWidget(self.model_combo)
        
        bottom_layout.addStretch()
        
        container_layout.addWidget(bottom_area)
        
        main_layout.addWidget(container)
    
    def _apply_styles(self):
        """Apply styles to the widget."""
        self.setStyleSheet("""
            QWidget#startup_prompt_widget {
                background-color: transparent;
            }
            QFrame#prompt_container {
                background-color: #2d2d2d;
                border: 1px solid #3c3f41;
                border-radius: 8px;
            }
            QComboBox {
                background-color: #3c3f41;
                border: none;
                border-radius: 4px;
                color: #E1E1E1;
                padding: 4px 8px;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3f41;
                border: 1px solid #505254;
                selection-background-color: #4c5052;
            }
        """)
    
    def _load_models(self):
        """Load available models into the combo box."""
        # Get models from settings or use defaults
        models = [
            "gpt-4o",
            "gpt-4o-mini",
            "claude-3-5-sonnet",
            "claude-3-haiku",
        ]
        self.model_combo.clear()
        for model in models:
            self.model_combo.addItem(model)
    
    def _on_add_context(self):
        """Handle add context button click from AgentPromptWidget."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("选择文件"),
            "",
            tr("所有文件 (*.*)")
        )
        
        if file_path:
            # Use file name as context ID and name
            name = file_path.split('/')[-1]
            # Add context item to AgentPromptWidget
            self.prompt_widget.add_context_item(name, name)
    
    def _on_prompt_submitted(self, prompt: str):
        """Handle prompt submission from AgentPromptWidget."""
        model = self.model_combo.currentText()
        # Get context items from AgentPromptWidget
        context_ids = self.prompt_widget.get_context_items()
        # Convert to list format expected by signal
        contexts = [{"id": ctx_id, "name": ctx_id} for ctx_id in context_ids]
        
        self.prompt_submitted.emit(prompt, contexts, model)
    
    def clear(self):
        """Clear the prompt and contexts."""
        self.prompt_widget.clear()
        self.prompt_widget.clear_context_items()
    
    def get_prompt(self) -> str:
        """Get the current prompt text."""
        return self.prompt_widget.get_text()
    
    def get_contexts(self) -> list:
        """Get the current context items."""
        context_ids = self.prompt_widget.get_context_items()
        return [{"id": ctx_id, "name": ctx_id} for ctx_id in context_ids]
    
    def get_model(self) -> str:
        """Get the selected model."""
        return self.model_combo.currentText()
