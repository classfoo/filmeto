"""Response Node for generating final responses."""

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from agent.nodes.state import AgentState


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
