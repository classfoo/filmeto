"""Filmeto Agent - Main entry point for AI agent interactions with multi-agent architecture."""

import asyncio
from typing import Any, Dict, List, Optional, AsyncIterator, Callable, Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import logging

from agent.nodes import (
    AgentState,
    QuestionUnderstandingNode,
    PlannerNode,
    CoordinatorNode,
    ExecutorNode,
    ResponseNode,
    PlanRefinementNode,
    route_from_understanding,
    route_from_coordinator,
    route_after_tools,
    route_from_planner,
    route_from_sub_agent_executor,
    route_from_plan_review,
    route_from_refinement,
)
from agent.nodes.sub_agent_executor import (
    SubAgentExecutorNode,
    PlanReviewNode,
    ResultSynthesisNode
)
from agent.tools import ToolRegistry
from agent.sub_agents.registry import SubAgentRegistry
from app.data.conversation import ConversationManager, Conversation, Message, MessageRole

logger = logging.getLogger(__name__)


class FilmetoAgent:
    """
    Main agent class for Filmeto AI interactions with multi-agent architecture.
    
    Provides:
    - Multi-agent film production workflow
    - Question understanding and intelligent routing
    - Plan-based execution with sub-agents
    - Streaming conversation interface
    - LangGraph-based agent workflow
    - Tool calling capabilities
    - Conversation history management
    
    The agent system models a film production team:
    - User acts as Executive Producer (出品人)
    - Production Agent: Producer - overall project management
    - Director Agent: Creative vision and scene direction
    - Screenwriter Agent: Script and story development
    - Actor Agent: Character portrayal and performance
    - MakeupArtist Agent: Costume, makeup, and styling
    - Supervisor Agent: Continuity and script supervision
    - SoundMixer Agent: Audio mixing and sound design
    - Editor Agent: Video editing and final assembly
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
        self.model = model
        self.temperature = temperature
        
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
            self.llm = None
            logger.warning("⚠️ Warning: No OpenAI API key provided. Agent will not function until API key is set.")
            logger.warning("   Please set API key in workspace settings (ai_services.openai_api_key) or environment variable (OPENAI_API_KEY)")
            return
        
        self.llm = ChatOpenAI(**llm_kwargs)
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry(workspace=workspace, project=project)
        self.tools = self.tool_registry.get_all_tools()
        
        # Initialize sub-agent registry
        self.sub_agent_registry = SubAgentRegistry(llm=self.llm)
        
        # Initialize conversation manager
        self.conversation_manager = project.get_conversation_manager() if project else None
        self.current_conversation: Optional[Conversation] = None

        # Memory for checkpointing
        self.memory = MemorySaver()

        # Initialize graph
        self.graph = self._build_multi_agent_graph()
    
    def _build_multi_agent_graph(self) -> StateGraph:
        """
        Build the multi-agent LangGraph workflow.
        
        The workflow follows this structure:
        
        1. question_understanding: Analyze user request, determine if multi-agent needed
           → If simple: coordinator
           → If complex: planner
        
        2. coordinator: Handle simple tasks with tools
           → use_tools: Execute tool calls
           → respond: Generate response
        
        3. planner: Create execution plan for complex tasks
           → execute_sub_agent_plan: Execute plan with sub-agents
        
        4. execute_sub_agent_plan: Execute tasks using sub-agents
           → Continue until all tasks done
           → review_plan: Review results
        
        5. review_plan: Check execution quality
           → refine_plan: If refinement needed
           → synthesize_results: If successful
        
        6. refine_plan: Adjust plan based on results
           → execute_sub_agent_plan: Re-execute
           → synthesize_results: If no more refinement
        
        7. synthesize_results: Combine sub-agent results
           → respond: Generate final response
        
        8. respond: Generate user-facing response
           → END
        """
        if not self.llm:
            raise ValueError("Cannot build graph: LLM not initialized. API key is required.")
        
        # Create nodes
        question_understanding = QuestionUnderstandingNode(self.llm, self.sub_agent_registry)
        coordinator = CoordinatorNode(self.llm, self.tools)
        planner = PlannerNode(self.llm, self.sub_agent_registry)
        executor = ExecutorNode(self.llm, self.tools)
        responder = ResponseNode(self.llm)
        
        # Create sub-agent nodes
        sub_agent_executor = SubAgentExecutorNode(
            self.sub_agent_registry,
            self.tool_registry,
            self.workspace,
            self.project
        )
        plan_review = PlanReviewNode(self.llm)
        plan_refinement = PlanRefinementNode(self.llm, self.sub_agent_registry)
        result_synthesis = ResultSynthesisNode(self.llm)
        
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add all nodes
        workflow.add_node("question_understanding", question_understanding)
        workflow.add_node("coordinator", coordinator)
        workflow.add_node("planner", planner)
        workflow.add_node("use_tools", executor)
        workflow.add_node("respond", responder)
        workflow.add_node("execute_sub_agent_plan", sub_agent_executor)
        workflow.add_node("review_plan", plan_review)
        workflow.add_node("refine_plan", plan_refinement)
        workflow.add_node("synthesize_results", result_synthesis)
        
        # Set entry point
        workflow.set_entry_point("question_understanding")
        
        # Add edges from question_understanding
        workflow.add_conditional_edges(
            "question_understanding",
            route_from_understanding,
            {
                "planner": "planner",
                "coordinator": "coordinator"
            }
        )
        
        # Add edges from coordinator
        workflow.add_conditional_edges(
            "coordinator",
            route_from_coordinator,
            {
                "use_tools": "use_tools",
                "respond": "respond",
                "end": END
            }
        )
        
        # Add edge from tools back to coordinator
        workflow.add_conditional_edges(
            "use_tools",
            route_after_tools,
            {
                "coordinator": "coordinator",
                "end": END
            }
        )
        
        # Add edges from planner
        workflow.add_conditional_edges(
            "planner",
            route_from_planner,
            {
                "execute_sub_agent_plan": "execute_sub_agent_plan",
                "coordinator": "coordinator"
            }
        )
        
        # Add edges from sub-agent executor
        workflow.add_conditional_edges(
            "execute_sub_agent_plan",
            route_from_sub_agent_executor,
            {
                "execute_sub_agent_plan": "execute_sub_agent_plan",
                "review_plan": "review_plan",
                "end": END
            }
        )
        
        # Add edges from plan review
        workflow.add_conditional_edges(
            "review_plan",
            route_from_plan_review,
            {
                "refine_plan": "refine_plan",
                "synthesize_results": "synthesize_results",
                "respond": "respond"
            }
        )
        
        # Add edges from plan refinement
        workflow.add_conditional_edges(
            "refine_plan",
            route_from_refinement,
            {
                "execute_sub_agent_plan": "execute_sub_agent_plan",
                "synthesize_results": "synthesize_results"
            }
        )
        
        # Add edge from synthesis to respond
        workflow.add_edge("synthesize_results", "respond")
        
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
        messages = []
        for msg in conversation.messages:
            if msg.role == MessageRole.USER:
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                if msg.tool_calls:
                    messages.append(AIMessage(content=msg.content, tool_calls=msg.tool_calls))
                else:
                    messages.append(AIMessage(content=msg.content))
            elif msg.role == MessageRole.TOOL:
                messages.append(ToolMessage(
                    content=msg.content,
                    tool_call_id=msg.tool_call_id
                ))
            elif msg.role == MessageRole.SYSTEM:
                messages.append(SystemMessage(content=msg.content))
        
        # Initial state
        initial_state: AgentState = {
            "messages": messages,
            "next_action": "question_understanding",
            "context": {},
            "iteration_count": 0,
            "execution_plan": None,
            "current_task_index": 0,
            "sub_agent_results": {},
            "requires_multi_agent": False,
            "plan_refinement_count": 0
        }
        
        # Stream response
        full_response = ""
        final_messages = []

        # Create config with thread_id for memory checkpointer
        config = {"configurable": {"thread_id": conversation.conversation_id}}

        if self.streaming:
            # Use astream for streaming
            async for event in self.graph.astream(initial_state, config=config):
                for node_name, node_output in event.items():
                    if "messages" in node_output:
                        # Keep track of all messages
                        final_messages = node_output["messages"]
                        
                        last_message = node_output["messages"][-1]
                        if isinstance(last_message, AIMessage):
                            content = last_message.content
                            if content and content not in full_response:
                                new_content = content[len(full_response):]
                                full_response = content

                                # Yield token by token
                                for char in new_content:
                                    if on_token:
                                        on_token(char)
                                    yield char
                                    await asyncio.sleep(0.01)
        else:
            # Non-streaming mode
            result = await self.graph.ainvoke(initial_state, config=config)
            if "messages" in result:
                final_messages = result["messages"]
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    full_response = last_message.content
                    if on_token:
                        on_token(full_response)
                    yield full_response
        
        # Save all new messages to conversation
        num_existing_messages = len(messages)
        new_messages = final_messages[num_existing_messages:]
        
        for msg in new_messages:
            if isinstance(msg, AIMessage):
                assistant_msg = Message(
                    role=MessageRole.ASSISTANT,
                    content=msg.content or "",
                    timestamp=datetime.now().isoformat(),
                    tool_calls=msg.tool_calls if hasattr(msg, 'tool_calls') and msg.tool_calls else None
                )
                conversation.add_message(assistant_msg)
            elif isinstance(msg, ToolMessage):
                tool_msg = Message(
                    role=MessageRole.TOOL,
                    content=msg.content,
                    timestamp=datetime.now().isoformat(),
                    tool_call_id=msg.tool_call_id
                )
                conversation.add_message(tool_msg)
        
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
            llm_kwargs = {
                "model": self.model,
                "temperature": self.temperature,
                "streaming": self.streaming,
                "api_key": api_key
            }
            
            self.llm = ChatOpenAI(**llm_kwargs)
            
            # Update sub-agent registry with new LLM
            self.sub_agent_registry = SubAgentRegistry(llm=self.llm)
        
        # Update tool registry
        self.tool_registry.update_context(workspace, project)
        
        # Rebuild graph with updated tools
        self.tools = self.tool_registry.get_all_tools()
        try:
            self.graph = self._build_multi_agent_graph()
        except ValueError:
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
