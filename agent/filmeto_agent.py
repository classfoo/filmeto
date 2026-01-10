"""Filmeto Agent - Main entry point for AI agent interactions."""

import asyncio
from typing import Any, Dict, List, Optional, AsyncIterator, Callable
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent.nodes import (
    AgentState,
    CoordinatorNode,
    PlannerNode,
    ExecutorNode,
    ResponseNode,
    should_continue,
    route_after_tools
)
from agent.tools import ToolRegistry
from app.data.conversation import ConversationManager, Conversation, Message, MessageRole


class FilmetoAgent:
    """
    Main agent class for Filmeto AI interactions.
    
    Provides:
    - Streaming conversation interface
    - LangGraph-based agent workflow
    - Tool calling capabilities
    - Conversation history management
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
        Initialize Filmeto Agent.
        
        Args:
            workspace: Workspace instance
            project: Project instance
            api_key: OpenAI API key (optional, can use settings or environment variable)
            model: LLM model to use
            temperature: Temperature for LLM
            streaming: Enable streaming responses
            base_url: OpenAI API base URL (optional, can use settings)
        """
        self.workspace = workspace
        self.project = project
        self.streaming = streaming
        
        # Get settings from workspace
        settings = None
        if workspace and hasattr(workspace, 'settings'):
            settings = workspace.settings
        
        # Initialize LLM
        llm_kwargs = {
            "model": model,
            "temperature": temperature,
            "streaming": streaming
        }
        
        # Configure API key - priority: parameter > settings > environment
        if api_key:
            llm_kwargs["api_key"] = api_key
        elif settings:
            settings_api_key = settings.get("ai_services.openai_api_key", "")
            if settings_api_key:
                llm_kwargs["api_key"] = settings_api_key
        else:
            # Fall back to environment variable
            import os
            env_api_key = os.getenv("OPENAI_API_KEY")
            if env_api_key:
                llm_kwargs["api_key"] = env_api_key
        
        # Configure base URL - priority: parameter > settings > default
        if base_url:
            llm_kwargs["base_url"] = base_url
        elif settings:
            settings_base_url = settings.get("ai_services.openai_host", "")
            if settings_base_url:
                llm_kwargs["base_url"] = settings_base_url
        
        # Check if we have required configuration
        if "api_key" not in llm_kwargs:
            # If no API key is provided, we can't initialize the LLM
            self.llm = None
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("⚠️ Warning: No OpenAI API key provided. Agent will not function until API key is set.")
            logger.warning("   Please set API key in workspace settings (ai_services.openai_api_key) or environment variable (OPENAI_API_KEY)")
            return
        
        self.llm = ChatOpenAI(**llm_kwargs)
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry(workspace=workspace, project=project)
        self.tools = self.tool_registry.get_all_tools()
        
        # Initialize conversation manager
        self.conversation_manager = project.get_conversation_manager() if project else None
        self.current_conversation: Optional[Conversation] = None

        # Memory for checkpointing
        self.memory = MemorySaver()

        # Initialize graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        if not self.llm:
            raise ValueError("Cannot build graph: LLM not initialized. API key is required.")
        
        # Create nodes
        coordinator = CoordinatorNode(self.llm, self.tools)
        planner = PlannerNode(self.llm, self.tools)
        executor = ExecutorNode(self.llm, self.tools)
        responder = ResponseNode(self.llm)
        
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("coordinator", coordinator)
        workflow.add_node("planner", planner)
        workflow.add_node("use_tools", executor)
        workflow.add_node("respond", responder)
        
        # Set entry point
        workflow.set_entry_point("coordinator")
        
        # Add conditional edges from coordinator
        workflow.add_conditional_edges(
            "coordinator",
            should_continue,
            {
                "use_tools": "use_tools",
                "respond": "respond",
                "plan": "planner",
                "end": END
            }
        )
        
        # Add edge from planner to executor
        workflow.add_edge("planner", "use_tools")
        
        # Add conditional edge from executor back to coordinator
        workflow.add_conditional_edges(
            "use_tools",
            route_after_tools,
            {
                "coordinator": "coordinator",
                "end": END
            }
        )
        
        # Add edge from responder to end
        workflow.add_edge("respond", END)
        
        # Compile graph
        return workflow.compile(checkpointer=self.memory)
    
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
    
    async def chat_stream(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        on_token: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None
    ) -> AsyncIterator[str]:
        """
        Stream a chat response.
        
        Args:
            message: User message
            conversation_id: Optional conversation ID (uses current if not provided)
            on_token: Optional callback for each token
            on_complete: Optional callback when complete
            
        Yields:
            Response tokens as they are generated
        """
        # Check if LLM is initialized
        if not self.llm:
            error_msg = "Error: OpenAI API key not configured. Please set your API key in settings."
            if on_token:
                on_token(error_msg)
            yield error_msg
            return
        
        # Get or create conversation
        if conversation_id:
            self.set_conversation(conversation_id)
        
        conversation = self.get_or_create_conversation()
        
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
        
        # Prepare messages for LLM
        messages = [
            HumanMessage(content=msg.content) if msg.role == MessageRole.USER
            else AIMessage(content=msg.content)
            for msg in conversation.messages
        ]
        
        # Initial state
        initial_state: AgentState = {
            "messages": messages,
            "next_action": "coordinator",
            "context": {},
            "iteration_count": 0
        }
        
        # Stream response
        full_response = ""

        # Create config with thread_id for memory checkpointer
        config = {"configurable": {"thread_id": conversation.conversation_id}}

        if self.streaming:
            # Use astream for streaming
            async for event in self.graph.astream(initial_state, config=config):
                for node_name, node_output in event.items():
                    if "messages" in node_output:
                        last_message = node_output["messages"][-1]
                        if isinstance(last_message, AIMessage):
                            content = last_message.content
                            if content and content not in full_response:
                                # Extract new content
                                new_content = content[len(full_response):]
                                full_response = content

                                # Yield token by token
                                for char in new_content:
                                    if on_token:
                                        on_token(char)
                                    yield char
                                    await asyncio.sleep(0.01)  # Small delay for smooth streaming
        else:
            # Non-streaming mode
            result = await self.graph.ainvoke(initial_state, config=config)
            if "messages" in result:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    full_response = last_message.content
                    if on_token:
                        on_token(full_response)
                    yield full_response
        
        # Add assistant message to conversation
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=full_response,
            timestamp=datetime.now().isoformat()
        )
        conversation.add_message(assistant_message)
        
        # Save conversation
        if self.conversation_manager:
            self.conversation_manager.save_conversation(conversation)
        
        # Call completion callback
        if on_complete:
            on_complete(full_response)
    
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
        if not self.llm:
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
            self.conversation_manager = project.get_conversation_manager()
        
        # Update API key if provided
        if api_key:
            # Reinitialize LLM with new API key
            llm_kwargs = {
                "model": "gpt-4o-mini",  # Use default model or store model in instance
                "temperature": 0.7,       # Use default temperature or store in instance
                "streaming": self.streaming,
                "api_key": api_key
            }
            
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(**llm_kwargs)
        
        # Update tool registry
        self.tool_registry.update_context(workspace, project)
        
        # Rebuild graph with updated tools
        self.tools = self.tool_registry.get_all_tools()
        try:
            self.graph = self._build_graph()
        except ValueError:
            # LLM might still not be initialized
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("⚠️ Cannot build graph: LLM not initialized")
    
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
        
        # Clear current conversation if it's being deleted
        if self.current_conversation and self.current_conversation.conversation_id == conversation_id:
            self.current_conversation = None
        
        return self.conversation_manager.delete_conversation(conversation_id)

