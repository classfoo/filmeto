"""Agent panel for AI Agent interactions."""

from PySide6.QtWidgets import QVBoxLayout, QLabel
from app.ui.panels.base_panel import BasePanel
from app.data.workspace import Workspace
from app.ui.panels.agent.chat_history_widget import ChatHistoryWidget
from app.ui.panels.agent.prompt_input_widget import AgentPromptInputWidget
from utils.i18n_utils import tr


class AgentPanel(BasePanel):
    """Panel for AI Agent interactions."""
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the agent panel."""
        super().__init__(workspace, parent)
    
    def setup_ui(self):
        """Set up the UI components with vertical layout."""
        # Main vertical layout
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
        
        # Chat history component (top, takes most space)
        self.chat_history_widget = ChatHistoryWidget(self.workspace, self)
        layout.addWidget(self.chat_history_widget, 1)  # Stretch factor 1
        
        # Prompt input component (bottom, fixed height)
        self.prompt_input_widget = AgentPromptInputWidget(self.workspace, self)
        layout.addWidget(self.prompt_input_widget, 0)  # No stretch
        
        # Connect signals
        self.prompt_input_widget.message_submitted.connect(self._on_message_submitted)
    
    def _on_message_submitted(self, message: str):
        """Handle message submission from prompt input widget."""
        if not message:
            return
        
        # Add user message to chat history
        self.chat_history_widget.append_message(tr("用户"), message)
        
        # TODO: Send to agent and get response
        # For now, just echo back
        self.chat_history_widget.append_message(tr("Agent"), tr("收到消息: {}").format(message))
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        print("✅ Agent panel activated")
    
    def on_deactivated(self):
        """Called when panel is hidden."""
        super().on_deactivated()
        print("⏸️ Agent panel deactivated")

