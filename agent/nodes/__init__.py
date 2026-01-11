"""LangGraph nodes for Filmeto agent with multi-agent architecture."""

from typing import Any, Dict, List, Literal, TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator
import json
import re


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
    requires_multi_agent: bool  # Whether multi-agent collaboration is needed
    plan_refinement_count: int  # Number of plan refinements


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
            ("system", f"""You are a question understanding system for Filmeto, an AI-powered film/video creation platform.

Your role is to:
1. Understand user questions and requests
2. Determine if the request requires multi-agent collaboration
3. Identify which sub-agents might be needed

The user is the "Executive Producer" (出品人) who commissions the film production team.

Available sub-agents and their capabilities:
{capabilities_str}

Film Production Workflow:
1. Pre-Production: Script writing, storyboarding, costume design, character design
2. Production: Scene shooting, directing, acting, makeup application
3. Post-Production: Video editing, sound mixing, color grading, final assembly

Analysis criteria:
- Simple queries about project state: Use coordinator directly (no multi-agent)
- Single-step tasks: Use coordinator with tools (no multi-agent)
- Creative tasks requiring film production skills: Require sub-agent collaboration
- Multi-step tasks with different specialized skills: Require sub-agent collaboration

For each user request, analyze:
1. Does this require multiple specialized film production skills?
2. Which agents would be most suitable based on their skills?
3. What is the complexity level?

You MUST respond with valid JSON format:
{{{{
    "requires_sub_agents": true/false,
    "complexity": "simple" | "moderate" | "complex",
    "suggested_agents": ["AgentName1", "AgentName2"],
    "task_type": "pre_production" | "production" | "post_production" | "full_production" | "query",
    "reasoning": "Brief explanation of why this needs/doesn't need multi-agent collaboration"
}}}}"""),
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
                "messages": [],
                "next_action": "coordinator",
                "context": context,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "execution_plan": None,
                "current_task_index": 0,
                "sub_agent_results": {},
                "requires_multi_agent": False,
                "plan_refinement_count": 0
            }
        
        # Format prompt
        formatted_prompt = self.prompt.format_messages(messages=messages)
        
        # Get LLM response
        response = self.llm.invoke(formatted_prompt)
        
        # Parse response
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            analysis = {
                "requires_sub_agents": False,
                "complexity": "simple",
                "suggested_agents": [],
                "task_type": "query",
                "reasoning": "Could not parse analysis, defaulting to coordinator"
            }
        
        # Store analysis in context
        context["question_analysis"] = analysis
        context["original_request"] = user_message
        
        # Determine next action
        requires_multi_agent = analysis.get("requires_sub_agents", False)
        if requires_multi_agent:
            next_action = "planner"
        else:
            next_action = "coordinator"
        
        # Create analysis message for transparency
        analysis_msg = f"[Question Analysis] Task type: {analysis.get('task_type', 'unknown')}, " \
                       f"Complexity: {analysis.get('complexity', 'unknown')}, " \
                       f"Multi-agent required: {requires_multi_agent}"
        if requires_multi_agent:
            analysis_msg += f", Suggested agents: {', '.join(analysis.get('suggested_agents', []))}"
        
        return {
            "messages": [AIMessage(content=analysis_msg)],
            "next_action": next_action,
            "context": context,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "execution_plan": None,
            "current_task_index": 0,
            "sub_agent_results": {},
            "requires_multi_agent": requires_multi_agent,
            "plan_refinement_count": 0
        }


# ============================================================================
# Planner Node (for Multi-Agent Collaboration)
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
            ("system", f"""You are a film production planner for Filmeto, an AI-powered video creation platform.

Your role is to create detailed execution plans using sub-agent skills to complete complex film production requests.

Available sub-agents and their skills:
{capabilities_str}

Film Production Workflow Guidelines:
1. Pre-Production Phase:
   - Screenwriter: script_outline → script_detail → dialogue_writing
   - Director: storyboard → scene_composition → shot_planning
   - MakeupArtist: costume_design → character_makeup → appearance_styling
   - Production: project_planning → resource_allocation

2. Production Phase:
   - Director: scene_direction
   - Actor: character_portrayal → performance_execution
   - Supervisor: continuity_tracking → shot_logging

3. Post-Production Phase:
   - Editor: video_editing → scene_assembly → pacing_control → final_assembly
   - SoundMixer: sound_design → audio_mixing → audio_quality_control
   - Supervisor: script_supervision

For each user request, create an execution plan with:
1. Sequence of tasks, each assigned to an appropriate sub-agent
2. Each task specifies: agent_name, skill_name, parameters
3. Dependencies between tasks (task_id references)
4. Expected outcomes

You MUST respond with valid JSON format:
{{{{
    "description": "Overall plan description",
    "phase": "pre_production" | "production" | "post_production" | "full_production",
    "tasks": [
        {{{{
            "task_id": 1,
            "agent_name": "Screenwriter",
            "skill_name": "script_outline",
            "parameters": {{{{"topic": "...", "genre": "..."}}}},
            "dependencies": [],
            "expected_output": "Script outline with story structure"
        }}}},
        {{{{
            "task_id": 2,
            "agent_name": "Director",
            "skill_name": "storyboard",
            "parameters": {{{{"script": "from_task_1"}}}},
            "dependencies": [1],
            "expected_output": "Visual storyboard"
        }}}}
    ],
    "success_criteria": "What determines successful completion"
}}}}

Create a detailed execution plan for the user's request, ensuring proper task sequencing and dependencies."""),
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
        
        # Add analysis context to messages for planner
        analysis_context = f"[Context] Suggested agents: {suggested_agents}, Task type: {analysis.get('task_type', 'unknown')}"
        augmented_messages = list(messages) + [SystemMessage(content=analysis_context)]
        
        # Format prompt
        formatted_prompt = self.prompt.format_messages(messages=augmented_messages)
        
        # Get plan from LLM
        response = self.llm.invoke(formatted_prompt)
        
        # Parse plan (try to extract JSON from response)
        plan_content = response.content
        execution_plan = None
        
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', plan_content)
            if json_match:
                execution_plan = json.loads(json_match.group())
            else:
                execution_plan = json.loads(plan_content)
        except (json.JSONDecodeError, AttributeError):
            # Fallback: create a simple plan structure
            execution_plan = {
                "tasks": [],
                "description": plan_content,
                "phase": "unknown",
                "success_criteria": "Complete all tasks"
            }
        
        # Validate and structure the plan
        if "tasks" not in execution_plan:
            execution_plan["tasks"] = []
        
        # Store plan in context
        context["plan_description"] = execution_plan.get("description", plan_content)
        context["plan_phase"] = execution_plan.get("phase", "unknown")
        
        # Create plan message
        task_count = len(execution_plan.get("tasks", []))
        plan_msg = f"[Execution Plan] Created plan with {task_count} tasks for phase: {execution_plan.get('phase', 'unknown')}\n"
        plan_msg += f"Description: {execution_plan.get('description', 'N/A')[:200]}..."
        
        return {
            "messages": [AIMessage(content=plan_msg)],
            "next_action": "execute_sub_agent_plan",
            "context": context,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "execution_plan": execution_plan,
            "current_task_index": 0,
            "sub_agent_results": {},
            "requires_multi_agent": True,
            "plan_refinement_count": state.get("plan_refinement_count", 0)
        }


# ============================================================================
# Coordinator Node (for Simple Tasks)
# ============================================================================

class CoordinatorNode:
    """
    Coordinator node that handles simple tasks and tool calls.
    
    The coordinator is responsible for:
    - Understanding user intent for simple tasks
    - Executing tool calls directly
    - Managing simple conversation flow
    """
    
    def __init__(self, llm: ChatOpenAI, tools: List[Any]):
        """Initialize coordinator node."""
        self.llm = llm
        self.tools = tools
        
        # Create coordinator prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a coordinator for Filmeto, an AI-powered video creation platform.

Your role is to:
1. Handle simple queries and tasks that don't require multi-agent collaboration
2. Use tools to get project information, manage resources, and create tasks
3. Provide helpful responses to user questions

Available capabilities:
- Project management (get project info, timeline management)
- Character management (list, view, create characters)
- Resource management (list images, videos, audio files)
- Task creation (text2img, img2video, etc.)
- Timeline operations

Available tools: {tool_names}

When responding:
- If it's a query about project state, use appropriate tools
- If it's a simple task, execute it directly
- Provide clear, helpful responses"""),
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
            "iteration_count": state.get("iteration_count", 0) + 1,
            "execution_plan": state.get("execution_plan"),
            "current_task_index": state.get("current_task_index", 0),
            "sub_agent_results": state.get("sub_agent_results", {}),
            "requires_multi_agent": state.get("requires_multi_agent", False),
            "plan_refinement_count": state.get("plan_refinement_count", 0)
        }


# ============================================================================
# Executor Node
# ============================================================================

class ExecutorNode:
    """
    Executor node that carries out tool calls.
    
    The executor:
    - Executes tool calls from the coordinator
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
            "iteration_count": state.get("iteration_count", 0),
            "execution_plan": state.get("execution_plan"),
            "current_task_index": state.get("current_task_index", 0),
            "sub_agent_results": state.get("sub_agent_results", {}),
            "requires_multi_agent": state.get("requires_multi_agent", False),
            "plan_refinement_count": state.get("plan_refinement_count", 0)
        }


# ============================================================================
# Response Node
# ============================================================================

class ResponseNode:
    """
    Response node that generates final responses to users.
    
    The responder:
    - Synthesizes information from tool results or sub-agent results
    - Formats responses in a user-friendly way
    - Provides context and explanations
    """
    
    def __init__(self, llm: ChatOpenAI):
        """Initialize response node."""
        self.llm = llm
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Filmeto Assistant, helping users create films and videos with AI.

Your role is to:
- Provide clear, helpful responses
- Explain tool results or execution plan results in user-friendly language
- Summarize what was accomplished
- Suggest next steps when appropriate

The user is the "Executive Producer" (出品人) who commissions the film production team.

When responding:
- Use markdown formatting for better readability
- Highlight important information
- Provide actionable suggestions
- Be encouraging and professional"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
    
    def __call__(self, state: AgentState) -> AgentState:
        """Generate final response."""
        messages = state["messages"]
        context = state.get("context", {})
        sub_agent_results = state.get("sub_agent_results", {})
        
        # Add context about multi-agent results if available
        if sub_agent_results:
            results_summary = "\n[Sub-agent Results Summary]\n"
            for task_id, result in sorted(sub_agent_results.items()):
                agent = result.get("agent", "Unknown")
                skill = result.get("skill", "Unknown")
                status = result.get("status", "unknown")
                message = result.get("message", "")[:100]
                results_summary += f"- {agent}/{skill}: {status} - {message}\n"
            messages = list(messages) + [SystemMessage(content=results_summary)]
        
        formatted_prompt = self.prompt.format_messages(messages=messages)
        response = self.llm.invoke(formatted_prompt)
        
        return {
            "messages": [response],
            "next_action": "end",
            "context": context,
            "iteration_count": state.get("iteration_count", 0),
            "execution_plan": state.get("execution_plan"),
            "current_task_index": state.get("current_task_index", 0),
            "sub_agent_results": sub_agent_results,
            "requires_multi_agent": state.get("requires_multi_agent", False),
            "plan_refinement_count": state.get("plan_refinement_count", 0)
        }


# ============================================================================
# Plan Refinement Node
# ============================================================================

class PlanRefinementNode:
    """
    Plan refinement node that adjusts execution plans based on results.
    
    This node:
    - Reviews execution results
    - Identifies failed or low-quality tasks
    - Creates refined plan for rework
    """
    
    def __init__(self, llm: ChatOpenAI, sub_agent_registry: Any):
        """Initialize plan refinement node."""
        self.llm = llm
        self.sub_agent_registry = sub_agent_registry
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a plan refinement system for Filmeto film production.

Review the execution results and determine if refinement is needed.

For each failed or low-quality task, decide:
1. Should it be retried with different parameters?
2. Should a different agent handle it?
3. Should additional tasks be added?

You MUST respond with valid JSON:
{{
    "needs_refinement": true/false,
    "refinement_type": "retry" | "reassign" | "add_tasks" | "complete",
    "refined_tasks": [
        {{
            "task_id": 100,
            "agent_name": "AgentName",
            "skill_name": "skill_name",
            "parameters": {{}},
            "dependencies": [],
            "reason": "Why this task is added/modified"
        }}
    ],
    "reasoning": "Explanation of refinement decision"
}}"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
    
    def __call__(self, state: AgentState) -> AgentState:
        """Refine execution plan based on results."""
        messages = state["messages"]
        context = state.get("context", {})
        execution_plan = state.get("execution_plan", {})
        sub_agent_results = state.get("sub_agent_results", {})
        plan_refinement_count = state.get("plan_refinement_count", 0)
        
        # Limit refinement iterations
        if plan_refinement_count >= 3:
            return {
                "messages": [AIMessage(content="[Plan Refinement] Maximum refinement attempts reached. Proceeding to synthesis.")],
                "next_action": "synthesize_results",
                "context": context,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "execution_plan": execution_plan,
                "current_task_index": state.get("current_task_index", 0),
                "sub_agent_results": sub_agent_results,
                "requires_multi_agent": True,
                "plan_refinement_count": plan_refinement_count
            }
        
        # Analyze results
        failed_tasks = []
        low_quality_tasks = []
        for task_id, result in sub_agent_results.items():
            if result.get("status") == "failed":
                failed_tasks.append((task_id, result))
            elif result.get("quality_score", 1.0) < 0.7:
                low_quality_tasks.append((task_id, result))
        
        # If all tasks successful with good quality, proceed to synthesis
        if not failed_tasks and not low_quality_tasks:
            return {
                "messages": [AIMessage(content="[Plan Refinement] All tasks completed successfully with good quality.")],
                "next_action": "synthesize_results",
                "context": context,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "execution_plan": execution_plan,
                "current_task_index": state.get("current_task_index", 0),
                "sub_agent_results": sub_agent_results,
                "requires_multi_agent": True,
                "plan_refinement_count": plan_refinement_count
            }
        
        # Add results context to messages
        results_msg = f"[Results for Refinement] Failed: {len(failed_tasks)}, Low quality: {len(low_quality_tasks)}"
        augmented_messages = list(messages) + [SystemMessage(content=results_msg)]
        
        # Get refinement plan
        formatted_prompt = self.prompt.format_messages(messages=augmented_messages)
        response = self.llm.invoke(formatted_prompt)
        
        # Parse refinement
        try:
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                refinement = json.loads(json_match.group())
            else:
                refinement = {"needs_refinement": False, "refinement_type": "complete"}
        except json.JSONDecodeError:
            refinement = {"needs_refinement": False, "refinement_type": "complete"}
        
        if refinement.get("needs_refinement", False) and refinement.get("refined_tasks"):
            # Add refined tasks to plan
            current_tasks = execution_plan.get("tasks", [])
            refined_tasks = refinement.get("refined_tasks", [])
            execution_plan["tasks"] = current_tasks + refined_tasks
            
            return {
                "messages": [AIMessage(content=f"[Plan Refinement] Added {len(refined_tasks)} tasks for rework.")],
                "next_action": "execute_sub_agent_plan",
                "context": context,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "execution_plan": execution_plan,
                "current_task_index": len(current_tasks),  # Start from new tasks
                "sub_agent_results": sub_agent_results,
                "requires_multi_agent": True,
                "plan_refinement_count": plan_refinement_count + 1
            }
        
        return {
            "messages": [AIMessage(content="[Plan Refinement] No further refinement needed.")],
            "next_action": "synthesize_results",
            "context": context,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "execution_plan": execution_plan,
            "current_task_index": state.get("current_task_index", 0),
            "sub_agent_results": sub_agent_results,
            "requires_multi_agent": True,
            "plan_refinement_count": plan_refinement_count
        }


# ============================================================================
# Router Functions
# ============================================================================

def route_from_understanding(state: AgentState) -> Literal["planner", "coordinator"]:
    """Route from question understanding to next node."""
    next_action = state.get("next_action", "coordinator")
    if next_action == "planner":
        return "planner"
    return "coordinator"


def route_from_coordinator(state: AgentState) -> Literal["use_tools", "respond", "end"]:
    """Route from coordinator to next node."""
    next_action = state.get("next_action", "respond")
    iteration_count = state.get("iteration_count", 0)
    
    # Prevent infinite loops
    if iteration_count > 10:
        return "end"
    
    if next_action == "use_tools":
        return "use_tools"
    elif next_action == "respond":
        return "respond"
    return "end"


def route_after_tools(state: AgentState) -> Literal["coordinator", "end"]:
    """Route after tool execution."""
    messages = state["messages"]
    
    # Check if we have tool results
    if messages and isinstance(messages[-1], ToolMessage):
        return "coordinator"
    
    return "end"


def route_from_planner(state: AgentState) -> Literal["execute_sub_agent_plan", "coordinator"]:
    """Route from planner to execution."""
    execution_plan = state.get("execution_plan")
    if execution_plan and execution_plan.get("tasks"):
        return "execute_sub_agent_plan"
    return "coordinator"


def route_from_sub_agent_executor(state: AgentState) -> Literal["execute_sub_agent_plan", "review_plan", "end"]:
    """Route from sub-agent executor."""
    next_action = state.get("next_action", "end")
    
    if next_action == "execute_sub_agent_plan":
        return "execute_sub_agent_plan"
    elif next_action == "review_plan":
        return "review_plan"
    return "end"


def route_from_plan_review(state: AgentState) -> Literal["refine_plan", "synthesize_results", "respond"]:
    """Route from plan review."""
    next_action = state.get("next_action", "respond")
    
    if next_action == "refine_plan":
        return "refine_plan"
    elif next_action == "synthesize_results":
        return "synthesize_results"
    return "respond"


def route_from_refinement(state: AgentState) -> Literal["execute_sub_agent_plan", "synthesize_results"]:
    """Route from plan refinement."""
    next_action = state.get("next_action", "synthesize_results")
    
    if next_action == "execute_sub_agent_plan":
        return "execute_sub_agent_plan"
    return "synthesize_results"


# ============================================================================
# Legacy Router Functions (for backward compatibility)
# ============================================================================

def should_continue(state: AgentState) -> Literal["use_tools", "respond", "plan", "end"]:
    """Determine the next node based on state (legacy)."""
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
        "planner": "plan",
        "execute_plan": "use_tools",
        "coordinator": "use_tools",
        "end": "end"
    }
    
    return action_map.get(next_action, "end")


# Re-export sub-agent executor nodes
from agent.nodes.sub_agent_executor import (
    SubAgentExecutorNode,
    PlanReviewNode,
    ResultSynthesisNode
)

__all__ = [
    'AgentState',
    'QuestionUnderstandingNode',
    'PlannerNode',
    'CoordinatorNode',
    'ExecutorNode',
    'ResponseNode',
    'PlanRefinementNode',
    'SubAgentExecutorNode',
    'PlanReviewNode',
    'ResultSynthesisNode',
    'route_from_understanding',
    'route_from_coordinator',
    'route_after_tools',
    'route_from_planner',
    'route_from_sub_agent_executor',
    'route_from_plan_review',
    'route_from_refinement',
    'should_continue',
]
