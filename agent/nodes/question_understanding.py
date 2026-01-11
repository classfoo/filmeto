"""Question Understanding Node."""

from typing import Any, Dict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import json
import re

from agent.graph.state import AgentState


class QuestionUnderstandingNode:
    """
    Question understanding node that analyzes user questions.
    
    This node:
    - Analyzes user questions to understand intent
    - Determines if sub-agents are needed for collaboration
    - Routes to planner if sub-agents are needed, or to coordinator for simple tasks
    """
    
    def __init__(self, llm: ChatOpenAI, sub_agent_registry: Any):
        """Initialize question understanding node."""
        self.llm = llm
        self.sub_agent_registry = sub_agent_registry
        
        # Get agent capabilities
        capabilities = sub_agent_registry.get_agent_capabilities()
        capabilities_str = self._format_capabilities(capabilities)
        
        # Create question understanding prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a question understanding system for Filmeto, an AI-powered film/video creation platform.

Your role is to:
1. Understand user questions and requests
2. Determine if the request requires multi-agent collaboration
3. Identify which sub-agents might be needed

The user is the "Executive Producer" (出品人) who commissions the film production team.

Available sub-agents and their capabilities:
{capabilities_str}

Film Production Workflow:
1. Pre-Production: Script writing, storyboarding, costume design, character design
2. Production: Scene shooting, directing, acting, makeup application
3. Post-Production: Video editing, sound mixing, color grading, final assembly

Analysis criteria:
- Simple queries about project state: Use coordinator directly (no multi-agent)
- Single-step tasks: Use coordinator with tools (no multi-agent)
- Creative tasks requiring film production skills: Require sub-agent collaboration
- Multi-step tasks with different specialized skills: Require sub-agent collaboration

For each user request, analyze:
1. Does this require multiple specialized film production skills?
2. Which agents would be most suitable based on their skills?
3. What is the complexity level?

You MUST respond with valid JSON format:
{{{{
    "requires_sub_agents": true/false,
    "complexity": "simple" | "moderate" | "complex",
    "suggested_agents": ["AgentName1", "AgentName2"],
    "task_type": "pre_production" | "production" | "post_production" | "full_production" | "query",
    "reasoning": "Brief explanation of why this needs/doesn't need multi-agent collaboration"
}}}}"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
    
    def _format_capabilities(self, capabilities: Dict[str, list]) -> str:
        """Format agent capabilities for prompt."""
        lines = []
        for agent_name, skills in capabilities.items():
            lines.append(f"\n{agent_name}:")
            for skill in skills:
                lines.append(f"  - {skill['name']}: {skill['description']}")
        return "\n".join(lines)
    
    def __call__(self, state: AgentState) -> AgentState:
        """Process question understanding."""
        messages = state["messages"]
        context = state.get("context", {})
        
        # Get the last user message
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        if not user_message:
            # No user message found, proceed to coordinator
            return {
                "messages": [],
                "next_action": "coordinator",
                "context": context,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "execution_plan": None,
                "current_task_index": 0,
                "sub_agent_results": {},
                "requires_multi_agent": False,
                "plan_refinement_count": 0
            }
        
        # Format prompt
        formatted_prompt = self.prompt.format_messages(messages=messages)
        
        # Get LLM response
        response = self.llm.invoke(formatted_prompt)
        
        # Parse response
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            analysis = {
                "requires_sub_agents": False,
                "complexity": "simple",
                "suggested_agents": [],
                "task_type": "query",
                "reasoning": "Could not parse analysis, defaulting to coordinator"
            }
        
        # Store analysis in context
        context["question_analysis"] = analysis
        context["original_request"] = user_message
        
        # Determine next action
        requires_multi_agent = analysis.get("requires_sub_agents", False)
        if requires_multi_agent:
            next_action = "planner"
        else:
            next_action = "coordinator"
        
        # Create analysis message for transparency
        analysis_msg = f"[Question Analysis] Task type: {analysis.get('task_type', 'unknown')}, " \
                       f"Complexity: {analysis.get('complexity', 'unknown')}, " \
                       f"Multi-agent required: {requires_multi_agent}"
        if requires_multi_agent:
            analysis_msg += f", Suggested agents: {', '.join(analysis.get('suggested_agents', []))}"
        
        return {
            "messages": [AIMessage(content=analysis_msg)],
            "next_action": next_action,
            "context": context,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "execution_plan": None,
            "current_task_index": 0,
            "sub_agent_results": {},
            "requires_multi_agent": requires_multi_agent,
            "plan_refinement_count": 0
        }
