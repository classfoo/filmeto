"""Response Node for generating final responses."""

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import logging

from agent.graph.state import AgentState
from agent.workflow_logger import workflow_logger

logger = logging.getLogger(__name__)


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
        flow_id = state.get("flow_id", "unknown")
        workflow_logger.log_node_entry(flow_id, "ResponseNode", state)
        
        logger.info("=" * 80)
        logger.info(f"[ResponseNode] ENTRY")
        logger.info(f"[ResponseNode] Message count: {len(state.get('messages', []))}")
        
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
            workflow_logger.log_logic_step(flow_id, "ResponseNode", "summarize_results", f"Summarizing {len(sub_agent_results)} sub-agent results")
        
        logger.info("[ResponseNode] Generating final response...")
        formatted_prompt = self.prompt.format_messages(messages=messages)
        response = self.llm.invoke(formatted_prompt)
        logger.info("[ResponseNode] Response generated")
        
        logger.info(f"[ResponseNode] Routing to: end")
        logger.info("[ResponseNode] EXIT")
        logger.info("=" * 80)
        
        output_state = {
            "messages": [response],
            "next_action": "end",
            "context": context,
            "iteration_count": state.get("iteration_count", 0),
            "execution_plan": state.get("execution_plan"),
            "current_task_index": state.get("current_task_index", 0),
            "sub_agent_results": sub_agent_results,
            "requires_multi_agent": state.get("requires_multi_agent", False),
            "plan_refinement_count": state.get("plan_refinement_count", 0),
            "flow_id": flow_id
        }
        workflow_logger.log_node_exit(flow_id, "ResponseNode", output_state, next_action="end")
        return output_state

