"""Executor Node for tool execution."""

from typing import Any, List, Optional
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
import logging

from agent.graph.state import AgentState
from agent.workflow_logger import workflow_logger
from agent.streaming import StreamEventEmitter, AgentRole

logger = logging.getLogger(__name__)


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
        self._stream_emitter: Optional[StreamEventEmitter] = None
    
    def set_stream_emitter(self, emitter: Optional[StreamEventEmitter]):
        """Set the stream event emitter."""
        self._stream_emitter = emitter
    
    def __call__(self, state: AgentState) -> AgentState:
        """Execute tools based on the current state."""
        flow_id = state.get("flow_id", "unknown")
        workflow_logger.log_node_entry(flow_id, "ExecutorNode", state)
        
        logger.info("=" * 80)
        logger.info(f"[ExecutorNode] ENTRY")
        logger.info(f"[ExecutorNode] Message count: {len(state.get('messages', []))}")
        
        # Emit executor start event
        if self._stream_emitter:
            self._stream_emitter.emit_agent_start("Executor", AgentRole.EXECUTOR)
        
        messages = state["messages"]
        
        # Extract tool calls from messages
        tool_calls = []
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls.extend(msg.tool_calls)
        
        logger.info(f"[ExecutorNode] Executing {len(tool_calls)} tool call(s)")
        workflow_logger.log_logic_step(flow_id, "ExecutorNode", "executing_tools", [tc.get('name') for tc in tool_calls])
        
        # Emit tool execution start
        if self._stream_emitter and tool_calls:
            tool_names = [tc.get('name', 'unknown') for tc in tool_calls]
            execution_info = f"正在执行 {len(tool_calls)} 个工具: {', '.join(tool_names)}"
            self._stream_emitter.emit_agent_content("Executor", execution_info, append=True)
        
        for i, tool_call in enumerate(tool_calls):
            logger.info(f"  Tool call {i+1}: {tool_call.get('name', 'unknown')} with args: {str(tool_call.get('args', {}))[:100]}")
        
        # Execute tools using LangGraph's ToolNode
        logger.info("[ExecutorNode] Invoking ToolNode...")
        result = self.tool_node.invoke({"messages": messages})
        
        # Log tool results
        tool_results = [msg for msg in result["messages"] if hasattr(msg, 'tool_call_id')]
        logger.info(f"[ExecutorNode] Tool execution completed: {len(tool_results)} result(s)")
        workflow_logger.log_logic_step(flow_id, "ExecutorNode", "tool_execution_completed", f"Executed {len(tool_results)} tools")
        
        # Emit tool execution completion
        if self._stream_emitter:
            completion_info = f"工具执行完成: {len(tool_results)} 个工具已执行"
            self._stream_emitter.emit_agent_content("Executor", completion_info, append=True)
        
        for i, tool_result in enumerate(tool_results[:3]):  # Log first 3 results
            result_content = str(tool_result.content)[:100] if hasattr(tool_result, 'content') else str(tool_result)[:100]
            logger.debug(f"  Result {i+1}: {result_content}...")
        
        logger.info(f"[ExecutorNode] Routing to: coordinator")
        logger.info("[ExecutorNode] EXIT")
        logger.info("=" * 80)
        
        # Emit executor complete event
        if self._stream_emitter:
            self._stream_emitter.emit_agent_complete("Executor", "")
        
        output_state = {
            "messages": result["messages"],
            "next_action": "coordinator",  # Return to coordinator after execution
            "context": state.get("context", {}),
            "iteration_count": state.get("iteration_count", 0),
            "execution_plan": state.get("execution_plan"),
            "current_task_index": state.get("current_task_index", 0),
            "sub_agent_results": state.get("sub_agent_results", {}),
            "requires_multi_agent": state.get("requires_multi_agent", False),
            "plan_refinement_count": state.get("plan_refinement_count", 0),
            "flow_id": flow_id
        }
        workflow_logger.log_node_exit(flow_id, "ExecutorNode", output_state, next_action="coordinator")
        return output_state

