"""Base sub-agent implementation with LangGraph Subgraph support."""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus
from agent.graph.state import SubAgentState
import logging

logger = logging.getLogger(__name__)


class BaseSubAgent(ABC):
    """
    Base class for sub-agents in the film production team.
    
    Each sub-agent is now a complete LangGraph Subgraph with:
    - Independent state management (SubAgentState)
    - Own execution workflow
    - A set of skills (capabilities)
    - The ability to execute tasks
    - The ability to evaluate work quality
    - The ability to communicate with other agents via state
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        description: str,
        skills: List[BaseSkill],
        llm: Any = None,
        specialty: Optional[str] = None,  # Agent's specialty area
        collaborates_with: Optional[List[str]] = None  # Agents this agent typically works with
    ):
        """
        Initialize sub-agent.
        
        Args:
            name: Agent name (e.g., "Director")
            role: Agent role (e.g., "Director")
            description: Agent description
            skills: List of skills this agent can perform
            llm: Optional LLM for agent reasoning
            specialty: Agent's specialty area (e.g., "pre_production", "production", "post_production")
            collaborates_with: List of agent names this agent typically collaborates with
        """
        self.name = name
        self.role = role
        self.description = description
        self.skills = {skill.name: skill for skill in skills}
        self.llm = llm
        self.specialty = specialty
        self.collaborates_with = collaborates_with or []
        
        # Set agent name on all skills
        for skill in skills:
            skill.agent_name = name
        
        # Build the subgraph for this agent
        self.graph = self._build_subgraph()
    
    def _build_subgraph(self) -> StateGraph:
        """
        Build the LangGraph subgraph for this agent.
        
        The default workflow:
        1. execute_skill: Execute the requested skill
        2. evaluate_result: Evaluate the execution result
        3. END
        
        Subclasses can override this to customize the workflow.
        """
        workflow = StateGraph(SubAgentState)
        
        # Add nodes
        workflow.add_node("execute_skill", self._execute_skill_node)
        workflow.add_node("evaluate_result", self._evaluate_result_node)
        
        # Set entry point
        workflow.set_entry_point("execute_skill")
        
        # Add edges
        workflow.add_edge("execute_skill", "evaluate_result")
        workflow.add_edge("evaluate_result", END)
        
        return workflow.compile()
    
    def _execute_skill_node(self, state: SubAgentState) -> SubAgentState:
        """
        Node that executes the requested skill.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        task = state["task"]
        skill_name = task.get("skill_name")
        
        # Update status
        state["status"] = "in_progress"
        
        if not skill_name or skill_name not in self.skills:
            available = ", ".join(self.list_skills())
            state["result"] = {
                "status": "failed",
                "output": None,
                "message": f"Unknown skill: {skill_name}. Available: {available}",
                "metadata": {"agent": self.name}
            }
            state["status"] = "failed"
            return state
        
        skill = self.skills[skill_name]
        parameters = task.get("parameters", {})
        
        # Create skill context from state
        # Get project_id from state context
        project_id = state["context"].get("project_id")
        
        # Get other context from instance variable (_current_context)
        if hasattr(self, '_current_context') and self._current_context:
            # For production use, workspace and project should be retrieved using project_id
            # For now, we'll use the context values but in a real implementation, 
            # we would retrieve workspace and project via singleton/service locator
            workspace = self._current_context.workspace
            project = self._current_context.project
            agent_name = self._current_context.agent_name
            tool_registry = self._current_context.tool_registry
            llm = self._current_context.llm
        else:
            # Final fallback: try to get from state context (for backward compatibility)
            workspace = state["context"].get("workspace")
            project = state["context"].get("project")
            agent_name = self.name
            tool_registry = None
            llm = self.llm
        
        context = SkillContext(
            workspace=workspace,
            project=project,
            agent_name=agent_name,
            parameters=parameters,
            shared_state=state["context"].get("shared_state", {}),
            tool_registry=tool_registry,
            llm=llm
        )
        
        try:
            logger.info(f"[{self.name}] Executing skill: {skill_name}")
            # Execute skill synchronously (will be wrapped in async by graph)
            import asyncio
            if asyncio.iscoroutinefunction(skill.execute):
                result = asyncio.create_task(skill.execute(context)).result()
            else:
                result = skill.execute(context)
            
            # Store result
            state["result"] = {
                "status": result.status.value,
                "output": result.output,
                "message": result.message,
                "metadata": result.metadata,
                "quality_score": result.quality_score
            }
            
            # Add result message
            result_msg = AIMessage(
                content=f"[{self.name}] Skill '{skill_name}' completed: {result.message}"
            )
            state["messages"] = [result_msg]
            
            # Store in shared state
            context.set_shared_data(f"{self.name}_{skill_name}", result.output)
            state["context"]["shared_state"] = context.shared_state
            
        except Exception as e:
            logger.error(f"[{self.name}] Error executing skill {skill_name}: {e}")
            state["result"] = {
                "status": "failed",
                "output": None,
                "message": f"Error executing skill: {str(e)}",
                "metadata": {"error": str(e), "agent": self.name, "skill": skill_name}
            }
            state["status"] = "failed"
            
            error_msg = AIMessage(
                content=f"[{self.name}] Error in skill '{skill_name}': {str(e)}"
            )
            state["messages"] = [error_msg]
        
        return state
    
    def _evaluate_result_node(self, state: SubAgentState) -> SubAgentState:
        """
        Node that evaluates the execution result.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        result = state.get("result")
        
        if not result:
            state["status"] = "failed"
            return state
        
        # Update final status based on result
        if result["status"] == "success":
            state["status"] = "completed"
        else:
            state["status"] = "failed"
        
        # Add evaluation message
        eval_msg = AIMessage(
            content=f"[{self.name}] Evaluation: {result['status']} (quality: {result.get('quality_score', 0.0):.2f})"
        )
        state["messages"] = [eval_msg]
        
        return state
    
    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a skill by name."""
        return self.skills.get(skill_name)
    
    def list_skills(self) -> List[str]:
        """List all skill names."""
        return list(self.skills.keys())
    
    def get_skill_descriptions(self) -> List[Dict[str, str]]:
        """Get descriptions of all skills."""
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "required_tools": skill.required_tools,
                "category": skill.category
            }
            for skill in self.skills.values()
        ]
    
    def get_skills_by_category(self, category: str) -> List[BaseSkill]:
        """Get skills in a specific category."""
        return [skill for skill in self.skills.values() if skill.category == category]
    
    async def execute_task(
        self,
        task: Dict[str, Any],
        context: SkillContext
    ) -> SkillResult:
        """
        Execute a task using the agent's subgraph.
        
        This method now invokes the agent's LangGraph subgraph to execute
        the task through the defined workflow.
        
        Args:
            task: Task description with skill_name and parameters
            context: Skill execution context
            
        Returns:
            SkillResult with execution status and output
        """
        # Store context in instance variable to avoid serialization issues
        self._current_context = context
        
        # Create initial state for the subgraph (without non-serializable objects)
        initial_state: SubAgentState = {
            "agent_id": self.name,
            "agent_name": self.role,
            "task": task,
            "task_id": task.get("task_id", "unknown"),
            "messages": [],
            "context": {
                "shared_state": context.shared_state,
                "project_id": getattr(context.project, 'id', None) if context.project else None
            },
            "result": None,
            "status": "pending",
            "metadata": {}
        }
        
        # Execute the subgraph
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            # Extract result from final state
            result_dict = final_state.get("result", {})
            
            # Convert to SkillResult
            status_str = result_dict.get("status", "failed")
            status = SkillStatus.SUCCESS if status_str == "success" else SkillStatus.FAILED
            
            return SkillResult(
                status=status,
                output=result_dict.get("output"),
                message=result_dict.get("message", ""),
                metadata=result_dict.get("metadata", {}),
                quality_score=result_dict.get("quality_score", 0.0)
            )
        except Exception as e:
            logger.error(f"[{self.name}] Error executing subgraph: {e}")
            import traceback
            traceback.print_exc()
            return SkillResult(
                status=SkillStatus.FAILED,
                output=None,
                message=f"Error executing agent subgraph: {str(e)}",
                metadata={"error": str(e), "agent": self.name}
            )
        finally:
            # Clean up
            self._current_context = None
    
    async def evaluate_result(
        self,
        result: SkillResult,
        task: Dict[str, Any],
        context: SkillContext
    ) -> SkillResult:
        """
        Evaluate the quality of work result.
        
        Args:
            result: Previous execution result
            task: Original task
            context: Skill execution context
            
        Returns:
            Updated SkillResult with evaluation
        """
        skill_name = task.get("skill_name")
        if skill_name and skill_name in self.skills:
            skill = self.skills[skill_name]
            return await skill.evaluate(result, context)
        
        # Default evaluation
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.75
        return result
    
    def can_help_with(self, skill_name: str) -> bool:
        """Check if this agent can help with a specific skill."""
        return skill_name in self.skills
    
    def should_collaborate_with(self, agent_name: str) -> bool:
        """Check if this agent should collaborate with another agent."""
        return agent_name in self.collaborates_with
    
    def get_recommended_helper(self, task: Dict[str, Any]) -> Optional[str]:
        """
        Get recommended agent to help with a task.
        
        Args:
            task: Task that needs help
            
        Returns:
            Name of recommended helper agent or None
        """
        if self.collaborates_with:
            return self.collaborates_with[0]  # Simple: return first collaborator
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary."""
        return {
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "specialty": self.specialty,
            "collaborates_with": self.collaborates_with,
            "skills": [skill.to_dict() for skill in self.skills.values()]
        }


class FilmProductionAgent(BaseSubAgent):
    """
    Base class for film production agents with common functionality.
    
    Uses the default LangGraph subgraph workflow:
    1. execute_skill: Execute the requested skill
    2. evaluate_result: Evaluate the result
    
    All film production agents (Director, Screenwriter, etc.) inherit from this.
    """
    pass  # Uses default subgraph implementation from BaseSubAgent
