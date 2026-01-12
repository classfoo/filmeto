"""State definition for the agent graph."""

from typing import Any, Dict, Optional, Sequence, Annotated, List
from langchain_core.messages import BaseMessage
import operator


class AgentState(dict):
    """Base state for the agent graph."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_action: str
    context: Dict[str, Any]
    iteration_count: int
    flow_id: Optional[str]  # Unique identifier for the execution flow



class ProductionAgentState(AgentState):
    """
    State for Production Agent (Main Agent).
    
    This is the main agent that orchestrates the entire workflow,
    including question understanding, planning, coordination, and
    sub-agent execution.
    """
    project_id: str  # Project identifier for context isolation
    execution_plan: Optional[Dict[str, Any]]  # Execution plan with sub-agent tasks
    current_task_index: int  # Current task index in execution plan
    sub_agent_results: Dict[str, Any]  # Results from sub-agent executions
    requires_multi_agent: bool  # Whether multi-agent collaboration is needed
    plan_refinement_count: int  # Number of plan refinements


class SubAgentState(dict):
    """
    State for Sub-Agent execution.
    
    Each sub-agent (Director, Screenwriter, etc.) has its own state
    that is managed independently within its subgraph.
    """
    agent_id: str  # Agent identifier (e.g., "Director", "Screenwriter")
    agent_name: str  # Agent display name
    task: Dict[str, Any]  # Task to execute
    task_id: str  # Task identifier
    messages: Annotated[Sequence[BaseMessage], operator.add]  # Agent's internal messages
    context: Dict[str, Any]  # Skill execution context
    result: Optional[Dict[str, Any]]  # Execution result
    status: str  # Execution status: "pending", "in_progress", "completed", "failed"
    metadata: Dict[str, Any]  # Additional metadata
    flow_id: Optional[str]  # Trace back to main flow

