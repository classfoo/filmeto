"""Prompt input component for agent panel."""

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from app.ui.base_widget import BaseWidget
from app.data.workspace import Workspace
from utils.i18n_utils import tr


class AgentPromptInputWidget(BaseWidget):
    """Prompt input component for agent interactions."""
    
    # Signals
    message_submitted = Signal(str)  # Emitted when message is submitted
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the prompt input widget."""
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Header label
        header_label = QLabel(tr("输入消息"), self)
        header_label.setObjectName("prompt_input_header")
        header_label.setStyleSheet("""
            QLabel#prompt_input_header {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        layout.addWidget(header_label)
        
        # Input area with horizontal layout
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(5)
        
        # Text input field
        self.input_text = QTextEdit(self)
        self.input_text.setObjectName("agent_input_text")
        self.input_text.setMinimumHeight(60)
        self.input_text.setMaximumHeight(120)
        self.input_text.setStyleSheet("""
            QTextEdit#agent_input_text {
                background-color: #2b2d30;
                color: #e1e1e1;
                border: 1px solid #505254;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
            QTextEdit#agent_input_text:focus {
                border: 1px solid #005a9e;
            }
        """)
        self.input_text.setPlaceholderText(tr("输入消息..."))
        self.input_text.installEventFilter(self)
        input_layout.addWidget(self.input_text, 1)
        
        # Send button
        self.send_button = QPushButton(tr("发送"), self)
        self.send_button.setObjectName("agent_send_button")
        self.send_button.setFixedWidth(70)
        self.send_button.setFixedHeight(60)
        self.send_button.setStyleSheet("""
            QPushButton#agent_send_button {
                background-color: #005a9e;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#agent_send_button:hover {
                background-color: #0066b3;
            }
            QPushButton#agent_send_button:pressed {
                background-color: #004d85;
            }
            QPushButton#agent_send_button:disabled {
                background-color: #3d3f42;
                color: #6d6f72;
            }
        """)
        self.send_button.clicked.connect(self._on_send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
    
    def eventFilter(self, obj, event):
        """Handle keyboard events for the input text field."""
        if obj == self.input_text and event.type() == QKeyEvent.KeyPress:
            # Ctrl+Enter or Cmd+Enter to send message
            if (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter):
                modifiers = event.modifiers()
                if modifiers & Qt.ControlModifier or modifiers & Qt.MetaModifier:
                    self._on_send_message()
                    return True
        return super().eventFilter(obj, event)
    
    def _on_send_message(self):
        """Handle send message button click."""
        message = self.input_text.toPlainText().strip()
        if not message:
            return
        
        # Emit signal with message
        self.message_submitted.emit(message)
        
        # Clear input
        self.input_text.clear()
    
    def get_text(self) -> str:
        """Get the current input text."""
        return self.input_text.toPlainText()
    
    def set_text(self, text: str):
        """Set the input text."""
        self.input_text.setPlainText(text)
    
    def clear(self):
        """Clear the input field."""
        self.input_text.clear()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the input widget."""
        self.input_text.setEnabled(enabled)
        self.send_button.setEnabled(enabled)

