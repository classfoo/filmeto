"""Coordinator Node for simple tasks."""

from typing import Any, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from agent.graph.state import AgentState


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
