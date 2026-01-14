"""Filmeto Agent - Main entry point for AI agent interactions with multi-agent architecture.

This version uses LiteLLM for LLM calls and implements a simple state machine for workflow orchestration,
removing dependencies on LangChain and LangGraph.
"""

import asyncio
from typing import Any, Dict, List, Optional, AsyncIterator, Callable
import logging

from agent.new_production_agent import NewProductionAgent
from agent.tools import ToolRegistry
from agent.sub_agents.registry import SubAgentRegistry
from agent.streaming import (
    StreamEventEmitter,
    StreamEvent,
    StreamEventType,
    AgentRole,
    AgentStreamManager,
    AgentStreamSession,
    PlanContent,
)
from app.data.conversation import ConversationManager, Conversation, Message, MessageRole

logger = logging.getLogger(__name__)


class FilmetoAgent:
    """
    Main agent class for Filmeto AI interactions with project-isolated architecture.

    Key Features:
    - Project-level isolation: Each project has independent conversation context
    - New Production Agent as orchestrator: Uses NewProductionAgent (LiteLLM-based)
    - Multi-agent coordination: All sub-agents are integrated directly
    - Streaming support: Real-time event streaming for UI updates

    Architecture:
    FilmetoAgent (Project-scoped)
      └── NewProductionAgent (LiteLLM-based)
            ├── question_understanding (node)
            ├── coordinator (node)
            ├── planner (node)
            ├── sub_agent_executor (node)
            │     ├── DirectorAgent (direct)
            │     ├── ScreenwriterAgent (direct)
            │     └── ... other agents (direct)
            └── respond (node)
    """

    def __init__(
        self,
        workspace: Any,
        project: Any,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        streaming: bool = True,
        base_url: Optional[str] = None
    ):
        """
        Initialize Filmeto Agent for a specific project.

        Args:
            workspace: Workspace instance
            project: Project instance (required for project isolation)
            api_key: OpenAI API key (optional, can use settings or environment variable)
            model: LLM model to use
            temperature: Temperature for LLM
            streaming: Enable streaming responses
            base_url: OpenAI API base URL (optional, can use settings)
        """
        self.workspace = workspace
        self.project = project
        self.streaming = streaming
        self.model = model
        self.temperature = temperature

        # Project ID for context isolation
        self.project_id = project.project_name if project else "default"

        # Stream manager for multi-agent communication
        self.stream_manager = AgentStreamManager()
        self._current_session: Optional[AgentStreamSession] = None
        self._current_emitter: Optional[StreamEventEmitter] = None

        # Get settings from workspace
        settings = None
        if workspace and hasattr(workspace, 'settings'):
            settings = workspace.settings

        # Configure API key - priority: parameter > settings > environment
        if api_key:
            self.api_key = api_key
        elif settings:
            settings_api_key = settings.get("ai_services.openai_api_key", "")
            if settings_api_key:
                self.api_key = settings_api_key
        else:
            # Fall back to environment variable
            import os
            env_api_key = os.getenv("OPENAI_API_KEY")
            if env_api_key:
                self.api_key = env_api_key

        # Configure base URL - priority: parameter > settings > default
        if base_url:
            self.base_url = base_url
        elif settings:
            settings_base_url = settings.get("ai_services.openai_host", "")
            if settings_base_url:
                self.base_url = settings_base_url

        # Check if we have required configuration
        if not hasattr(self, 'api_key') or not self.api_key:
            self.new_production_agent = None
            logger.warning("⚠️ Warning: No OpenAI API key provided. Agent will not function until API key is set.")
            logger.warning("   Please set API key in workspace settings (ai_services.openai_api_key) or environment variable (OPENAI_API_KEY)")
            return

        # Initialize tool registry
        self.tool_registry = ToolRegistry(workspace=workspace, project=project)

        # Initialize sub-agent registry
        self.sub_agent_registry = SubAgentRegistry()

        # Initialize conversation manager (project-scoped)
        self.conversation_manager = project.get_conversation_manager() if project else None
        self.current_conversation: Optional[Conversation] = None

        # Initialize New Production Agent (the main orchestrator)
        self.new_production_agent = NewProductionAgent(
            project_id=self.project_id,
            workspace=workspace,
            project=project,
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
            sub_agent_registry=self.sub_agent_registry,
            tool_registry=self.tool_registry
        )

    def set_conversation(self, conversation_id: str) -> bool:
        """
        Set the current conversation by ID.

        Args:
            conversation_id: Conversation ID to load

        Returns:
            True if successful, False if conversation not found
        """
        if not self.conversation_manager:
            return False

        conversation = self.conversation_manager.get_conversation(conversation_id)
        if conversation:
            self.current_conversation = conversation
            return True
        return False

    def create_conversation(self, title: Optional[str] = None) -> Conversation:
        """
        Create a new conversation.

        Args:
            title: Optional title for the conversation

        Returns:
            New Conversation object
        """
        if not self.conversation_manager:
            raise RuntimeError("No conversation manager available")

        conversation = self.conversation_manager.create_conversation(title)
        self.current_conversation = conversation
        return conversation

    def get_or_create_conversation(self) -> Conversation:
        """Get current conversation or create a new one."""
        if self.current_conversation:
            return self.current_conversation

        if self.conversation_manager:
            self.current_conversation = self.conversation_manager.get_or_create_default_conversation()
            return self.current_conversation

        raise RuntimeError("No conversation manager available")

    def create_stream_session(self) -> tuple[AgentStreamSession, StreamEventEmitter]:
        """Create a new streaming session with emitter."""
        session, emitter = self.stream_manager.create_session()
        self._current_session = session
        self._current_emitter = emitter
        return session, emitter

    def get_current_session(self) -> Optional[AgentStreamSession]:
        """Get the current streaming session."""
        return self._current_session

    def get_current_emitter(self) -> Optional[StreamEventEmitter]:
        """Get the current stream emitter."""
        return self._current_emitter

    async def chat_stream(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        on_token: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
        on_stream_event: Optional[Callable[[StreamEvent], None]] = None
    ) -> AsyncIterator[str]:
        """
        Stream a chat response using the New Production Agent.

        Args:
            message: User message
            conversation_id: Optional conversation ID (uses current if not provided)
            on_token: Optional callback for each token (legacy)
            on_complete: Optional callback when complete (legacy)
            on_stream_event: Optional callback for stream events (new API)

        Yields:
            Response tokens as they are generated
        """
        logger.info("=" * 80)
        logger.info(f"[FilmetoAgent] ENTRY: chat_stream")
        logger.info(f"[FilmetoAgent] Message: {message[:100]}...")
        logger.info(f"[FilmetoAgent] Conversation ID: {conversation_id}")
        logger.info(f"[FilmetoAgent] Project ID: {self.project_id}")
        logger.info("=" * 80)

        # Check if agent is initialized
        if not self.new_production_agent:
            error_msg = "Error: OpenAI API key not configured. Please set your API key in settings."
            logger.error(f"[FilmetoAgent] ERROR: Production agent not initialized")
            if on_token:
                on_token(error_msg)
            yield error_msg
            logger.info("[FilmetoAgent] EXIT: chat_stream (early exit - no production agent)")
            return

        # Get or create conversation
        if conversation_id:
            logger.info(f"[FilmetoAgent] Setting conversation: {conversation_id}")
            self.set_conversation(conversation_id)

        conversation = self.get_or_create_conversation()
        logger.info(f"[FilmetoAgent] Using conversation: {conversation.conversation_id}")

        # Create streaming session
        session, emitter = self.create_stream_session()
        logger.info(f"[FilmetoAgent] Created stream session: {session.session_id}")

        # Set emitter on production agent
        self.new_production_agent.stream_emitter = emitter

        # Add stream event callback if provided
        if on_stream_event:
            emitter.add_callback(on_stream_event)

        # Emit session start
        emitter.emit_session_start({"message": message, "project_id": self.project_id})

        # Add user message to conversation
        from datetime import datetime
        user_message = Message(
            role=MessageRole.USER,
            content=message,
            timestamp=datetime.now().isoformat()
        )
        conversation.add_message(user_message)

        # Save conversation
        if self.conversation_manager:
            self.conversation_manager.save_conversation(conversation)

        # Prepare messages for LLM using the safe conversion method
        messages = conversation.get_messages_as_dicts()  # This method needs to be implemented in the Conversation class

        logger.info(f"[FilmetoAgent] Prepared {len(messages)} messages for LLM")

        # Create config with thread_id for memory checkpointer
        config = {"configurable": {"thread_id": conversation.conversation_id, "project_id": self.project_id}}

        # Stream response
        full_response = ""
        final_messages = []
        plan_id = None

        if self.streaming:
            logger.info("[FilmetoAgent] Starting streaming mode")
            # Use new production agent stream
            async for event in self.new_production_agent.stream(messages, config=config):
                for node_name, node_output in event.items():
                    logger.debug(f"[FilmetoAgent] Received event from node: {node_name}")
                    # Emit node-specific events
                    if node_name == "question_understanding":
                        emitter.emit_agent_start("QuestionUnderstanding", AgentRole.QUESTION_UNDERSTANDING)
                        context = node_output.get("context", {})
                        analysis = context.get("question_analysis", {})
                        if analysis:
                            thinking_text = f"Task type: {analysis.get('task_type', 'unknown')}"
                            emitter.emit_agent_thinking("QuestionUnderstanding", thinking_text)

                    elif node_name == "planner":
                        emitter.emit_agent_start("Planner", AgentRole.PLANNER)
                        execution_plan = node_output.get("execution_plan")
                        if execution_plan:
                            plan_event, plan_id = emitter.emit_plan_created(execution_plan, "Planner")

                    elif node_name == "coordinator":
                        emitter.emit_agent_start("Coordinator", AgentRole.COORDINATOR)

                    # Handle messages
                    if "messages" in node_output:
                        final_messages = node_output["messages"]

                        last_message = node_output["messages"][-1]
                        if isinstance(last_message, dict) and "content" in last_message:
                            content = last_message["content"]
                            if content:
                                # Determine which agent is responding
                                agent_name = self._get_agent_name_from_node(node_name, node_output)
                                agent_role = AgentRole.from_agent_name(agent_name)

                                # Check if this is new content
                                if content not in full_response:
                                    new_content = content[len(full_response):]
                                    full_response = content

                                    # Emit content event
                                    emitter.emit_agent_content(agent_name, new_content, append=True)

                                    # Yield token by token for legacy API
                                    for char in new_content:
                                        if on_token:
                                            on_token(char)
                                        yield char
                                        await asyncio.sleep(0.01)
        else:
            logger.info("[FilmetoAgent] Starting non-streaming mode")
            # Non-streaming mode
            result = await self.new_production_agent.execute(messages, config=config)
            if "messages" in result:
                final_messages = result["messages"]
                last_message = result["messages"][-1]
                if isinstance(last_message, dict) and "content" in last_message:
                    full_response = last_message["content"]
                    if on_token:
                        on_token(full_response)
                    yield full_response

        logger.info(f"[FilmetoAgent] Received {len(final_messages)} final messages")

        # Save all new messages to conversation
        num_existing_messages = len(messages)
        new_messages = final_messages[num_existing_messages:]
        logger.info(f"[FilmetoAgent] Saving {len(new_messages)} new messages to conversation")

        for msg in new_messages:
            if isinstance(msg, dict) and "content" in msg:
                assistant_msg = Message(
                    role=MessageRole.ASSISTANT,
                    content=msg["content"] or "",
                    timestamp=datetime.now().isoformat(),
                    tool_calls=msg.get("tool_calls", None)
                )
                conversation.add_message(assistant_msg)

        # Save conversation
        if self.conversation_manager:
            self.conversation_manager.save_conversation(conversation)

        # Emit session end
        emitter.emit_session_end({"total_response_length": len(full_response)})

        # Call completion callback
        if on_complete:
            on_complete(full_response)

        logger.info("=" * 80)
        logger.info(f"[FilmetoAgent] EXIT: chat_stream")
        logger.info(f"[FilmetoAgent] Total response length: {len(full_response)}")
        logger.info("=" * 80)

    def _get_agent_name_from_node(self, node_name: str, node_output: Dict[str, Any]) -> str:
        """Get agent name from node name and output."""
        node_to_agent = {
            "question_understanding": "QuestionUnderstanding",
            "coordinator": "Coordinator",
            "planner": "Planner",
            "use_tools": "Executor",
            "respond": "Response",
            "execute_sub_agent_plan": None,  # Determined by task
            "review_plan": "Reviewer",
            "refine_plan": "PlanRefinement",
            "synthesize_results": "Synthesizer",
        }

        # For execute_sub_agent_plan, try to get from task context
        if node_name == "execute_sub_agent_plan":
            sub_agent_results = node_output.get("sub_agent_results", {})
            if sub_agent_results:
                # Get the last added result's agent
                for task_id, result in sorted(sub_agent_results.items(), reverse=True):
                    if "agent" in result:
                        return result["agent"]
            return "Executor"

        return node_to_agent.get(node_name, "Agent")

    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Send a chat message and get the complete response.

        Args:
            message: User message
            conversation_id: Optional conversation ID

        Returns:
            Complete response string
        """
        if not self.api_key:
            return "Error: OpenAI API key not configured. Please set your API key in settings."

        response = ""
        async for token in self.chat_stream(message, conversation_id):
            response += token
        return response

    def update_context(self, workspace: Any = None, project: Any = None, api_key: Optional[str] = None):
        """
        Update workspace and project context.

        Args:
            workspace: New workspace instance
            project: New project instance
            api_key: New API key (optional)
        """
        if workspace:
            self.workspace = workspace
        if project:
            self.project = project
            self.project_id = project.project_name
            self.conversation_manager = project.get_conversation_manager()

        # Update API key if provided
        if api_key:
            self.api_key = api_key

        # Update tool registry
        if workspace or project:
            self.tool_registry.update_context(workspace, project)

        # Rebuild new production agent with updated context
        if self.api_key and (workspace or project):
            self.new_production_agent = NewProductionAgent(
                project_id=self.project_id,
                workspace=self.workspace,
                project=self.project,
                model=self.model,
                api_key=self.api_key,
                base_url=getattr(self, 'base_url', None),
                temperature=self.temperature,
                sub_agent_registry=self.sub_agent_registry,
                tool_registry=self.tool_registry
            )

    def get_conversation_history(self, conversation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history.

        Args:
            conversation_id: Optional conversation ID (uses current if not provided)

        Returns:
            List of messages
        """
        if conversation_id:
            conversation = self.conversation_manager.get_conversation(conversation_id)
        else:
            conversation = self.current_conversation

        if not conversation:
            return []

        return [msg.to_dict() for msg in conversation.messages]

    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all conversations.

        Returns:
            List of conversation metadata
        """
        if not self.conversation_manager:
            return []

        return self.conversation_manager.list_conversations()

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation ID to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.conversation_manager:
            return False

        if self.current_conversation and self.current_conversation.conversation_id == conversation_id:
            self.current_conversation = None

        return self.conversation_manager.delete_conversation(conversation_id)

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """
        Get list of available sub-agents.

        Returns:
            List of agent info dictionaries
        """
        return [agent.to_dict() for agent in self.sub_agent_registry.list_agents()]

    def get_agent_capabilities(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get capabilities of all sub-agents.

        Returns:
            Dictionary mapping agent names to their skills
        """
        return self.sub_agent_registry.get_agent_capabilities()

    def add_stream_callback(self, callback: Callable[[StreamEvent], None]):
        """Add a callback for stream events."""
        if self._current_emitter:
            self._current_emitter.add_callback(callback)

    def remove_stream_callback(self, callback: Callable[[StreamEvent], None]):
        """Remove a stream event callback."""
        if self._current_emitter:
            self._current_emitter.remove_callback(callback)

    def add_ui_callback(self, callback: Callable[[StreamEvent, AgentStreamSession], None]):
        """Add a UI callback to the stream manager."""
        self.stream_manager.add_ui_callback(callback)

    def remove_ui_callback(self, callback: Callable[[StreamEvent, AgentStreamSession], None]):
        """Remove a UI callback from the stream manager."""
        self.stream_manager.remove_ui_callback(callback)
