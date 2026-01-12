"""Sub-agent execution nodes for multi-agent workflow with parallel execution and streaming support."""

from typing import Any, Dict, List, Optional, Literal, Callable, Set
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from agent.skills.base import SkillContext, SkillStatus
import json
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from agent.graph.state import AgentState, SubAgentState
from agent.streaming import StreamEventEmitter, AgentStreamSession, StreamEventType, AgentRole
from agent.workflow_logger import workflow_logger

logger = logging.getLogger(__name__)


class DependencyGraph:
    """Dependency graph for task execution ordering.
    
    Manages task dependencies and determines which tasks can be executed in parallel.
    """
    
    def __init__(self):
        """Initialize dependency graph."""
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._dependents: Dict[str, List[str]] = {}
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._running: Set[str] = set()
    
    def add_task(self, task_id: str, task_info: Dict[str, Any], dependencies: List[str] = None):
        """Add a task with its dependencies."""
        self._tasks[task_id] = task_info
        self._dependencies[task_id] = list(dependencies) if dependencies else []
        
        if not task_id in self._dependents:
            self._dependents[task_id] = []
        
        for dep in (dependencies or []):
            if dep not in self._dependents:
                self._dependents[dep] = []
            self._dependents[dep].append(task_id)
    
    def add_tasks_from_plan(self, plan: Dict[str, Any]):
        """Add tasks from an execution plan."""
        tasks = plan.get("tasks", [])
        for task in tasks:
            task_id = str(task.get("task_id", len(self._tasks)))
            dependencies = [str(d) for d in task.get("dependencies", [])]
            self.add_task(task_id, task, dependencies)
    
    def get_ready_tasks(self) -> List[str]:
        """Get tasks that are ready to execute (all dependencies met)."""
        ready = []
        for task_id in self._tasks:
            if task_id in self._completed or task_id in self._failed or task_id in self._running:
                continue
            
            deps = self._dependencies.get(task_id, [])
            # All dependencies must be completed (not just present)
            if all(dep in self._completed for dep in deps):
                ready.append(task_id)
        
        return ready
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task info by ID."""
        return self._tasks.get(task_id)
    
    def mark_running(self, task_id: str):
        """Mark a task as running."""
        self._running.add(task_id)
    
    def mark_complete(self, task_id: str):
        """Mark a task as complete."""
        self._running.discard(task_id)
        self._completed.add(task_id)
    
    def mark_failed(self, task_id: str):
        """Mark a task as failed."""
        self._running.discard(task_id)
        self._failed.add(task_id)
    
    def is_complete(self) -> bool:
        """Check if all tasks are complete or failed."""
        return len(self._completed) + len(self._failed) == len(self._tasks)
    
    def get_completion_status(self) -> Dict[str, Any]:
        """Get completion status."""
        return {
            "total": len(self._tasks),
            "completed": len(self._completed),
            "failed": len(self._failed),
            "running": len(self._running),
            "pending": len(self._tasks) - len(self._completed) - len(self._failed) - len(self._running),
            "is_complete": self.is_complete(),
        }
    
    def get_parallel_groups(self) -> List[List[str]]:
        """Get groups of tasks that can be executed in parallel."""
        groups = []
        remaining = set(self._tasks.keys())
        completed_for_grouping = set()
        
        while remaining:
            group = []
            for task_id in list(remaining):
                deps = self._dependencies.get(task_id, [])
                if all(dep in completed_for_grouping for dep in deps):
                    group.append(task_id)
            
            if not group:
                logger.warning(f"Could not schedule remaining tasks: {remaining}")
                break
            
            groups.append(group)
            for task_id in group:
                remaining.discard(task_id)
                completed_for_grouping.add(task_id)
        
        return groups


class SubAgentExecutorNode:
    """
    Sub-agent executor node that executes tasks using sub-agents with parallel execution support.
    
    This node:
    - Executes tasks from the execution plan using appropriate sub-agents
    - Supports parallel execution of independent tasks based on dependencies
    - Emits streaming events for UI updates
    - Evaluates results and quality
    - Handles task dependencies
    """
    
    def __init__(
        self,
        sub_agent_registry: Any,
        tool_registry: Any,
        workspace: Any = None,
        project: Any = None,
        max_parallel_tasks: int = 3
    ):
        """Initialize sub-agent executor node."""
        self.sub_agent_registry = sub_agent_registry
        self.tool_registry = tool_registry
        # Note: We don't store workspace and project in the instance to avoid serialization issues
        # We'll get workspace and project from the state context/configurable parameters
        self.project_id = getattr(project, 'id', None) if project else None
        self.max_parallel_tasks = max_parallel_tasks
        self._stream_emitter = None
        self._plan_id = None
    
    def set_stream_emitter(self, emitter: Any):
        """Set the stream event emitter."""
        self._stream_emitter = emitter
    
    def set_plan_id(self, plan_id: str):
        """Set the current plan ID."""
        self._plan_id = plan_id
    
    async def _execute_task_async(
        self,
        agent: Any,
        task_dict: Dict[str, Any],
        skill_context: SkillContext,
        flow_id: str = "unknown"
    ) -> Any:
        """Execute task asynchronously."""
        # Add flow_id to task_dict so it can be passed to the agent's subgraph
        task_dict["flow_id"] = flow_id
        result = await agent.execute_task(task_dict, skill_context)
        evaluated_result = await agent.evaluate_result(result, task_dict, skill_context)
        return evaluated_result
    
    def _execute_single_task(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any],
        sub_agent_results: Dict[str, Any],
        flow_id: str = "unknown"
    ) -> Dict[str, Any]:
        """Execute a single task and return the result."""
        task_id = str(task.get("task_id", 0))
        agent_name = task.get("agent_name")
        skill_name = task.get("skill_name")
        parameters = dict(task.get("parameters", {}))
        dependencies = task.get("dependencies", [])
        
        workflow_logger.log_sub_agent_start(flow_id, f"{agent_name}/{skill_name}", f"Task {task_id} executing with params: {str(parameters)[:100]}...")
        
        # Emit task start event
        if self._stream_emitter:
            self._stream_emitter.emit_task_start(
                task_id=task_id,
                agent_name=agent_name,
                skill_name=skill_name,
                plan_id=self._plan_id
            )
        
        # Inject dependency results into parameters
        for dep_id in dependencies:
            dep_id_str = str(dep_id)
            dep_result = sub_agent_results.get(dep_id_str)
            if dep_result and dep_result.get("output"):
                parameters[f"from_task_{dep_id_str}"] = dep_result.get("output")
        
        # Get agent
        agent = self.sub_agent_registry.get_agent(agent_name)
        if not agent:
            error_msg = f"Agent '{agent_name}' not found"
            workflow_logger.log_logic_step(flow_id, "SubAgentExecutor", "agent_not_found", error_msg)
            result = {
                "status": "failed",
                "error": error_msg,
                "agent": agent_name,
                "skill": skill_name,
                "task_id": task_id
            }
            
            # Emit error event
            if self._stream_emitter:
                self._stream_emitter.emit_agent_error(agent_name, error_msg)
            
            return result
        
        # Create skill context
        shared_state = context.get("shared_state", {})
        # Get project_id from configurable params first, then from state context, then from node instance
        project_id = self.configurable_params.get('project_id') or context.get("project_id") or self.project_id
        
        # For testing purposes, we'll pass the project_id and let the skill context handle the retrieval
        # In a real implementation, we would use a singleton or service locator pattern
        workspace = self.tool_registry.workspace if hasattr(self.tool_registry, 'workspace') else None
        project = self.tool_registry.project if hasattr(self.tool_registry, 'project') else None
        
        # If still not found, try to get from state context as fallback
        if not workspace:
            workspace = context.get("workspace")
        if not project:
            project = context.get("project")
        
        skill_context = SkillContext(
            workspace=workspace,
            project=project,
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
                        self._execute_task_async(agent, task_dict, skill_context, flow_id)
                    )
                    evaluated_result = future.result()
            except RuntimeError:
                evaluated_result = asyncio.run(
                    self._execute_task_async(agent, task_dict, skill_context, flow_id)
                )
            
            # Store result
            result = {
                "status": evaluated_result.status.value,
                "output": evaluated_result.output,
                "message": evaluated_result.message,
                "quality_score": evaluated_result.quality_score,
                "requires_help": evaluated_result.requires_help,
                "agent": agent_name,
                "skill": skill_name,
                "task_id": task_id
            }
            
            workflow_logger.log_sub_agent_end(flow_id, f"{agent_name}/{skill_name}", result)
            
            # Update shared state
            if evaluated_result.output:
                shared_state[f"{agent_name}_{skill_name}"] = evaluated_result.output
                context["shared_state"] = shared_state
            
            # Emit task complete event
            if self._stream_emitter:
                self._stream_emitter.emit_task_complete(
                    task_id=task_id,
                    agent_name=agent_name,
                    skill_name=skill_name,
                    status=evaluated_result.status.value,
                    message=evaluated_result.message,
                    quality_score=evaluated_result.quality_score,
                    output=evaluated_result.output,
                    plan_id=self._plan_id
                )
            
            return result
        
        except Exception as e:
            error_msg = f"Error in task {task_id}: {str(e)}"
            logger.error(f"[Executor] {error_msg}")
            workflow_logger.log_logic_step(flow_id, "SubAgentExecutor", "task_execution_error", error_msg)
            
            result = {
                "status": "failed",
                "error": str(e),
                "agent": agent_name,
                "skill": skill_name,
                "task_id": task_id
            }
            
            # Emit error event
            if self._stream_emitter:
                self._stream_emitter.emit_agent_error(agent_name, error_msg)
            
            return result
    
    def _execute_parallel_batch(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any],
        sub_agent_results: Dict[str, Any],
        flow_id: str = "unknown"
    ) -> Dict[str, Dict[str, Any]]:
        """Execute a batch of tasks in parallel."""
        results = {}
        
        if len(tasks) == 1:
            # Single task, execute directly
            task = tasks[0]
            task_id = str(task.get("task_id", 0))
            results[task_id] = self._execute_single_task(task, context, sub_agent_results, flow_id)
        else:
            # Multiple tasks, execute in parallel
            with ThreadPoolExecutor(max_workers=min(len(tasks), self.max_parallel_tasks)) as executor:
                future_to_task = {
                    executor.submit(
                        self._execute_single_task,
                        task,
                        context.copy(),
                        sub_agent_results.copy(),
                        flow_id
                    ): task
                    for task in tasks
                }
                
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    task_id = str(task.get("task_id", 0))
                    try:
                        result = future.result()
                        results[task_id] = result
                    except Exception as e:
                        logger.error(f"Task {task_id} raised exception: {e}")
                        results[task_id] = {
                            "status": "failed",
                            "error": str(e),
                            "agent": task.get("agent_name"),
                            "skill": task.get("skill_name"),
                            "task_id": task_id
                        }
        
        return results
    
    def __call__(self, state: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """Execute sub-agent tasks with parallel execution support."""
        from agent.nodes import AgentState
        
        flow_id = state.get("flow_id", "unknown")
        workflow_logger.log_node_entry(flow_id, "SubAgentExecutor", state)
        
        # Store configurable parameters for later use
        self.configurable_params = config.get("configurable", {}) if config else {}
        
        execution_plan = state.get("execution_plan")
        current_task_index = state.get("current_task_index", 0)
        context = state.get("context", {})
        sub_agent_results = state.get("sub_agent_results", {})
        
        # Get or create dependency graph
        # Store dependency graph state separately to avoid serialization issues
        dep_graph_state = context.get("_dependency_graph_state", {})
        dep_graph = DependencyGraph()
        
        if not execution_plan or "tasks" not in execution_plan:
            output_state = {
                **state,
                "next_action": "respond",
                "messages": state["messages"] + [
                    AIMessage(content="[Executor] No execution plan available, proceeding to response")
                ],
                "flow_id": flow_id
            }
            workflow_logger.log_node_exit(flow_id, "SubAgentExecutor", output_state, next_action="respond")
            return output_state
        
        # Create dependency graph from plan
        dep_graph.add_tasks_from_plan(execution_plan)
        
        # Restore graph state from context
        completed_tasks = dep_graph_state.get("completed", [])
        failed_tasks = dep_graph_state.get("failed", [])
        running_tasks = dep_graph_state.get("running", [])
        
        # Mark already completed/failed/running tasks
        for task_id in completed_tasks:
            dep_graph.mark_complete(task_id)
        for task_id in failed_tasks:
            dep_graph.mark_failed(task_id)
        for task_id in running_tasks:
            dep_graph.mark_running(task_id)
        
        # Also mark completed/failed tasks from sub_agent_results
        for task_id in sub_agent_results:
            if sub_agent_results[task_id].get("status") == "success":
                dep_graph.mark_complete(task_id)
            elif sub_agent_results[task_id].get("status") == "failed":
                dep_graph.mark_failed(task_id)
        
        # Check if all tasks are done
        if dep_graph.is_complete():
            status = dep_graph.get_completion_status()
            logger.info(f"All {status['total']} tasks completed, proceeding to review")
            workflow_logger.log_logic_step(flow_id, "SubAgentExecutor", "tasks_completed", f"All {status['total']} tasks completed")
            output_state = {
                **state,
                "next_action": "review_plan",
                "sub_agent_results": sub_agent_results,
                "context": context,
                "messages": state["messages"] + [
                    AIMessage(content=f"[Executor] All {status['total']} tasks completed ({status['completed']} success, {status['failed']} failed), reviewing results")
                ],
                "flow_id": flow_id
            }
            workflow_logger.log_node_exit(flow_id, "SubAgentExecutor", output_state, next_action="review_plan")
            return output_state
        
        # Get ready tasks
        ready_task_ids = dep_graph.get_ready_tasks()
        
        if not ready_task_ids:
            # No tasks ready, might be waiting for dependencies or stuck
            status = dep_graph.get_completion_status()
            if status['running'] > 0:
                # Still have running tasks, wait
                return {
                    **state,
                    "next_action": "execute_sub_agent_plan",
                    "context": context,
                    "messages": state["messages"]
                }
            else:
                # No running tasks and no ready tasks - likely circular dependency or all failed
                logger.warning("No tasks ready and none running - possible dependency issue")
                return {
                    **state,
                    "next_action": "review_plan",
                    "sub_agent_results": sub_agent_results,
                    "context": context,
                    "messages": state["messages"] + [
                        AIMessage(content="[Executor] No more tasks can be executed, proceeding to review")
                    ]
                }
        
        # Get task details for ready tasks
        tasks_to_execute = []
        for task_id in ready_task_ids:
            task = dep_graph.get_task(task_id)
            if task:
                dep_graph.mark_running(task_id)
                tasks_to_execute.append(task)
        
        if not tasks_to_execute:
            return {
                **state,
                "next_action": "review_plan",
                "sub_agent_results": sub_agent_results,
                "context": context,
                "messages": state["messages"]
            }
        
        logger.info(f"Executing {len(tasks_to_execute)} tasks in parallel: {[t.get('task_id') for t in tasks_to_execute]}")
        workflow_logger.log_logic_step(flow_id, "SubAgentExecutor", "executing_tasks", [f"{t.get('task_id')}: {t.get('agent_name')}/{t.get('skill_name')}" for t in tasks_to_execute])
        
        # Execute tasks (possibly in parallel)
        batch_results = self._execute_parallel_batch(tasks_to_execute, context, sub_agent_results, flow_id)
        
        # Update results and dependency graph
        messages = []
        for task_id, result in batch_results.items():
            sub_agent_results[task_id] = result
            
            if result.get("status") == "success":
                dep_graph.mark_complete(task_id)
            else:
                dep_graph.mark_failed(task_id)
            
            # Create result message
            agent_name = result.get("agent", "Unknown")
            skill_name = result.get("skill", "Unknown")
            status = result.get("status", "unknown")
            msg = result.get("message", result.get("error", ""))
            quality_score = result.get("quality_score")
            
            status_emoji = "✓" if status == "success" else "✗"
            quality_str = f" (Quality: {quality_score:.2f})" if quality_score else ""
            result_message = f"[{agent_name}] {status_emoji} Task {task_id} - {skill_name}: {msg[:100]}{quality_str}"
            
            messages.append(AIMessage(content=result_message))
            logger.info(result_message)
        
        # Update context with dependency graph state (instead of the graph object itself)
        context["_dependency_graph_state"] = {
            "completed": list(dep_graph._completed),
            "failed": list(dep_graph._failed),
            "running": list(dep_graph._running)
        }
        
        # Check if done after this batch
        if dep_graph.is_complete():
            status = dep_graph.get_completion_status()
            messages.append(AIMessage(content=f"[Executor] All {status['total']} tasks completed, reviewing results"))
            next_action = "review_plan"
            workflow_logger.log_logic_step(flow_id, "SubAgentExecutor", "all_tasks_completed", f"All {status['total']} tasks completed")
        else:
            next_action = "execute_sub_agent_plan"
            workflow_logger.log_logic_step(flow_id, "SubAgentExecutor", "batch_completed", "Batch completed, more tasks pending")
        
        output_state = {
            **state,
            "next_action": next_action,
            "current_task_index": current_task_index + len(tasks_to_execute),
            "sub_agent_results": sub_agent_results,
            "context": context,
            "messages": state["messages"] + messages,
            "flow_id": flow_id
        }
        workflow_logger.log_node_exit(flow_id, "SubAgentExecutor", output_state, next_action=next_action)
        return output_state


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
        self._stream_emitter = None
    
    def set_stream_emitter(self, emitter: Any):
        """Set the stream event emitter."""
        self._stream_emitter = emitter
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Review execution plan results."""
        flow_id = state.get("flow_id", "unknown")
        workflow_logger.log_node_entry(flow_id, "PlanReviewNode", state)
        
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
        
        workflow_logger.log_logic_step(flow_id, "PlanReviewNode", "analyzed_results", {
            "total": total_count,
            "success": successful_count,
            "failed": failed_count,
            "avg_quality": avg_quality
        })
        
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
        
        workflow_logger.log_logic_step(flow_id, "PlanReviewNode", "decision_made", f"Status: {status}, Next action: {next_action}")
        
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
        
        # Emit agent content event
        if self._stream_emitter:
            self._stream_emitter.emit_agent_start("Reviewer", AgentRole.REVIEWER)
            self._stream_emitter.emit_agent_content("Reviewer", summary)
            self._stream_emitter.emit_agent_complete("Reviewer", summary)
        
        logger.info(f"Plan review: {status}, next action: {next_action}")
        
        output_state = {
            **state,
            "next_action": next_action,
            "context": context,
            "messages": state["messages"] + [AIMessage(content=summary)],
            "flow_id": flow_id
        }
        workflow_logger.log_node_exit(flow_id, "PlanReviewNode", output_state, next_action=next_action)
        return output_state



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
        self._stream_emitter = None
    
    def set_stream_emitter(self, emitter: Any):
        """Set the stream event emitter."""
        self._stream_emitter = emitter
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize execution results."""
        flow_id = state.get("flow_id", "unknown")
        workflow_logger.log_node_entry(flow_id, "ResultSynthesisNode", state)
        
        execution_plan = state.get("execution_plan", {})
        sub_agent_results = state.get("sub_agent_results", {})
        context = state.get("context", {})
        
        # Get original request
        original_request = context.get("original_request", "Unknown request")
        plan_description = context.get("plan_description", "")
        
        workflow_logger.log_logic_step(flow_id, "ResultSynthesisNode", "synthesis_start", {
            "results_count": len(sub_agent_results),
            "original_request_len": len(original_request)
        })
        
        # Emit synthesis start
        if self._stream_emitter:
            from agent.streaming.protocol import AgentRole
            self._stream_emitter.emit_agent_start("Synthesizer", AgentRole.SYNTHESIZER)
        
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
        
        # Emit content
        if self._stream_emitter:
            self._stream_emitter.emit_agent_content("Synthesizer", synthesis)
            self._stream_emitter.emit_agent_complete("Synthesizer", synthesis)
        
        logger.info(f"Synthesis complete: {successful}/{total} tasks successful")
        workflow_logger.log_logic_step(flow_id, "ResultSynthesisNode", "synthesis_complete", f"{successful}/{total} tasks successful")
        
        output_state = {
            **state,
            "next_action": "respond",
            "messages": state["messages"] + [AIMessage(content=synthesis)],
            "flow_id": flow_id
        }
        workflow_logger.log_node_exit(flow_id, "ResultSynthesisNode", output_state, next_action="respond")
        return output_state


# Import AgentRole for use in nodes
from agent.streaming.protocol import AgentRole
