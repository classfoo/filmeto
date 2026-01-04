"""LangGraph nodes for Filmeto agent."""

from typing import Any, Dict, List, Literal, TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator


# ============================================================================
# State Definition
# ============================================================================

class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_action: str
    context: Dict[str, Any]
    iteration_count: int


# ============================================================================
# Coordinator Node
# ============================================================================

class CoordinatorNode:
    """
    Coordinator node that analyzes user requests and decides the next action.
    
    The coordinator is responsible for:
    - Understanding user intent
    - Deciding whether to plan, use tools, or respond directly
    - Managing the overall conversation flow
    """
    
    def __init__(self, llm: ChatOpenAI, tools: List[Any]):
        """Initialize coordinator node."""
        self.llm = llm
        self.tools = tools
        
        # Create coordinator prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a coordinator for Filmeto, an AI-powered video creation platform.

Your role is to:
1. Understand user requests and questions
2. Decide the best approach to handle each request
3. Coordinate between planning, tool usage, and direct responses

Available capabilities:
- Project management (get project info, timeline management)
- Character management (list, view, create characters)
- Resource management (list images, videos, audio files)
- Task creation (text2img, img2video, etc.)
- Timeline operations

When a user asks a question:
- If it's a simple query about project state, use tools directly
- If it's a complex multi-step request, create a plan first
- If it's a general question, respond directly

Available tools: {tool_names}

Analyze the user's request and decide the next action."""),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
    
    def __call__(self, state: AgentState) -> AgentState:
        """Process coordinator logic."""
        messages = state["messages"]
        context = state.get("context", {})
        
        # Format prompt with tool names
        tool_names = [tool.name for tool in self.tools]
        formatted_prompt = self.prompt.format_messages(
            messages=messages,
            tool_names=", ".join(tool_names)
        )
        
        # Get LLM response with tool calling capability
        response = self.llm_with_tools.invoke(formatted_prompt)
        
        # Determine next action based on response
        if response.tool_calls:
            next_action = "use_tools"
        else:
            next_action = "respond"
        
        return {
            "messages": [response],
            "next_action": next_action,
            "context": context,
            "iteration_count": state.get("iteration_count", 0) + 1
        }


# ============================================================================
# Planner Node
# ============================================================================

class PlannerNode:
    """
    Planner node that creates execution plans for complex tasks.
    
    The planner breaks down complex user requests into:
    - Sequence of steps
    - Required tools for each step
    - Dependencies between steps
    """
    
    def __init__(self, llm: ChatOpenAI, tools: List[Any]):
        """Initialize planner node."""
        self.llm = llm
        self.tools = tools
        
        # Create planner prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a planner for Filmeto, an AI-powered video creation platform.

Your role is to break down complex user requests into actionable steps.

Available tools: {tool_names}

For each user request, create a plan with:
1. Clear sequence of steps
2. Which tools to use for each step
3. Expected outcomes

Example plan format:
Step 1: Get current project information using 'get_project_info'
Step 2: List available characters using 'list_characters'
Step 3: Create a new task using 'create_task' with the selected character

Create a detailed plan for the user's request."""),
            MessagesPlaceholder(variable_name="messages"),
        ])
    
    def __call__(self, state: AgentState) -> AgentState:
        """Create a plan for the user's request."""
        messages = state["messages"]
        context = state.get("context", {})
        
        # Format prompt with tool names
        tool_names = [tool.name for tool in self.tools]
        formatted_prompt = self.prompt.format_messages(
            messages=messages,
            tool_names=", ".join(tool_names)
        )
        
        # Get plan from LLM
        response = self.llm.invoke(formatted_prompt)
        
        # Store plan in context
        context["plan"] = response.content
        
        return {
            "messages": [response],
            "next_action": "execute_plan",
            "context": context,
            "iteration_count": state.get("iteration_count", 0) + 1
        }


# ============================================================================
# Executor Node
# ============================================================================

class ExecutorNode:
    """
    Executor node that carries out plans and tool calls.
    
    The executor:
    - Executes tool calls from the coordinator
    - Follows plans created by the planner
    - Handles tool results and errors
    """
    
    def __init__(self, llm: ChatOpenAI, tools: List[Any]):
        """Initialize executor node."""
        self.llm = llm
        self.tools = tools
        self.tool_node = ToolNode(tools)
    
    def __call__(self, state: AgentState) -> AgentState:
        """Execute tools based on the current state."""
        messages = state["messages"]
        
        # Execute tools using LangGraph's ToolNode
        result = self.tool_node.invoke({"messages": messages})
        
        return {
            "messages": result["messages"],
            "next_action": "coordinator",  # Return to coordinator after execution
            "context": state.get("context", {}),
            "iteration_count": state.get("iteration_count", 0)
        }


# ============================================================================
# Response Node
# ============================================================================

class ResponseNode:
    """
    Response node that generates final responses to users.
    
    The responder:
    - Synthesizes information from tool results
    - Formats responses in a user-friendly way
    - Provides context and explanations
    """
    
    def __init__(self, llm: ChatOpenAI):
        """Initialize response node."""
        self.llm = llm
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Filmeto Assistant, helping users create videos with AI.

Your role is to:
- Provide clear, helpful responses
- Explain tool results in user-friendly language
- Suggest next steps when appropriate
- Be concise but informative

When responding:
- Use markdown formatting for better readability
- Highlight important information
- Provide actionable suggestions
- Be encouraging and supportive"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
    
    def __call__(self, state: AgentState) -> AgentState:
        """Generate final response."""
        messages = state["messages"]
        
        formatted_prompt = self.prompt.format_messages(messages=messages)
        response = self.llm.invoke(formatted_prompt)
        
        return {
            "messages": [response],
            "next_action": "end",
            "context": state.get("context", {}),
            "iteration_count": state.get("iteration_count", 0)
        }


# ============================================================================
# Router Functions
# ============================================================================

def should_continue(state: AgentState) -> Literal["use_tools", "respond", "plan", "end"]:
    """Determine the next node based on state."""
    next_action = state.get("next_action", "end")
    iteration_count = state.get("iteration_count", 0)
    
    # Prevent infinite loops
    if iteration_count > 10:
        return "end"
    
    # Map next_action to actual node names
    action_map = {
        "use_tools": "use_tools",
        "respond": "respond",
        "plan": "plan",
        "execute_plan": "use_tools",
        "coordinator": "coordinator",
        "end": "end"
    }
    
    return action_map.get(next_action, "end")


def route_after_tools(state: AgentState) -> Literal["coordinator", "end"]:
    """Route after tool execution."""
    messages = state["messages"]
    
    # Check if we have tool results
    if messages and isinstance(messages[-1], ToolMessage):
        return "coordinator"
    
    return "end"

