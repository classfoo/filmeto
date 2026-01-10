"""Prompt input component for agent panel."""

from PySide6.QtCore import Signal
from app.ui.base_widget import BaseWidget
from app.data.workspace import Workspace
from app.ui.prompt.agent_prompt_widget import AgentPromptWidget
from utils.i18n_utils import tr


class AgentPromptInputWidget(AgentPromptWidget):
    """
    Prompt input component for agent interactions.
    
    This is essentially an alias for AgentPromptWidget to maintain backward compatibility.
    The actual implementation is in AgentPromptWidget.
    """
    
    # Signals (redefined for clarity, but inherited from AgentPromptWidget)
    message_submitted = Signal(str)  # Emitted when message is submitted (alias for prompt_submitted)
    add_context_requested = Signal()  # Emitted when add context button is clicked
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the prompt input widget."""
        super().__init__(workspace, parent)
        
        # Connect prompt_submitted to message_submitted for backward compatibility
        self.prompt_submitted.connect(self.message_submitted.emit)
    
    # All methods are inherited from AgentPromptWidget, so no need to redefine them
