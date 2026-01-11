"""Base sub-agent implementation."""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class BaseSubAgent(ABC):
    """
    Base class for sub-agents.
    
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
        llm: Any = None
    ):
        """
        Initialize sub-agent.
        
        Args:
            name: Agent name (e.g., "Director")
            role: Agent role (e.g., "Director")
            description: Agent description
            skills: List of skills this agent can perform
            llm: Optional LLM for agent reasoning
        """
        self.name = name
        self.role = role
        self.description = description
        self.skills = {skill.name: skill for skill in skills}
        self.llm = llm
    
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
                "required_tools": skill.required_tools
            }
            for skill in self.skills.values()
        ]
    
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
        return result
    
    def can_help_with(self, skill_name: str) -> bool:
        """Check if this agent can help with a specific skill."""
        return skill_name in self.skills
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary."""
        return {
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "skills": [skill.to_dict() for skill in self.skills.values()]
        }
