"""Chat history panel for viewing conversation history."""

from PySide6.QtWidgets import QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
from app.ui.panels.base_panel import BasePanel
from app.data.workspace import Workspace
from utils.i18n_utils import tr


class ChatHistoryPanel(BasePanel):
    """Panel for viewing chat conversation history."""
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the chat history panel."""
        super().__init__(workspace, parent)
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header with actions
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        header_label = QLabel(tr("对话历史"), self)
        header_label.setObjectName("panel_header_label")
        header_label.setStyleSheet("""
            QLabel#panel_header_label {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        self.refresh_button = QPushButton(tr("刷新"), self)
        self.refresh_button.setFixedWidth(60)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3f4e;
                color: #e1e1e1;
                border: 1px solid #505254;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4d4f5e;
            }
            QPushButton:pressed {
                background-color: #2d2f3e;
            }
        """)
        self.refresh_button.clicked.connect(self._on_refresh)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Conversation list
        self.conversation_list = QListWidget(self)
        self.conversation_list.setObjectName("chat_history_list")
        self.conversation_list.setStyleSheet("""
            QListWidget#chat_history_list {
                background-color: #1e1f22;
                color: #e1e1e1;
                border: 1px solid #505254;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget#chat_history_list::item {
                padding: 8px;
                border-bottom: 1px solid #323436;
            }
            QListWidget#chat_history_list::item:hover {
                background-color: #2b2d30;
            }
            QListWidget#chat_history_list::item:selected {
                background-color: #005a9e;
            }
        """)
        layout.addWidget(self.conversation_list, 1)
        
        # Load sample conversations
        self._load_conversations()
    
    def _load_conversations(self):
        """Load conversation history."""
        # TODO: Load actual conversation history from workspace/project
        # For now, add sample items
        sample_conversations = [
            tr("对话 1"),
            tr("对话 2"),
            tr("对话 3"),
        ]
        
        self.conversation_list.clear()
        for conv in sample_conversations:
            item = QListWidgetItem(conv)
            self.conversation_list.addItem(item)
    
    def _on_refresh(self):
        """Handle refresh button click."""
        self._load_conversations()
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        self._load_conversations()
        print("✅ Chat history panel activated")
    
    def on_deactivated(self):
        """Called when panel is hidden."""
        super().on_deactivated()
        print("⏸️ Chat history panel deactivated")

