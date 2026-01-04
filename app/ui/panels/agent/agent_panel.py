"""Agent panel for AI Agent interactions."""

import asyncio
from typing import Optional
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import QObject, Signal, Slot
from app.ui.panels.base_panel import BasePanel
from app.data.workspace import Workspace
from app.ui.panels.agent.chat_history_widget import ChatHistoryWidget
from app.ui.panels.agent.prompt_input_widget import AgentPromptInputWidget
from agent.filmeto_agent import FilmetoAgent
from utils.i18n_utils import tr


class AgentPanel(BasePanel):
    """Panel for AI Agent interactions."""
    
    # Signals for async operations
    response_token_received = Signal(str)
    response_complete = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the agent panel."""
        super().__init__(workspace, parent)
        
        # Initialize agent (will be set when project is available)
        self.agent: Optional[FilmetoAgent] = None
        self._current_response = ""
        self._current_message_id = None
        self._is_processing = False
        
        # Connect internal signals
        self.response_token_received.connect(self._on_token_received)
        self.response_complete.connect(self._on_response_complete)
        self.error_occurred.connect(self._on_error)
    
    def setup_ui(self):
        """Set up the UI components with vertical layout."""
        # Main vertical layout - no margins
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
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
        if not message or self._is_processing:
            return
        
        # Add user message to chat history FIRST - always show user messages
        # regardless of whether agent processing succeeds or fails
        self.chat_history_widget.append_message(tr("用户"), message)
        
        # Check if agent is initialized
        if not self.agent:
            self._initialize_agent()
        
        if not self.agent:
            # Show error message, but user message is already displayed
            self.chat_history_widget.append_message(
                tr("系统"),
                tr("错误: Agent未初始化。请确保项目已加载。")
            )
            return
        
        # Disable input while processing
        self._is_processing = True
        self.prompt_input_widget.set_enabled(False)
        
        # Reset current response and start streaming message
        self._current_response = ""
        self._current_message_id = self.chat_history_widget.start_streaming_message(tr("Agent"))
        
        # Start streaming response in background
        # Wrap in try-except to ensure errors don't prevent user message from showing
        try:
            asyncio.create_task(self._stream_response(message))
        except Exception as e:
            # If task creation fails, still show error but user message is already displayed
            error_msg = f"Error: {str(e)}"
            self.error_occurred.emit(error_msg)
    
    async def _stream_response(self, message: str):
        """Stream response from agent."""
        try:
            # Stream tokens from agent
            async for token in self.agent.chat_stream(
                message=message,
                on_token=lambda t: self.response_token_received.emit(t),
                on_complete=lambda r: self.response_complete.emit(r)
            ):
                # Tokens are handled by signal callbacks
                pass
        except Exception as e:
            # Ensure error is displayed, but user message is already shown
            error_msg = f"{tr('错误')}: {str(e)}"
            self.error_occurred.emit(error_msg)
        finally:
            # Ensure we always clean up streaming state even if there's an error
            # The error handler will also clean up, but this provides extra safety
            pass
    
    @Slot(str)
    def _on_token_received(self, token: str):
        """Handle received token from agent."""
        self._current_response += token
        # Update the streaming message in chat history
        if self._current_message_id:
            self.chat_history_widget.update_streaming_message(
                self._current_message_id,
                self._current_response
            )
    
    @Slot(str)
    def _on_response_complete(self, response: str):
        """Handle complete response from agent."""
        # Update the final message (already displayed via streaming)
        if self._current_message_id:
            self.chat_history_widget.update_streaming_message(
                self._current_message_id,
                response
            )
        
        # Clear message ID
        self._current_message_id = None
        
        # Re-enable input
        self._is_processing = False
        self.prompt_input_widget.set_enabled(True)
    
    @Slot(str)
    def _on_error(self, error_message: str):
        """Handle error during agent processing."""
        # If there's a streaming message in progress, update it with error
        # Otherwise, add a new error message
        if self._current_message_id:
            # Update the streaming message to show error
            self.chat_history_widget.update_streaming_message(
                self._current_message_id,
                error_message
            )
            self._current_message_id = None
        else:
            # Add error message as new message
            self.chat_history_widget.append_message(tr("系统"), error_message)
        
        # Clear current response
        self._current_response = ""
        
        # Re-enable input
        self._is_processing = False
        self.prompt_input_widget.set_enabled(True)
    
    def _initialize_agent(self):
        """Initialize the agent with current workspace and project."""
        try:
            # Get current project from workspace
            project = self.workspace.get_project()
            if not project:
                return
            
            # Get API key from settings (if available)
            settings = self.workspace.get_settings()
            api_key = settings.get('openai_api_key') if settings else None
            
            # Create agent instance
            self.agent = FilmetoAgent(
                workspace=self.workspace,
                project=project,
                api_key=api_key,
                model="gpt-4o-mini",
                temperature=0.7,
                streaming=True
            )
            
            print("✅ Agent initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing agent: {e}")
            import traceback
            traceback.print_exc()
    
    def update_project(self, project):
        """Update agent with new project context."""
        if self.agent:
            self.agent.update_context(project=project)
        else:
            self._initialize_agent()
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        print("✅ Agent panel activated")
        
        # Initialize agent if not already done
        if not self.agent:
            self._initialize_agent()
    
    def on_deactivated(self):
        """Called when panel is hidden."""
        super().on_deactivated()
        print("⏸️ Agent panel deactivated")

