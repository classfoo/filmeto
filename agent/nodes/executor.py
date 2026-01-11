"""Executor Node for tool execution."""

from typing import Any, List
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from agent.nodes.state import AgentState


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
