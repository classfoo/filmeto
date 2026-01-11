"""Plan Refinement Node."""

from typing import Any
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import json
import re

from agent.graph.state import AgentState


class PlanRefinementNode:
    """
    Plan refinement node that adjusts execution plans based on results.
    
    This node:
    - Reviews execution results
    - Identifies failed or low-quality tasks
    - Creates refined plan for rework
    """
    
    def __init__(self, llm: ChatOpenAI, sub_agent_registry: Any):
        """Initialize plan refinement node."""
        self.llm = llm
        self.sub_agent_registry = sub_agent_registry
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a plan refinement system for Filmeto film production.

Review the execution results and determine if refinement is needed.

For each failed or low-quality task, decide:
1. Should it be retried with different parameters?
2. Should a different agent handle it?
3. Should additional tasks be added?

You MUST respond with valid JSON:
{{
    "needs_refinement": true/false,
    "refinement_type": "retry" | "reassign" | "add_tasks" | "complete",
    "refined_tasks": [
        {{
            "task_id": 100,
            "agent_name": "AgentName",
            "skill_name": "skill_name",
            "parameters": {{}},
            "dependencies": [],
            "reason": "Why this task is added/modified"
        }}
    ],
    "reasoning": "Explanation of refinement decision"
}}"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
    
    def __call__(self, state: AgentState) -> AgentState:
        """Refine execution plan based on results."""
        messages = state["messages"]
        context = state.get("context", {})
        execution_plan = state.get("execution_plan", {})
        sub_agent_results = state.get("sub_agent_results", {})
        plan_refinement_count = state.get("plan_refinement_count", 0)
        
        # Limit refinement iterations
        if plan_refinement_count >= 3:
            return {
                "messages": [AIMessage(content="[Plan Refinement] Maximum refinement attempts reached. Proceeding to synthesis.")],
                "next_action": "synthesize_results",
                "context": context,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "execution_plan": execution_plan,
                "current_task_index": state.get("current_task_index", 0),
                "sub_agent_results": sub_agent_results,
                "requires_multi_agent": True,
                "plan_refinement_count": plan_refinement_count
            }
        
        # Analyze results
        failed_tasks = []
        low_quality_tasks = []
        for task_id, result in sub_agent_results.items():
            if result.get("status") == "failed":
                failed_tasks.append((task_id, result))
            elif result.get("quality_score", 1.0) < 0.7:
                low_quality_tasks.append((task_id, result))
        
        # If all tasks successful with good quality, proceed to synthesis
        if not failed_tasks and not low_quality_tasks:
            return {
                "messages": [AIMessage(content="[Plan Refinement] All tasks completed successfully with good quality.")],
                "next_action": "synthesize_results",
                "context": context,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "execution_plan": execution_plan,
                "current_task_index": state.get("current_task_index", 0),
                "sub_agent_results": sub_agent_results,
                "requires_multi_agent": True,
                "plan_refinement_count": plan_refinement_count
            }
        
        # Add results context to messages
        results_msg = f"[Results for Refinement] Failed: {len(failed_tasks)}, Low quality: {len(low_quality_tasks)}"
        augmented_messages = list(messages) + [SystemMessage(content=results_msg)]
        
        # Get refinement plan
        formatted_prompt = self.prompt.format_messages(messages=augmented_messages)
        response = self.llm.invoke(formatted_prompt)
        
        # Parse refinement
        try:
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                refinement = json.loads(json_match.group())
            else:
                refinement = {"needs_refinement": False, "refinement_type": "complete"}
        except json.JSONDecodeError:
            refinement = {"needs_refinement": False, "refinement_type": "complete"}
        
        if refinement.get("needs_refinement", False) and refinement.get("refined_tasks"):
            # Add refined tasks to plan
            current_tasks = execution_plan.get("tasks", [])
            refined_tasks = refinement.get("refined_tasks", [])
            execution_plan["tasks"] = current_tasks + refined_tasks
            
            return {
                "messages": [AIMessage(content=f"[Plan Refinement] Added {len(refined_tasks)} tasks for rework.")],
                "next_action": "execute_sub_agent_plan",
                "context": context,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "execution_plan": execution_plan,
                "current_task_index": len(current_tasks),  # Start from new tasks
                "sub_agent_results": sub_agent_results,
                "requires_multi_agent": True,
                "plan_refinement_count": plan_refinement_count + 1
            }
        
        return {
            "messages": [AIMessage(content="[Plan Refinement] No further refinement needed.")],
            "next_action": "synthesize_results",
            "context": context,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "execution_plan": execution_plan,
            "current_task_index": state.get("current_task_index", 0),
            "sub_agent_results": sub_agent_results,
            "requires_multi_agent": True,
            "plan_refinement_count": plan_refinement_count
        }
