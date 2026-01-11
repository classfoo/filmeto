"""Skill registry for managing available skills."""

from typing import Dict, List, Optional
from agent.skills.base import BaseSkill


class SkillRegistry:
    """Registry for managing available skills by agent."""
    
    def __init__(self):
        """Initialize skill registry."""
        self._skills: Dict[str, Dict[str, BaseSkill]] = {}  # {agent_name: {skill_name: skill}}
        self._all_skills: Dict[str, BaseSkill] = {}  # {skill_name: skill}
    
    def register_skill(self, skill: BaseSkill, agent_name: str):
        """
        Register a skill for an agent.
        
        Args:
            skill: Skill to register
            agent_name: Name of agent that owns this skill
        """
        if agent_name not in self._skills:
            self._skills[agent_name] = {}
        
        self._skills[agent_name][skill.name] = skill
        self._all_skills[skill.name] = skill
        skill.agent_name = agent_name
    
    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a skill by name."""
        return self._all_skills.get(skill_name)
    
    def get_agent_skills(self, agent_name: str) -> List[BaseSkill]:
        """Get all skills for an agent."""
        return list(self._skills.get(agent_name, {}).values())
    
    def get_skills_by_tool(self, tool_name: str) -> List[BaseSkill]:
        """Get all skills that use a specific tool."""
        matching_skills = []
        for skill in self._all_skills.values():
            if tool_name in skill.required_tools:
                matching_skills.append(skill)
        return matching_skills
    
    def list_all_skills(self) -> List[BaseSkill]:
        """List all registered skills."""
        return list(self._all_skills.values())
    
    def list_agent_names(self) -> List[str]:
        """List all agent names that have skills."""
        return list(self._skills.keys())
    
    def get_skill_capabilities(self, agent_name: str) -> List[Dict[str, str]]:
        """
        Get skill capabilities for an agent as a list of skill descriptions.
        
        Args:
            agent_name: Name of agent
            
        Returns:
            List of dicts with 'name' and 'description' keys
        """
        skills = self.get_agent_skills(agent_name)
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "required_tools": skill.required_tools
            }
            for skill in skills
        ]
