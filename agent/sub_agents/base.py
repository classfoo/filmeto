"""Base sub-agent implementation."""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus
import logging

logger = logging.getLogger(__name__)


class BaseSubAgent(ABC):
    """
    Base class for sub-agents in the film production team.
    
    Each sub-agent has:
    - A name and role description
    - A set of skills (capabilities)
    - The ability to execute tasks
    - The ability to evaluate work quality
    - The ability to request help from other agents
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
    
    @abstractmethod
    async def execute_task(
        self,
        task: Dict[str, Any],
        context: SkillContext
    ) -> SkillResult:
        """
        Execute a task using appropriate skills.
        
        Args:
            task: Task description with skill_name and parameters
            context: Skill execution context
            
        Returns:
            SkillResult with execution status and output
        """
        pass
    
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
    
    Provides default implementation for execute_task that delegates to skills.
    """
    
    async def execute_task(
        self,
        task: Dict[str, Any],
        context: SkillContext
    ) -> SkillResult:
        """Execute a task using appropriate skill."""
        skill_name = task.get("skill_name")
        if not skill_name or skill_name not in self.skills:
            available = ", ".join(self.list_skills())
            return SkillResult(
                status=SkillStatus.FAILED,
                output=None,
                message=f"Unknown skill: {skill_name}. Available: {available}",
                metadata={"agent": self.name}
            )
        
        skill = self.skills[skill_name]
        parameters = task.get("parameters", {})
        context.parameters = parameters
        
        try:
            logger.info(f"[{self.name}] Executing skill: {skill_name}")
            result = await skill.execute(context)
            
            # Store result in shared state for other agents
            context.set_shared_data(f"{self.name}_{skill_name}", result.output)
            
            return result
            
        except Exception as e:
            logger.error(f"[{self.name}] Error executing skill {skill_name}: {e}")
            return SkillResult(
                status=SkillStatus.FAILED,
                output=None,
                message=f"Error executing skill: {str(e)}",
                metadata={"error": str(e), "agent": self.name, "skill": skill_name}
            )
