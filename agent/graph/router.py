"""Router functions for agent graph navigation."""

from typing import Literal
from langchain_core.messages import ToolMessage

from agent.graph.state import AgentState


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
    if messages:
        last_message = messages[-1]
        # Return to coordinator if we have a ToolMessage (tool execution result)
        if isinstance(last_message, ToolMessage):
            return "coordinator"
        # Also return to coordinator if we have an AI message with tool_calls (meaning tools were requested but not yet executed)
        from langchain_core.messages import AIMessage
        if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
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
