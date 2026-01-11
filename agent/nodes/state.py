"""State definition for the agent graph."""

from typing import Any, Dict, Optional, Sequence, Annotated
from langchain_core.messages import BaseMessage
import operator


class AgentState(dict):
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
