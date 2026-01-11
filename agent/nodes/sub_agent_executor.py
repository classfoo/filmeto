"""Sub-agent execution nodes for multi-agent workflow."""

from typing import Any, Dict, List, Optional, Literal
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from agent.skills.base import SkillContext, SkillStatus
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


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
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sub-agent tasks."""
        from agent.nodes import AgentState
        
        execution_plan = state.get("execution_plan")
        current_task_index = state.get("current_task_index", 0)
        context = state.get("context", {})
        sub_agent_results = state.get("sub_agent_results", {})
        
        if not execution_plan or "tasks" not in execution_plan:
            return {
                **state,
                "next_action": "respond",
                "messages": state["messages"] + [
                    AIMessage(content="[Executor] No execution plan available, proceeding to response")
                ]
            }
        
        tasks = execution_plan["tasks"]
        
        if current_task_index >= len(tasks):
            # All tasks completed
            logger.info(f"All {len(tasks)} tasks completed, proceeding to review")
            return {
                **state,
                "next_action": "review_plan",
                "sub_agent_results": sub_agent_results,
                "messages": state["messages"] + [
                    AIMessage(content=f"[Executor] All {len(tasks)} tasks completed, reviewing results")
                ]
            }
        
        # Get current task
        current_task = tasks[current_task_index]
        task_id = current_task.get("task_id", current_task_index)
        agent_name = current_task.get("agent_name")
        skill_name = current_task.get("skill_name")
        parameters = current_task.get("parameters", {})
        dependencies = current_task.get("dependencies", [])
        
        logger.info(f"Executing task {task_id}: {agent_name}/{skill_name}")
        
        # Check dependencies
        dependencies_met = all(dep in sub_agent_results for dep in dependencies)
        if not dependencies_met:
            # Check if dependencies failed
            missing = [d for d in dependencies if d not in sub_agent_results]
            logger.warning(f"Task {task_id} has unmet dependencies: {missing}")
            
            # Skip to next task and try again later
            return {
                **state,
                "next_action": "execute_sub_agent_plan",
                "current_task_index": current_task_index + 1,
                "messages": state["messages"] + [
                    AIMessage(content=f"[Executor] Task {task_id} waiting for dependencies: {missing}")
                ]
            }
        
        # Inject dependency results into parameters
        for dep_id in dependencies:
            dep_result = sub_agent_results.get(dep_id)
            if dep_result and dep_result.get("output"):
                parameters[f"from_task_{dep_id}"] = dep_result.get("output")
        
        # Get agent
        agent = self.sub_agent_registry.get_agent(agent_name)
        if not agent:
            error_msg = f"[Executor] Agent '{agent_name}' not found"
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
            tool_registry=self.tool_registry,
            llm=agent.llm
        )
        
        # Execute task
        try:
            task_dict = {
                "skill_name": skill_name,
                "parameters": parameters
            }
            
            # Run async code
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._execute_task_async(agent, task_dict, skill_context)
                    )
                    evaluated_result = future.result()
            except RuntimeError:
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
                "skill": skill_name,
                "task_id": task_id
            }
            sub_agent_results[task_id] = result_dict
            
            # Update shared state
            if evaluated_result.output:
                shared_state[f"{agent_name}_{skill_name}"] = evaluated_result.output
                context["shared_state"] = shared_state
            
            # Create result message
            status_emoji = "✓" if evaluated_result.status == SkillStatus.SUCCESS else "✗"
            quality_str = f" (Quality: {evaluated_result.quality_score:.2f})" if evaluated_result.quality_score else ""
            result_message = f"[{agent_name}] {status_emoji} Task {task_id} - {skill_name}: {evaluated_result.message}{quality_str}"
            
            logger.info(result_message)
            
            return {
                **state,
                "next_action": "execute_sub_agent_plan",
                "current_task_index": current_task_index + 1,
                "sub_agent_results": sub_agent_results,
                "context": context,
                "messages": state["messages"] + [AIMessage(content=result_message)]
            }
        
        except Exception as e:
            error_msg = f"[Executor] Error in task {task_id}: {str(e)}"
            logger.error(error_msg)
            
            sub_agent_results[task_id] = {
                "status": "failed",
                "error": str(e),
                "agent": agent_name,
                "skill": skill_name,
                "task_id": task_id
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
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Review execution plan results."""
        execution_plan = state.get("execution_plan")
        sub_agent_results = state.get("sub_agent_results", {})
        context = state.get("context", {})
        
        # Analyze results
        successful_count = sum(
            1 for result in sub_agent_results.values()
            if result.get("status") == "success"
        )
        failed_count = sum(
            1 for result in sub_agent_results.values()
            if result.get("status") == "failed"
        )
        total_count = len(sub_agent_results)
        
        quality_scores = [
            result.get("quality_score", 0.0)
            for result in sub_agent_results.values()
            if result.get("quality_score") is not None
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Determine next action
        all_successful = failed_count == 0 and total_count > 0
        
        if all_successful and avg_quality >= 0.7:
            next_action = "synthesize_results"
            status = "success"
        elif all_successful and avg_quality < 0.7:
            next_action = "refine_plan"
            status = "low_quality"
        elif failed_count > 0:
            next_action = "refine_plan"
            status = "has_failures"
        else:
            next_action = "synthesize_results"
            status = "unknown"
        
        # Create summary message
        summary = f"[Plan Review] Status: {status}\n"
        summary += f"- Tasks: {successful_count}/{total_count} successful\n"
        if quality_scores:
            summary += f"- Average quality: {avg_quality:.2f}\n"
        if failed_count > 0:
            failed_tasks = [r.get("task_id", "?") for r in sub_agent_results.values() if r.get("status") == "failed"]
            summary += f"- Failed tasks: {failed_tasks}\n"
        summary += f"→ Next: {next_action}"
        
        # Store review results
        context["plan_review"] = {
            "all_successful": all_successful,
            "avg_quality": avg_quality,
            "results_count": total_count,
            "failed_count": failed_count,
            "status": status
        }
        
        logger.info(f"Plan review: {status}, next action: {next_action}")
        
        return {
            **state,
            "next_action": next_action,
            "context": context,
            "messages": state["messages"] + [AIMessage(content=summary)]
        }


class ResultSynthesisNode:
    """
    Result synthesis node that synthesizes sub-agent results into final response.
    
    This node:
    - Synthesizes all sub-agent execution results
    - Creates a coherent final response
    - Presents results to the user (executive producer)
    """
    
    def __init__(self, llm: Any):
        """Initialize result synthesis node."""
        self.llm = llm
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize execution results."""
        execution_plan = state.get("execution_plan", {})
        sub_agent_results = state.get("sub_agent_results", {})
        context = state.get("context", {})
        
        # Get original request
        original_request = context.get("original_request", "Unknown request")
        plan_description = context.get("plan_description", "")
        
        # Build synthesis
        synthesis = "## 🎬 Film Production Team Report\n\n"
        synthesis += f"**Executive Producer Request:** {original_request[:200]}...\n\n"
        
        if plan_description:
            synthesis += f"**Production Plan:** {plan_description[:300]}...\n\n"
        
        synthesis += "### Task Results:\n\n"
        
        # Group results by agent
        agent_results: Dict[str, List] = {}
        for task_id, result in sorted(sub_agent_results.items()):
            agent = result.get("agent", "Unknown")
            if agent not in agent_results:
                agent_results[agent] = []
            agent_results[agent].append((task_id, result))
        
        for agent, results in agent_results.items():
            synthesis += f"#### {agent}\n"
            for task_id, result in results:
                skill = result.get("skill", "Unknown")
                status = result.get("status", "unknown")
                message = result.get("message", "")[:100]
                quality = result.get("quality_score")
                
                status_icon = "✅" if status == "success" else "❌"
                quality_str = f" (Quality: {quality:.0%})" if quality else ""
                synthesis += f"- {status_icon} **{skill}**: {message}{quality_str}\n"
            synthesis += "\n"
        
        # Add overall summary
        successful = sum(1 for r in sub_agent_results.values() if r.get("status") == "success")
        total = len(sub_agent_results)
        synthesis += f"### Summary\n"
        synthesis += f"- **Tasks completed:** {successful}/{total}\n"
        synthesis += f"- **Agents involved:** {len(agent_results)}\n"
        
        logger.info(f"Synthesis complete: {successful}/{total} tasks successful")
        
        return {
            **state,
            "next_action": "respond",
            "messages": state["messages"] + [AIMessage(content=synthesis)]
        }
