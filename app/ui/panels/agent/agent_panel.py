"""Agent panel for AI Agent interactions."""

import asyncio
import logging
from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import QObject, Signal, Slot
from app.ui.panels.base_panel import BasePanel
from app.data.workspace import Workspace
from app.ui.panels.agent.chat_history_widget import ChatHistoryWidget
from app.ui.panels.agent.prompt_input_widget import AgentPromptInputWidget
# Removed heavy top-level import: from agent.filmeto_agent import FilmetoAgent
from utils.i18n_utils import tr

if TYPE_CHECKING:
    from agent.filmeto_agent import FilmetoAgent

logger = logging.getLogger(__name__)


class AgentPanel(BasePanel):
    """Panel for AI Agent interactions."""
    
    # Signals for async operations
    response_token_received = Signal(str)
    response_complete = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the agent panel."""
        import time
        init_start = time.time()
        super().__init__(workspace, parent)
        
        # Initialize agent (will be set when project is available)
        # Use string type hint to avoid top-level import
        self.agent: Optional['FilmetoAgent'] = None
        self._current_response = ""
        self._current_message_id = None
        self._is_processing = False
        self._initialization_in_progress = False
        
        # Connect internal signals
        self.response_token_received.connect(self._on_token_received)
        self.response_complete.connect(self._on_response_complete)
        self.error_occurred.connect(self._on_error)
        init_time = (time.time() - init_start) * 1000
        logger.debug(f"⏱️  [AgentPanel] __init__ completed in {init_time:.2f}ms")
    
    def setup_ui(self):
        """Set up the UI components with vertical layout."""
        import time
        setup_start = time.time()
        self.set_panel_title(tr("Agent"))
        
        # Chat history component (top, takes most space)
        self.chat_history_widget = ChatHistoryWidget(self.workspace, self)
        self.content_layout.addWidget(self.chat_history_widget, 1)  # Stretch factor 1
        
        # Prompt input component (bottom, fixed height)
        self.prompt_input_widget = AgentPromptInputWidget(self.workspace, self)
        self.content_layout.addWidget(self.prompt_input_widget, 0)  # No stretch
        
        # Connect signals
        self.prompt_input_widget.message_submitted.connect(self._on_message_submitted)
        
        setup_time = (time.time() - setup_start) * 1000
        logger.debug(f"⏱️  [AgentPanel] setup_ui completed in {setup_time:.2f}ms")
    
    def _on_message_submitted(self, message: str):
        """Handle message submission from prompt input widget."""
        if not message or self._is_processing:
            return
        
        # Add user message to chat history FIRST - always show user messages
        # regardless of whether agent processing succeeds or fails
        self.chat_history_widget.append_message(tr("用户"), message)
        
        # Start async processing which will initialize agent if needed
        asyncio.create_task(self._process_message_async(message))
    
    async def _process_message_async(self, message: str):
        """Process message asynchronously, initializing agent if needed."""
        # Check if agent is initialized, if not, initialize it first
        if not self.agent:
            if not self._initialization_in_progress:
                # Show message that agent is initializing
                init_message_id = self.chat_history_widget.start_streaming_message(tr("系统"))
                self.chat_history_widget.update_streaming_message(
                    init_message_id,
                    tr("Agent正在初始化中，请稍候...")
                )
                
                # Initialize agent asynchronously
                await self._initialize_agent_async()
                
                # Update initialization message
                if self.agent:
                    self.chat_history_widget.update_streaming_message(
                        init_message_id,
                        tr("Agent初始化完成")
                    )
                else:
                    self.chat_history_widget.update_streaming_message(
                        init_message_id,
                        tr("错误: Agent初始化失败。请确保项目已加载。")
                    )
                    return
            else:
                # Wait for ongoing initialization to complete
                while self._initialization_in_progress:
                    await asyncio.sleep(0.1)
                
                if not self.agent:
                    self.chat_history_widget.append_message(
                        tr("系统"),
                        tr("错误: Agent初始化失败。请确保项目已加载。")
                    )
                    return
        
        # Disable input while processing
        self._is_processing = True
        self.prompt_input_widget.set_enabled(False)
        
        # Reset current response and start streaming message
        self._current_response = ""
        self._current_message_id = self.chat_history_widget.start_streaming_message(tr("Agent"))
        
        # Start streaming response
        try:
            await self._stream_response(message)
        except Exception as e:
            # If streaming fails, show error
            error_msg = f"{tr('错误')}: {str(e)}"
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
    
    async def _initialize_agent_async(self):
        """Initialize the agent asynchronously with current workspace and project."""
        if self._initialization_in_progress or self.agent:
            return
        
        self._initialization_in_progress = True
        
        try:
            # Run initialization in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._initialize_agent_sync)
        except Exception as e:
            logger.error(f"❌ Error initializing agent: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._initialization_in_progress = False
    
    def _initialize_agent_sync(self):
        """Synchronously initialize the agent with current workspace and project."""
        import time
        init_start = time.time()
        logger.info("⏱️  [AgentPanel] Starting lazy agent initialization...")
        try:
            # Lazy import heavy agent module only when needed
            from agent.filmeto_agent import FilmetoAgent
            
            # Get current project from workspace
            project = self.workspace.get_project()
            if not project:
                logger.warning("⚠️ Cannot initialize agent: No project loaded")
                return
            
            # Get settings (model from settings, let FilmetoAgent read api_key internally)
            settings = self.workspace.get_settings()
            model = settings.get('ai_services.default_model', 'gpt-4o-mini') if settings else 'gpt-4o-mini'
            temperature = 0.7  # Could also make this configurable
            
            # Create agent instance (it will read api_key and base_url from workspace.settings)
            self.agent = FilmetoAgent(
                workspace=self.workspace,
                project=project,
                model=model,
                temperature=temperature,
                streaming=True
            )
            
            init_time = (time.time() - init_start) * 1000
            # Check if agent has a valid LLM initialized
            if self.agent.llm is None:
                logger.warning(f"⚠️ Agent initialized in {init_time:.2f}ms but LLM is not configured (missing API key)")
            else:
                logger.info(f"✅ Agent initialized successfully in {init_time:.2f}ms")
        except Exception as e:
            logger.error(f"❌ Error initializing agent: {e}")
            import traceback
            traceback.print_exc()
    
    def update_project(self, project):
        """Update agent with new project context."""
        if self.agent:
            self.agent.update_context(project=project)
        # Removed proactive initialization to ensure strict lazy loading on send button click
    
    def load_data(self):
        """Load agent data when panel is first activated."""
        super().load_data()
        # Agent will be initialized lazily on first message submission
        # No data loading needed here
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        logger.info("✅ Agent panel activated")
        # Agent will be initialized lazily on first message submission
    
    def on_deactivated(self):
        """Called when panel is hidden."""
        super().on_deactivated()
        logger.info("⏸️ Agent panel deactivated")

