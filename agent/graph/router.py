"""Router functions for agent graph navigation."""

from typing import Literal
from langchain_core.messages import ToolMessage

from agent.graph.state import AgentState
from agent.workflow_logger import workflow_logger


def route_from_understanding(state: AgentState) -> Literal["planner", "coordinator"]:
    """Route from question understanding to next node."""
    flow_id = state.get("flow_id", "unknown")
    next_action = state.get("next_action", "coordinator")
    
    route = "planner" if next_action == "planner" else "coordinator"
    workflow_logger.log_logic_step(flow_id, "Router", "route_from_understanding", {"next_action": next_action, "route": route})
    return route


def route_from_coordinator(state: AgentState) -> Literal["use_tools", "respond", "end"]:
    """Route from coordinator to next node."""
    flow_id = state.get("flow_id", "unknown")
    next_action = state.get("next_action", "respond")
    iteration_count = state.get("iteration_count", 0)
    
    # Prevent infinite loops
    if iteration_count > 10:
        workflow_logger.log_logic_step(flow_id, "Router", "route_from_coordinator", {"reason": "max_iterations", "route": "end"})
        return "end"
    
    route = "end"
    if next_action == "use_tools":
        route = "use_tools"
    elif next_action == "respond":
        route = "respond"
    
    workflow_logger.log_logic_step(flow_id, "Router", "route_from_coordinator", {"next_action": next_action, "route": route})
    return route


def route_after_tools(state: AgentState) -> Literal["coordinator", "end"]:
    """Route after tool execution."""
    flow_id = state.get("flow_id", "unknown")
    messages = state["messages"]
    
    route = "end"
    # Check if we have tool results
    if messages:
        last_message = messages[-1]
        # Return to coordinator if we have a ToolMessage (tool execution result)
        if isinstance(last_message, ToolMessage):
            route = "coordinator"
        # Also return to coordinator if we have an AI message with tool_calls (meaning tools were requested but not yet executed)
        else:
            from langchain_core.messages import AIMessage
            if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                route = "coordinator"
    
    workflow_logger.log_logic_step(flow_id, "Router", "route_after_tools", {"route": route})
    return route


def route_from_planner(state: AgentState) -> Literal["execute_sub_agent_plan", "coordinator"]:
    """Route from planner to execution."""
    flow_id = state.get("flow_id", "unknown")
    execution_plan = state.get("execution_plan")
    
    route = "coordinator"
    if execution_plan and execution_plan.get("tasks"):
        route = "execute_sub_agent_plan"
    
    workflow_logger.log_logic_step(flow_id, "Router", "route_from_planner", {"has_plan": bool(execution_plan), "route": route})
    return route


def route_from_sub_agent_executor(state: AgentState) -> Literal["execute_sub_agent_plan", "review_plan", "end"]:
    """Route from sub-agent executor."""
    flow_id = state.get("flow_id", "unknown")
    next_action = state.get("next_action", "end")
    
    route = "end"
    if next_action == "execute_sub_agent_plan":
        route = "execute_sub_agent_plan"
    elif next_action == "review_plan":
        route = "review_plan"
    
    workflow_logger.log_logic_step(flow_id, "Router", "route_from_sub_agent_executor", {"next_action": next_action, "route": route})
    return route


def route_from_plan_review(state: AgentState) -> Literal["refine_plan", "synthesize_results", "respond"]:
    """Route from plan review."""
    flow_id = state.get("flow_id", "unknown")
    next_action = state.get("next_action", "respond")
    
    route = "respond"
    if next_action == "refine_plan":
        route = "refine_plan"
    elif next_action == "synthesize_results":
        route = "synthesize_results"
    
    workflow_logger.log_logic_step(flow_id, "Router", "route_from_plan_review", {"next_action": next_action, "route": route})
    return route


def route_from_refinement(state: AgentState) -> Literal["execute_sub_agent_plan", "synthesize_results"]:
    """Route from plan refinement."""
    flow_id = state.get("flow_id", "unknown")
    next_action = state.get("next_action", "synthesize_results")
    
    route = "synthesize_results"
    if next_action == "execute_sub_agent_plan":
        route = "execute_sub_agent_plan"
    
    workflow_logger.log_logic_step(flow_id, "Router", "route_from_refinement", {"next_action": next_action, "route": route})
    return route


def should_continue(state: AgentState) -> Literal["use_tools", "respond", "plan", "end"]:
    """Determine the next node based on state (legacy)."""
    flow_id = state.get("flow_id", "unknown")
    next_action = state.get("next_action", "end")
    iteration_count = state.get("iteration_count", 0)
    
    # Prevent infinite loops
    if iteration_count > 10:
        workflow_logger.log_logic_step(flow_id, "Router", "should_continue", {"reason": "max_iterations", "route": "end"})
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
    
    route = action_map.get(next_action, "end")
    workflow_logger.log_logic_step(flow_id, "Router", "should_continue", {"next_action": next_action, "route": route})
    return route
