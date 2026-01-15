"""Agent panel for AI Agent interactions with multi-agent streaming support."""

import asyncio
import logging
from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import Signal, Slot, QObject
from PySide6.QtWidgets import QApplication

from agent.filmeto_agent import StreamEvent, AgentStreamSession
from app.ui.panels.base_panel import BasePanel
from app.data.workspace import Workspace
from utils.i18n_utils import tr


logger = logging.getLogger(__name__)


class StreamEventHandler(QObject):
    """Handler for stream events that bridges async agent to Qt signals."""

    # Signal to emit stream events on Qt main thread
    stream_event_received = Signal(object, object)  # StreamEvent, AgentStreamSession

    def __init__(self, parent=None):
        super().__init__(parent)

    def handle_event(self, event: 'StreamEvent', session: 'AgentStreamSession'):
        """Handle a stream event (called from agent thread)."""
        # Emit signal to be handled on main thread
        self.stream_event_received.emit(event, session)


class AgentPanel(BasePanel):
    """Panel for AI Agent interactions with multi-agent streaming support.

    Features:
    - Multi-agent streaming display
    - Group-chat style agent collaboration visualization
    - Concurrent agent execution support
    - Structured content display (plans, tasks, media, references)
    """

    # Signals for async operations
    response_token_received = Signal(str)
    response_complete = Signal(str)
    error_occurred = Signal(str)
    stream_event = Signal(object, object)  # StreamEvent, AgentStreamSession

    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the agent panel."""
        import time
        init_start = time.time()
        super().__init__(workspace, parent)

        # Initialize agent (will be set when project is available)
        # Using forward reference to avoid import at class definition time
        self.agent: Optional['FilmetoAgent'] = None
        self._current_response = ""
        self._current_message_id = None
        self._is_processing = False
        self._initialization_in_progress = False

        # Stream event handler for bridging async to Qt
        self._stream_handler = StreamEventHandler(self)
        self._stream_handler.stream_event_received.connect(self._on_stream_event)

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

        # Defer widget creation to avoid blocking UI initialization
        # Widgets will be created on first activation
        self.chat_history_widget = None
        self.prompt_input_widget = None
        self._widgets_initialized = False

        setup_time = (time.time() - setup_start) * 1000
        logger.debug(f"⏱️  [AgentPanel] setup_ui completed in {setup_time:.2f}ms")
    
    def _initialize_widgets(self):
        """Initialize heavy UI widgets (deferred until first activation)."""
        import time
        init_start = time.time()
        
        # Import widgets locally to defer expensive imports
        import_start = time.time()
        from app.ui.chat.chat_history_widget import ChatHistoryWidget
        from app.ui.prompt.agent_prompt_widget import AgentPromptWidget
        import_time = (time.time() - import_start) * 1000
        logger.info(f"⏱️  Import widgets: {import_time:.2f}ms")

        # Chat history component (top, takes most space)
        chat_start = time.time()
        self.chat_history_widget = ChatHistoryWidget(self.workspace, self)
        chat_time = (time.time() - chat_start) * 1000
        logger.info(f"⏱️  ChatHistoryWidget created: {chat_time:.2f}ms")
        
        self.content_layout.addWidget(self.chat_history_widget, 1)  # Stretch factor 1

        # Prompt input component (bottom, fixed height)
        prompt_start = time.time()
        self.prompt_input_widget = AgentPromptWidget(self.workspace, self)
        prompt_time = (time.time() - prompt_start) * 1000
        logger.info(f"⏱️  AgentPromptWidget created: {prompt_time:.2f}ms")
        
        self.content_layout.addWidget(self.prompt_input_widget, 0)  # No stretch

        # Connect signals
        signal_start = time.time()
        self.prompt_input_widget.message_submitted.connect(self._on_message_submitted)
        self.chat_history_widget.reference_clicked.connect(self._on_reference_clicked)
        signal_time = (time.time() - signal_start) * 1000
        logger.info(f"⏱️  Signals connected: {signal_time:.2f}ms")
        
        self._widgets_initialized = True
        
        init_time = (time.time() - init_start) * 1000
        logger.info(f"✅ Agent panel widgets initialized in {init_time:.2f}ms")
    
    def _on_message_submitted(self, message: str):
        """Handle message submission from prompt input widget."""
        if not message or self._is_processing:
            return
        
        # Ensure widgets are initialized
        if not self._widgets_initialized:
            logger.warning("⚠️ Agent panel widgets not initialized yet")
            return
        
        # Add user message to chat history using new card-based display
        self.chat_history_widget.add_user_message(message)
        
        # Start async processing which will initialize agent if needed
        asyncio.create_task(self._process_message_async(message))
    
    def _on_reference_clicked(self, ref_type: str, ref_id: str):
        """Handle reference click in chat history."""
        logger.info(f"Reference clicked: {ref_type} / {ref_id}")
        # TODO: Implement reference navigation (e.g., jump to timeline item, show task details)
    
    async def _process_message_async(self, message: str):
        """Process message asynchronously, initializing agent if needed."""
        # Ensure widgets are initialized
        if not self._widgets_initialized:
            logger.error("❌ Agent panel widgets not initialized")
            return
        
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
        if self.prompt_input_widget:
            self.prompt_input_widget.set_enabled(False)
        
        # Reset current response - don't create a message card yet
        # The streaming events will create cards as agents start responding
        self._current_response = ""
        self._current_message_id = None
        
        # Start streaming response
        try:
            await self._stream_response(message)
        except Exception as e:
            # If streaming fails, show error
            error_msg = f"{tr('错误')}: {str(e)}"
            self.error_occurred.emit(error_msg)
    
    async def _stream_response(self, message: str):
        """Stream response from agent with multi-agent events."""
        try:
            # Register UI callback with stream manager
            self.agent.add_ui_callback(self._stream_handler.handle_event)
            
            try:
                # Stream tokens from agent with event callback
                async for token in self.agent.chat_stream(
                    message=message,
                    on_token=lambda t: self.response_token_received.emit(t),
                    on_complete=lambda r: self.response_complete.emit(r),
                    on_stream_event=lambda e: self._handle_stream_event_sync(e)
                ):
                    # Tokens are handled by signal callbacks and stream events
                    pass
            finally:
                # Remove UI callback
                self.agent.remove_ui_callback(self._stream_handler.handle_event)
                
        except Exception as e:
            # Ensure error is displayed
            error_msg = f"{tr('错误')}: {str(e)}"
            self.error_occurred.emit(error_msg)
        finally:
            # Re-enable input
            self._is_processing = False
            if self.prompt_input_widget:
                self.prompt_input_widget.set_enabled(True)
    
    def _handle_stream_event_sync(self, event: StreamEvent):
        """Handle stream event synchronously (called from agent thread)."""
        # Get session from agent
        session = self.agent.get_current_session() if self.agent else None
        if session:
            self._stream_handler.handle_event(event, session)
    
    @Slot(object, object)
    def _on_stream_event(self, event: StreamEvent, session: AgentStreamSession):
        """Handle stream event on Qt main thread."""
        # Ensure widgets are initialized
        if not self._widgets_initialized or not self.chat_history_widget:
            return
        
        # Forward to chat history widget
        self.chat_history_widget.handle_stream_event(event, session)

        # Process UI updates
        QApplication.processEvents()
    
    @Slot(str)
    def _on_token_received(self, token: str):
        """Handle received token from agent (legacy API)."""
        self._current_response += token
        
        # If we have a current message ID (legacy mode), update it
        if self._current_message_id and self.chat_history_widget:
            self.chat_history_widget.update_streaming_message(
                self._current_message_id,
                self._current_response
            )
    
    @Slot(str)
    def _on_response_complete(self, response: str):
        """Handle complete response from agent."""
        # Update the final message if in legacy mode
        if self._current_message_id and self.chat_history_widget:
            self.chat_history_widget.update_streaming_message(
                self._current_message_id,
                response
            )
        
        # Clear message ID
        self._current_message_id = None
        
        # Re-enable input
        self._is_processing = False
        if self.prompt_input_widget:
            self.prompt_input_widget.set_enabled(True)
    
    @Slot(str)
    def _on_error(self, error_message: str):
        """Handle error during agent processing."""
        if not self.chat_history_widget:
            logger.error(f"❌ Error but widgets not initialized: {error_message}")
            return
        
        # If there's a streaming message in progress, update it with error
        if self._current_message_id:
            self.chat_history_widget.update_streaming_message(
                self._current_message_id,
                error_message
            )
            self._current_message_id = None
        else:
            # Add error message as new system message
            self.chat_history_widget.append_message(tr("系统"), error_message)
        
        # Clear current response
        self._current_response = ""
        
        # Re-enable input
        self._is_processing = False
        if self.prompt_input_widget:
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
            if not self.agent.llm_service.validate_config():
                logger.warning(f"⚠️ Agent initialized in {init_time:.2f}ms but LLM is not configured (missing API key or base URL)")
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
    
    def load_data(self):
        """Load agent data when panel is first activated."""
        super().load_data()
        # Agent will be initialized lazily on first message submission
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        
        # Initialize widgets on first activation
        if not self._widgets_initialized:
            self._initialize_widgets()
        
        logger.info("✅ Agent panel activated")
    
    def on_deactivated(self):
        """Called when panel is hidden."""
        super().on_deactivated()
        logger.info("⏸️ Agent panel deactivated")
