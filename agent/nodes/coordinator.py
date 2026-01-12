"""Coordinator Node for simple tasks."""

from typing import Any, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import logging

from agent.graph.state import AgentState
from agent.workflow_logger import workflow_logger

logger = logging.getLogger(__name__)


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
        flow_id = state.get("flow_id", "unknown")
        workflow_logger.log_node_entry(flow_id, "CoordinatorNode", state)
        
        logger.info("=" * 80)
        logger.info(f"[CoordinatorNode] ENTRY")
        logger.info(f"[CoordinatorNode] Iteration: {state.get('iteration_count', 0)}")
        logger.info(f"[CoordinatorNode] Message count: {len(state.get('messages', []))}")
        logger.info(f"[CoordinatorNode] Available tools: {len(self.tools)}")
        
        messages = state["messages"]
        context = state.get("context", {})
        
        # Format prompt with tool names
        tool_names = [tool.name for tool in self.tools]
        logger.debug(f"[CoordinatorNode] Tool names: {', '.join(tool_names)}")
        formatted_prompt = self.prompt.format_messages(
            messages=messages,
            tool_names=", ".join(tool_names)
        )
        
        logger.info("[CoordinatorNode] Invoking LLM with tool calling capability...")
        # Get LLM response with tool calling capability
        response = self.llm_with_tools.invoke(formatted_prompt)
        
        # Determine next action based on response
        if response.tool_calls:
            next_action = "use_tools"
            logger.info(f"[CoordinatorNode] LLM requested {len(response.tool_calls)} tool call(s)")
            workflow_logger.log_logic_step(flow_id, "CoordinatorNode", "tool_selection", [tc.get('name') for tc in response.tool_calls])
            for i, tool_call in enumerate(response.tool_calls):
                logger.info(f"  Tool call {i+1}: {tool_call.get('name', 'unknown')}")
        else:
            next_action = "respond"
            logger.info("[CoordinatorNode] LLM response does not require tools")
            workflow_logger.log_logic_step(flow_id, "CoordinatorNode", "response_generation", "No tools needed")
        
        logger.info(f"[CoordinatorNode] Routing to: {next_action}")
        logger.info("[CoordinatorNode] EXIT")
        logger.info("=" * 80)
        
        output_state = {
            "messages": [response],
            "next_action": next_action,
            "context": context,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "execution_plan": state.get("execution_plan"),
            "current_task_index": state.get("current_task_index", 0),
            "sub_agent_results": state.get("sub_agent_results", {}),
            "requires_multi_agent": state.get("requires_multi_agent", False),
            "plan_refinement_count": state.get("plan_refinement_count", 0),
            "flow_id": flow_id
        }
        workflow_logger.log_node_exit(flow_id, "CoordinatorNode", output_state, next_action=next_action)
        return output_state

