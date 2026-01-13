"""Router functions for agent graph navigation."""
import logging
from typing import Literal
from langchain_core.messages import ToolMessage

from agent.graph.state import AgentState
from agent.workflow_logger import workflow_logger

logger = logging.getLogger(__name__)

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

    # Check if execution_plan key exists in state
    if "execution_plan" not in state:
        # Check if execution plan information exists in context
        context = state.get("context", {})
        plan_description = context.get("plan_description")
        plan_phase = context.get("plan_phase")

        if plan_description or plan_phase:
            # Execution plan information exists in context, construct a minimal plan
            execution_plan = {
                "description": plan_description or "Plan from context",
                "phase": plan_phase or "unknown",
                "tasks": [],  # May not have tasks in this representation
                "success_criteria": "Based on context information"
            }
            logger.info(f"[Router] Found execution plan in context, constructing plan object (flow_id: {flow_id})")
        else:
            # No execution plan anywhere
            workflow_logger.log_logic_step(flow_id, "Router", "route_from_planner", {
                "error": "execution_plan missing from state and context",
                "route": "coordinator"
            })
            logger.warning(f"[Router] No execution plan found in state or context (flow_id: {flow_id})")
            return "coordinator"
    else:
        execution_plan = state.get("execution_plan")

    # Check if execution_plan is falsy (None, empty dict, etc.)
    if not execution_plan:
        workflow_logger.log_logic_step(flow_id, "Router", "route_from_planner", {
            "has_plan": False,
            "reason": "execution_plan is falsy",
            "route": "coordinator"
        })
        logger.warning(f"[Router] execution_plan is falsy in route_from_planner: {execution_plan} (flow_id: {flow_id})")
        return "coordinator"

    # At this point, execution_plan exists and is truthy
    tasks = execution_plan.get("tasks", [])

    # If there are tasks, proceed to execute them
    if tasks and len(tasks) > 0:
        route = "execute_sub_agent_plan"
        workflow_logger.log_logic_step(flow_id, "Router", "route_from_planner", {
            "has_plan": True,
            "task_count": len(tasks),
            "route": route
        })
        return route
    else:
        # The execution plan exists but has no tasks
        # Instead of routing back to coordinator, continue to execute_sub_agent_plan
        # This allows the execution system to handle empty plans appropriately
        workflow_logger.log_logic_step(flow_id, "Router", "route_from_planner", {
            "has_plan": True,
            "task_count": 0,
            "reason": "no_tasks_in_plan",
            "route": "execute_sub_agent_plan"  # Changed to continue execution flow
        })
        logger.info(f"[Router] Execution plan exists but has no tasks, routing to execute_sub_agent_plan (flow_id: {flow_id})")
        return "execute_sub_agent_plan"


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
