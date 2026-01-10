# -*- coding: utf-8 -*-
"""
Startup Prompt Widget

This widget provides a prompt input with context management for the startup mode.
It includes:
- Top: Context management (add button + flow layout for context cards)
- Middle: Prompt input area
- Bottom: Model selection and send button
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QTextEdit, QComboBox, QScrollArea,
    QFileDialog
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QCursor

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from app.ui.layout.flow_layout import FlowLayout
from utils.i18n_utils import tr


class ContextItemWidget(QFrame):
    """Widget representing a single context item (file, image, etc.)."""
    
    removed = Signal(object)  # Emits self when remove is clicked
    
    def __init__(self, name: str, context_type: str = "file", data: dict = None, parent=None):
        super().__init__(parent)
        self.name = name
        self.context_type = context_type
        self.data = data or {}
        
        self.setObjectName("context_item")
        self.setFixedHeight(28)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 4, 4)
        layout.setSpacing(4)
        
        # Icon based on type
        icon_map = {
            "file": "\ue6b0",
            "image": "\ue697",
            "text": "\ue6b1",
        }
        icon = icon_map.get(context_type, "\ue6b0")
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-family: iconfont; font-size: 12px; color: #888888;")
        layout.addWidget(icon_label)
        
        # Name label (truncate if too long)
        display_name = name if len(name) <= 20 else name[:17] + "..."
        name_label = QLabel(display_name)
        name_label.setStyleSheet("color: #E1E1E1; font-size: 12px;")
        name_label.setToolTip(name)
        layout.addWidget(name_label)
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(16, 16)
        remove_btn.setCursor(QCursor(Qt.PointingHandCursor))
        remove_btn.clicked.connect(lambda: self.removed.emit(self))
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #888888;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ff4444;
            }
        """)
        layout.addWidget(remove_btn)
        
        self.setStyleSheet("""
            QFrame#context_item {
                background-color: #3c3f41;
                border-radius: 4px;
            }
        """)


class StartupPromptWidget(BaseWidget):
    """
    Prompt input widget for startup mode with context management.
    """
    
    prompt_submitted = Signal(str, list, str)  # prompt, contexts, model
    
    def __init__(self, workspace: Workspace, parent=None):
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        
        self.setObjectName("startup_prompt_widget")
        self._contexts = []
        
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
        
        # Top: Context management area
        context_area = QWidget()
        context_layout = QVBoxLayout(context_area)
        context_layout.setContentsMargins(0, 0, 0, 0)
        context_layout.setSpacing(4)
        
        # Context header with add button
        context_header = QWidget()
        context_header_layout = QHBoxLayout(context_header)
        context_header_layout.setContentsMargins(0, 0, 0, 0)
        context_header_layout.setSpacing(8)
        
        context_label = QLabel(tr("上下文"))
        context_label.setStyleSheet("color: #888888; font-size: 12px;")
        context_header_layout.addWidget(context_label)
        
        self.add_context_btn = QPushButton("\ue6b3")  # Add icon
        self.add_context_btn.setFixedSize(20, 20)
        self.add_context_btn.setToolTip(tr("添加上下文"))
        self.add_context_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.add_context_btn.clicked.connect(self._on_add_context)
        self.add_context_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #888888;
                font-family: iconfont;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #4080ff;
            }
        """)
        context_header_layout.addWidget(self.add_context_btn)
        context_header_layout.addStretch()
        
        context_layout.addWidget(context_header)
        
        # Context items flow layout
        self.context_container = QWidget()
        self.context_flow_layout = FlowLayout(self.context_container, margin=0, spacing=6)
        self.context_container.setMinimumHeight(0)
        context_layout.addWidget(self.context_container)
        
        container_layout.addWidget(context_area)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #3c3f41;")
        separator.setFixedHeight(1)
        container_layout.addWidget(separator)
        
        # Middle: Prompt input area
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("prompt_text_edit")
        self.text_edit.setPlaceholderText(tr("请输入您的需求或问题..."))
        self.text_edit.setMinimumHeight(60)
        self.text_edit.setMaximumHeight(150)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container_layout.addWidget(self.text_edit)
        
        # Bottom: Model selection and send button
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
        
        # Send button
        self.send_button = QPushButton(tr("发送"))
        self.send_button.setFixedSize(80, 32)
        self.send_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_button.clicked.connect(self._on_send_clicked)
        bottom_layout.addWidget(self.send_button)
        
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
            QTextEdit#prompt_text_edit {
                background-color: #1e1f22;
                border: none;
                border-radius: 6px;
                color: #E1E1E1;
                padding: 8px;
                font-size: 14px;
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
            QPushButton#prompt_send_button {
                background-color: #4080ff;
                border: none;
                border-radius: 6px;
                color: #FFFFFF;
                font-size: 14px;
            }
            QPushButton#prompt_send_button:hover {
                background-color: #5090ff;
            }
            QPushButton#prompt_send_button:pressed {
                background-color: #3070ee;
            }
        """)
        
        self.send_button.setObjectName("prompt_send_button")
        self.send_button.setStyleSheet("""
            QPushButton#prompt_send_button {
                background-color: #4080ff;
                border: none;
                border-radius: 6px;
                color: #FFFFFF;
                font-size: 14px;
            }
            QPushButton#prompt_send_button:hover {
                background-color: #5090ff;
            }
            QPushButton#prompt_send_button:pressed {
                background-color: #3070ee;
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
        """Handle add context button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("选择文件"),
            "",
            tr("所有文件 (*.*)")
        )
        
        if file_path:
            # Determine file type
            ext = file_path.split('.')[-1].lower()
            if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']:
                context_type = "image"
            else:
                context_type = "file"
            
            name = file_path.split('/')[-1]
            self._add_context_item(name, context_type, {"path": file_path})
    
    def _add_context_item(self, name: str, context_type: str, data: dict):
        """Add a context item to the flow layout."""
        item = ContextItemWidget(name, context_type, data)
        item.removed.connect(self._on_context_removed)
        
        self._contexts.append({
            "name": name,
            "type": context_type,
            "data": data,
            "widget": item
        })
        
        self.context_flow_layout.addWidget(item)
        
        # Update container height
        self.context_container.setMinimumHeight(
            self.context_flow_layout.heightForWidth(self.context_container.width())
        )
    
    def _on_context_removed(self, item: ContextItemWidget):
        """Handle context item removal."""
        # Find and remove from contexts list
        for i, ctx in enumerate(self._contexts):
            if ctx.get("widget") == item:
                self._contexts.pop(i)
                break
        
        # Remove widget
        self.context_flow_layout.removeWidget(item)
        item.deleteLater()
        
        # Update container height
        self.context_container.setMinimumHeight(
            self.context_flow_layout.heightForWidth(self.context_container.width())
        )
    
    def _on_send_clicked(self):
        """Handle send button click."""
        prompt = self.text_edit.toPlainText().strip()
        if not prompt:
            return
        
        model = self.model_combo.currentText()
        contexts = [
            {"name": ctx["name"], "type": ctx["type"], "data": ctx["data"]}
            for ctx in self._contexts
        ]
        
        self.prompt_submitted.emit(prompt, contexts, model)
    
    def clear(self):
        """Clear the prompt and contexts."""
        self.text_edit.clear()
        
        # Clear all context items
        for ctx in self._contexts:
            widget = ctx.get("widget")
            if widget:
                widget.deleteLater()
        self._contexts.clear()
    
    def get_prompt(self) -> str:
        """Get the current prompt text."""
        return self.text_edit.toPlainText()
    
    def get_contexts(self) -> list:
        """Get the current context items."""
        return [
            {"name": ctx["name"], "type": ctx["type"], "data": ctx["data"]}
            for ctx in self._contexts
        ]
    
    def get_model(self) -> str:
        """Get the selected model."""
        return self.model_combo.currentText()
