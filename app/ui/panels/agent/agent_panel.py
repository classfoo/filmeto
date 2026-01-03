"""Agent panel for AI Agent interactions."""

from PySide6.QtWidgets import QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from app.ui.panels.base_panel import BasePanel
from app.data.workspace import Workspace
from utils.i18n_utils import tr


class AgentPanel(BasePanel):
    """Panel for AI Agent interactions."""
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the agent panel."""
        super().__init__(workspace, parent)
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header_label = QLabel(tr("Agent"), self)
        header_label.setObjectName("panel_header_label")
        header_label.setStyleSheet("""
            QLabel#panel_header_label {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        layout.addWidget(header_label)
        
        # Chat area
        self.chat_history = QTextEdit(self)
        self.chat_history.setObjectName("agent_chat_history")
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit#agent_chat_history {
                background-color: #1e1f22;
                color: #e1e1e1;
                border: 1px solid #505254;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        self.chat_history.setPlaceholderText(tr("对话历史将显示在这里..."))
        layout.addWidget(self.chat_history, 1)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)
        
        self.input_text = QTextEdit(self)
        self.input_text.setObjectName("agent_input_text")
        self.input_text.setMaximumHeight(80)
        self.input_text.setStyleSheet("""
            QTextEdit#agent_input_text {
                background-color: #2b2d30;
                color: #e1e1e1;
                border: 1px solid #505254;
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
            }
            QTextEdit#agent_input_text:focus {
                border: 1px solid #005a9e;
            }
        """)
        self.input_text.setPlaceholderText(tr("输入消息..."))
        input_layout.addWidget(self.input_text, 1)
        
        self.send_button = QPushButton(tr("发送"), self)
        self.send_button.setFixedWidth(60)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #005a9e;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #0066b3;
            }
            QPushButton:pressed {
                background-color: #004d85;
            }
        """)
        self.send_button.clicked.connect(self._on_send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
    
    def _on_send_message(self):
        """Handle send message button click."""
        message = self.input_text.toPlainText().strip()
        if not message:
            return
        
        # Add message to chat history
        self.chat_history.append(f"<b>{tr('用户')}:</b> {message}")
        self.input_text.clear()
        
        # TODO: Send to agent and get response
        # For now, just echo back
        self.chat_history.append(f"<b>{tr('Agent')}:</b> {tr('收到消息: {}').format(message)}")
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        print("✅ Agent panel activated")
    
    def on_deactivated(self):
        """Called when panel is hidden."""
        super().on_deactivated()
        print("⏸️ Agent panel deactivated")

