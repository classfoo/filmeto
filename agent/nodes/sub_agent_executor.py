"""Sub-agent execution nodes."""

from typing import Any, Dict, List, Optional, Literal
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from agent.nodes import AgentState
from agent.skills.base import SkillContext, SkillStatus
import json
import asyncio


class SubAgentExecutorNode:
    """
    Sub-agent executor node that executes tasks using sub-agents.
    
    This node:
    - Executes tasks from the execution plan using appropriate sub-agents
    - Evaluates results and quality
    - Handles task dependencies
    - Can request help from other agents if needed
    """
    
    def __init__(
        self,
        sub_agent_registry: Any,
        tool_registry: Any,
        workspace: Any,
        project: Any
    ):
        """Initialize sub-agent executor node."""
        self.sub_agent_registry = sub_agent_registry
        self.tool_registry = tool_registry
        self.workspace = workspace
        self.project = project
    
    async def _execute_task_async(
        self,
        agent: Any,
        task_dict: Dict[str, Any],
        skill_context: SkillContext
    ) -> Any:
        """Execute task asynchronously."""
        result = await agent.execute_task(task_dict, skill_context)
        evaluated_result = await agent.evaluate_result(result, task_dict, skill_context)
        return evaluated_result
    
    def __call__(self, state: AgentState) -> AgentState:
        """Execute sub-agent tasks."""
        execution_plan = state.get("execution_plan")
        current_task_index = state.get("current_task_index", 0)
        context = state.get("context", {})
        sub_agent_results = state.get("sub_agent_results", {})
        
        if not execution_plan or "tasks" not in execution_plan:
            return {
                **state,
                "next_action": "coordinator",
                "messages": state["messages"] + [
                    AIMessage(content="No execution plan available")
                ]
            }
        
        tasks = execution_plan["tasks"]
        
        if current_task_index >= len(tasks):
            # All tasks completed
            return {
                **state,
                "next_action": "review_plan",
                "sub_agent_results": sub_agent_results
            }
        
        # Get current task
        current_task = tasks[current_task_index]
        task_id = current_task.get("task_id", current_task_index)
        agent_name = current_task.get("agent_name")
        skill_name = current_task.get("skill_name")
        parameters = current_task.get("parameters", {})
        dependencies = current_task.get("dependencies", [])
        
        # Check dependencies
        dependencies_met = all(dep in sub_agent_results for dep in dependencies)
        if not dependencies_met:
            # Dependencies not met, skip for now (would need dependency resolution logic)
            return {
                **state,
                "next_action": "execute_sub_agent_plan",
                "current_task_index": current_task_index + 1
            }
        
        # Get agent
        agent = self.sub_agent_registry.get_agent(agent_name)
        if not agent:
            error_msg = f"Agent '{agent_name}' not found"
            sub_agent_results[task_id] = {
                "status": "failed",
                "error": error_msg,
                "agent": agent_name,
                "skill": skill_name
            }
            return {
                **state,
                "next_action": "execute_sub_agent_plan",
                "current_task_index": current_task_index + 1,
                "sub_agent_results": sub_agent_results,
                "messages": state["messages"] + [AIMessage(content=error_msg)]
            }
        
        # Create skill context
        shared_state = context.get("shared_state", {})
        skill_context = SkillContext(
            workspace=self.workspace,
            project=self.project,
            agent_name=agent_name,
            parameters=parameters,
            shared_state=shared_state,
            tool_registry=self.tool_registry
        )
        
        # Execute task - handle async execution
        try:
            task_dict = {
                "skill_name": skill_name,
                "parameters": parameters
            }
            
            # Try to run async code in existing event loop or create new one
            try:
                loop = asyncio.get_running_loop()
                # If loop is running, we need to schedule and wait
                # This is a limitation - we'll need to handle this differently
                # For now, create a new thread with event loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._execute_task_async(agent, task_dict, skill_context)
                    )
                    evaluated_result = future.result()
            except RuntimeError:
                # No running loop, create new one
                evaluated_result = asyncio.run(
                    self._execute_task_async(agent, task_dict, skill_context)
                )
            
            # Store result
            result_dict = {
                "status": evaluated_result.status.value,
                "output": evaluated_result.output,
                "message": evaluated_result.message,
                "quality_score": evaluated_result.quality_score,
                "requires_help": evaluated_result.requires_help,
                "agent": agent_name,
                "skill": skill_name
            }
            sub_agent_results[task_id] = result_dict
            
            # Update shared state if needed
            if evaluated_result.output:
                shared_state[f"{agent_name}_{skill_name}"] = evaluated_result.output
                context["shared_state"] = shared_state
            
            # Create message for result
            result_message = f"Task {task_id} completed by {agent_name} using {skill_name}: {evaluated_result.message}"
            if evaluated_result.quality_score:
                result_message += f" (Quality: {evaluated_result.quality_score:.2f})"
            
            return {
                **state,
                "next_action": "execute_sub_agent_plan",
                "current_task_index": current_task_index + 1,
                "sub_agent_results": sub_agent_results,
                "context": context,
                "messages": state["messages"] + [AIMessage(content=result_message)]
            }
        
        except Exception as e:
            error_msg = f"Error executing task {task_id}: {str(e)}"
            sub_agent_results[task_id] = {
                "status": "failed",
                "error": str(e),
                "agent": agent_name,
                "skill": skill_name
            }
            return {
                **state,
                "next_action": "execute_sub_agent_plan",
                "current_task_index": current_task_index + 1,
                "sub_agent_results": sub_agent_results,
                "messages": state["messages"] + [AIMessage(content=error_msg)]
            }


class PlanReviewNode:
    """
    Plan review node that reviews execution results and decides next steps.
    
    This node:
    - Reviews all sub-agent execution results
    - Determines if plan needs refinement
    - Decides if rework is needed
    - Routes to appropriate next step
    """
    
    def __init__(self, llm: Any):
        """Initialize plan review node."""
        self.llm = llm
    
    def __call__(self, state: AgentState) -> AgentState:
        """Review execution plan results."""
        execution_plan = state.get("execution_plan")
        sub_agent_results = state.get("sub_agent_results", {})
        context = state.get("context", {})
        
        # Analyze results
        all_successful = all(
            result.get("status") == "success"
            for result in sub_agent_results.values()
        )
        
        quality_scores = [
            result.get("quality_score", 0.0)
            for result in sub_agent_results.values()
            if result.get("quality_score") is not None
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Determine next action
        if all_successful and avg_quality >= 0.7:
            # Plan executed successfully
            next_action = "synthesize_results"
        elif all_successful and avg_quality < 0.7:
            # Plan executed but quality is low - consider refinement
            next_action = "refine_plan"
        else:
            # Some tasks failed - may need rework
            next_action = "refine_plan"
        
        # Create summary message
        summary = f"Plan execution review: {len(sub_agent_results)} tasks completed"
        if quality_scores:
            summary += f", average quality: {avg_quality:.2f}"
        
        return {
            **state,
            "next_action": next_action,
            "context": {**context, "plan_review": {
                "all_successful": all_successful,
                "avg_quality": avg_quality,
                "results_count": len(sub_agent_results)
            }},
            "messages": state["messages"] + [AIMessage(content=summary)]
        }


class ResultSynthesisNode:
    """
    Result synthesis node that synthesizes sub-agent results into final response.
    
    This node:
    - Synthesizes all sub-agent execution results
    - Creates a coherent final response
    - Presents results to the user
    """
    
    def __init__(self, llm: Any):
        """Initialize result synthesis node."""
        self.llm = llm
    
    def __call__(self, state: AgentState) -> AgentState:
        """Synthesize execution results."""
        execution_plan = state.get("execution_plan")
        sub_agent_results = state.get("sub_agent_results", {})
        context = state.get("context", {})
        
        # Create synthesis message
        synthesis = "Multi-agent execution completed successfully.\n\n"
        synthesis += "Results summary:\n"
        for task_id, result in sorted(sub_agent_results.items()):
            agent = result.get("agent", "Unknown")
            skill = result.get("skill", "Unknown")
            status = result.get("status", "unknown")
            message = result.get("message", "")
            synthesis += f"- Task {task_id} ({agent}/{skill}): {status} - {message}\n"
        
        return {
            **state,
            "next_action": "respond",
            "messages": state["messages"] + [AIMessage(content=synthesis)]
        }
