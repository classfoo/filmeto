"""Chat history panel for viewing conversation history."""

from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QListWidget, QListWidgetItem, 
    QHBoxLayout, QPushButton, QWidget
)
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
        self.set_panel_title(tr("History"))
        self.add_toolbar_button("↻", self._on_refresh, tr("刷新"))
        
        # Container for content
        content_container = QWidget()
        layout = QVBoxLayout(content_container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
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
        
        self.content_layout.addWidget(content_container)
    
    def load_data(self):
        """Load conversation history when panel is first activated."""
        super().load_data()
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
        # Refresh conversations when panel is activated (if data already loaded)
        if self._data_loaded:
            self._load_conversations()
        print("✅ Chat history panel activated")
    
    def on_deactivated(self):
        """Called when panel is hidden."""
        super().on_deactivated()
        print("⏸️ Chat history panel deactivated")

