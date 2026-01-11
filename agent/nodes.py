"""LangGraph nodes for Filmeto agent."""

from typing import Any, Dict, List, Literal, TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator
import json


# ============================================================================
# State Definition
# ============================================================================

class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_action: str
    context: Dict[str, Any]
    iteration_count: int
    execution_plan: Optional[Dict[str, Any]]  # Execution plan with sub-agent tasks
    current_task_index: int  # Current task index in execution plan
    sub_agent_results: Dict[str, Any]  # Results from sub-agent executions


# ============================================================================
# Question Understanding Node
# ============================================================================

class QuestionUnderstandingNode:
    """
    Question understanding node that analyzes user questions.
    
    This node:
    - Analyzes user questions to understand intent
    - Determines if sub-agents are needed for collaboration
    - Routes to planner if sub-agents are needed, or to coordinator for simple tasks
    """
    
    def __init__(self, llm: ChatOpenAI, sub_agent_registry: Any):
        """Initialize question understanding node."""
        self.llm = llm
        self.sub_agent_registry = sub_agent_registry
        
        # Get agent capabilities
        capabilities = sub_agent_registry.get_agent_capabilities()
        capabilities_str = self._format_capabilities(capabilities)
        
        # Create question understanding prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a question understanding system for Filmeto, an AI-powered video creation platform.

Your role is to:
1. Understand user questions and requests
2. Determine if the request requires multi-agent collaboration
3. Identify which sub-agents might be needed

Available sub-agents and their capabilities:
{capabilities}

Analysis criteria:
- Simple queries about project state: Use coordinator directly
- Single-step tasks: Use coordinator with tools
- Complex multi-step tasks requiring different skills: Require sub-agent collaboration
- Creative tasks (script writing, directing, editing): Require sub-agent collaboration

For each user request, analyze:
1. Does this require multiple specialized skills?
2. Which agents would be most suitable?
3. What is the complexity level?

Respond with JSON format:
{{
    "requires_sub_agents": true/false,
    "complexity": "simple|moderate|complex",
    "suggested_agents": ["AgentName1", "AgentName2"],
    "reasoning": "Brief explanation"
}}""".format(capabilities=capabilities_str)),
            MessagesPlaceholder(variable_name="messages"),
        ])
    
    def _format_capabilities(self, capabilities: Dict[str, List[Dict[str, str]]]) -> str:
        """Format agent capabilities for prompt."""
        lines = []
        for agent_name, skills in capabilities.items():
            lines.append(f"\n{agent_name}:")
            for skill in skills:
                lines.append(f"  - {skill['name']}: {skill['description']}")
        return "\n".join(lines)
    
    def __call__(self, state: AgentState) -> AgentState:
        """Process question understanding."""
        messages = state["messages"]
        context = state.get("context", {})
        
        # Get the last user message
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        if not user_message:
            # No user message found, proceed to coordinator
            return {
                "messages": messages,
                "next_action": "coordinator",
                "context": context,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "execution_plan": None,
                "current_task_index": 0,
                "sub_agent_results": {}
            }
        
        # Format prompt
        formatted_prompt = self.prompt.format_messages(messages=messages)
        
        # Get LLM response
        response = self.llm.invoke(formatted_prompt)
        
        # Parse response
        try:
            analysis = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            analysis = {
                "requires_sub_agents": False,
                "complexity": "simple",
                "suggested_agents": [],
                "reasoning": "Could not parse analysis"
            }
        
        # Store analysis in context
        context["question_analysis"] = analysis
        
        # Determine next action
        if analysis.get("requires_sub_agents", False):
            next_action = "planner"
        else:
            next_action = "coordinator"
        
        return {
            "messages": [response],
            "next_action": next_action,
            "context": context,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "execution_plan": None,
            "current_task_index": 0,
            "sub_agent_results": {}
        }


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
    Planner node that creates execution plans based on sub-agent skills.
    
    The planner:
    - Creates execution plans using sub-agent skills
    - Breaks down complex tasks into sub-agent tasks
    - Determines task dependencies and sequencing
    """
    
    def __init__(self, llm: ChatOpenAI, sub_agent_registry: Any):
        """Initialize planner node."""
        self.llm = llm
        self.sub_agent_registry = sub_agent_registry
        
        # Get agent capabilities
        capabilities = sub_agent_registry.get_agent_capabilities()
        capabilities_str = self._format_capabilities(capabilities)
        
        # Create planner prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a planner for Filmeto, an AI-powered video creation platform.

Your role is to create execution plans using sub-agent skills to complete complex user requests.

Available sub-agents and their skills:
{capabilities}

For each user request, create an execution plan with:
1. Sequence of tasks, each assigned to an appropriate sub-agent
2. Each task specifies: agent_name, skill_name, parameters
3. Dependencies between tasks
4. Expected outcomes

Example plan format (JSON):
{{
    "tasks": [
        {{
            "task_id": 1,
            "agent_name": "Screenwriter",
            "skill_name": "script_outline",
            "parameters": {{"topic": "..."}},
            "dependencies": []
        }},
        {{
            "task_id": 2,
            "agent_name": "Director",
            "skill_name": "storyboard",
            "parameters": {{"script": "..."}},
            "dependencies": [1]
        }}
    ],
    "description": "Plan description"
}}

Create a detailed execution plan for the user's request.""").format(capabilities=capabilities_str),
            MessagesPlaceholder(variable_name="messages"),
        ])
    
    def _format_capabilities(self, capabilities: Dict[str, List[Dict[str, str]]]) -> str:
        """Format agent capabilities for prompt."""
        lines = []
        for agent_name, skills in capabilities.items():
            lines.append(f"\n{agent_name}:")
            for skill in skills:
                lines.append(f"  - {skill['name']}: {skill['description']}")
        return "\n".join(lines)
    
    def __call__(self, state: AgentState) -> AgentState:
        """Create an execution plan for the user's request."""
        messages = state["messages"]
        context = state.get("context", {})
        
        # Get question analysis if available
        analysis = context.get("question_analysis", {})
        suggested_agents = analysis.get("suggested_agents", [])
        
        # Format prompt
        formatted_prompt = self.prompt.format_messages(messages=messages)
        
        # Get plan from LLM
        response = self.llm.invoke(formatted_prompt)
        
        # Parse plan (try to extract JSON from response)
        plan_content = response.content
        execution_plan = None
        
        try:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', plan_content)
            if json_match:
                execution_plan = json.loads(json_match.group())
            else:
                execution_plan = json.loads(plan_content)
        except (json.JSONDecodeError, AttributeError):
            # Fallback: create a simple plan structure
            execution_plan = {
                "tasks": [],
                "description": plan_content
            }
        
        # Validate and structure the plan
        if "tasks" not in execution_plan:
            execution_plan["tasks"] = []
        
        # Store plan in state
        context["plan_description"] = execution_plan.get("description", plan_content)
        
        return {
            "messages": [response],
            "next_action": "execute_sub_agent_plan",
            "context": context,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "execution_plan": execution_plan,
            "current_task_index": 0,
            "sub_agent_results": {}
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

