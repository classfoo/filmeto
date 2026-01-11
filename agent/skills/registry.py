"""Skill registry for managing available skills by agent."""

from typing import Dict, List, Optional, Any, Type
from agent.skills.base import BaseSkill, ScriptedSkill, LLMEnhancedSkill, SkillBuilder


class SkillRegistry:
    """Registry for managing available skills by agent."""
    
    def __init__(self):
        """Initialize skill registry."""
        self._skills: Dict[str, Dict[str, BaseSkill]] = {}  # {agent_name: {skill_name: skill}}
        self._all_skills: Dict[str, BaseSkill] = {}  # {skill_name: skill}
        self._categories: Dict[str, List[str]] = {}  # {category: [skill_names]}
    
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
        
        # Register by category
        if skill.category:
            if skill.category not in self._categories:
                self._categories[skill.category] = []
            if skill.name not in self._categories[skill.category]:
                self._categories[skill.category].append(skill.name)
    
    def unregister_skill(self, skill_name: str, agent_name: str) -> bool:
        """
        Unregister a skill.
        
        Args:
            skill_name: Name of skill to unregister
            agent_name: Name of agent that owns the skill
            
        Returns:
            True if skill was found and removed, False otherwise
        """
        if agent_name in self._skills and skill_name in self._skills[agent_name]:
            skill = self._skills[agent_name].pop(skill_name)
            if skill_name in self._all_skills:
                del self._all_skills[skill_name]
            if skill.category and skill.category in self._categories:
                if skill_name in self._categories[skill.category]:
                    self._categories[skill.category].remove(skill_name)
            return True
        return False
    
    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a skill by name."""
        return self._all_skills.get(skill_name)
    
    def get_agent_skills(self, agent_name: str) -> List[BaseSkill]:
        """Get all skills for an agent."""
        return list(self._skills.get(agent_name, {}).values())
    
    def get_skills_by_category(self, category: str) -> List[BaseSkill]:
        """Get all skills in a category."""
        skill_names = self._categories.get(category, [])
        return [self._all_skills[name] for name in skill_names if name in self._all_skills]
    
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
    
    def list_categories(self) -> List[str]:
        """List all skill categories."""
        return list(self._categories.keys())
    
    def get_skill_capabilities(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        Get skill capabilities for an agent as a list of skill descriptions.
        
        Args:
            agent_name: Name of agent
            
        Returns:
            List of dicts with skill info
        """
        skills = self.get_agent_skills(agent_name)
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "required_tools": skill.required_tools,
                "category": skill.category
            }
            for skill in skills
        ]
    
    def find_skill_for_task(self, task_description: str) -> Optional[BaseSkill]:
        """
        Find a skill that matches a task description (simple matching).
        
        Args:
            task_description: Description of the task
            
        Returns:
            Best matching skill or None
        """
        task_lower = task_description.lower()
        
        # Simple keyword matching
        for skill in self._all_skills.values():
            skill_keywords = skill.name.lower().replace("_", " ").split()
            if any(kw in task_lower for kw in skill_keywords):
                return skill
        
        return None
    
    def get_workflow_skills(self, workflow_type: str) -> List[BaseSkill]:
        """
        Get skills for a specific workflow type.
        
        Args:
            workflow_type: Type of workflow ("pre_production", "production", "post_production", "full_production")
            
        Returns:
            List of skills for the workflow
        """
        if workflow_type == "full_production":
            return self.list_all_skills()
        
        return self.get_skills_by_category(workflow_type)


class SkillFactory:
    """Factory for creating common skill types."""
    
    @staticmethod
    def create_tool_skill(
        name: str,
        description: str,
        tool_name: str,
        tool_params_func: callable,
        agent_name: str,
        category: str = None
    ) -> ScriptedSkill:
        """
        Create a skill that wraps a single tool call.
        
        Args:
            name: Skill name
            description: Skill description
            tool_name: Name of tool to call
            tool_params_func: Function that takes context and returns tool parameters
            agent_name: Owning agent name
            category: Skill category
            
        Returns:
            ScriptedSkill instance
        """
        from agent.skills.base import SkillStep
        
        def execute_tool(context, step_data):
            params = tool_params_func(context)
            return context.execute_tool(tool_name, **params)
        
        step = SkillStep(
            name=f"execute_{tool_name}",
            description=f"Execute {tool_name} tool",
            action=execute_tool
        )
        
        return ScriptedSkill(
            name=name,
            description=description,
            steps=[step],
            required_tools=[tool_name],
            agent_name=agent_name,
            category=category
        )
    
    @staticmethod
    def create_multi_tool_skill(
        name: str,
        description: str,
        tool_sequence: List[Dict[str, Any]],
        agent_name: str,
        category: str = None
    ) -> ScriptedSkill:
        """
        Create a skill that executes multiple tools in sequence.
        
        Args:
            name: Skill name
            description: Skill description
            tool_sequence: List of {"tool_name": str, "params_func": callable, "step_name": str}
            agent_name: Owning agent name
            category: Skill category
            
        Returns:
            ScriptedSkill instance
        """
        from agent.skills.base import SkillStep
        
        steps = []
        required_tools = []
        
        for tool_def in tool_sequence:
            tool_name = tool_def["tool_name"]
            params_func = tool_def.get("params_func", lambda ctx: {})
            step_name = tool_def.get("step_name", f"execute_{tool_name}")
            
            def make_action(tn, pf):
                def action(context, step_data):
                    params = pf(context)
                    return context.execute_tool(tn, **params)
                return action
            
            steps.append(SkillStep(
                name=step_name,
                description=f"Execute {tool_name}",
                action=make_action(tool_name, params_func)
            ))
            required_tools.append(tool_name)
        
        return ScriptedSkill(
            name=name,
            description=description,
            steps=steps,
            required_tools=required_tools,
            agent_name=agent_name,
            category=category
        )
    
    @staticmethod
    def create_llm_skill(
        name: str,
        description: str,
        system_prompt: str,
        agent_name: str,
        category: str = None,
        output_format: str = "text"
    ) -> LLMEnhancedSkill:
        """
        Create an LLM-enhanced skill.
        
        Args:
            name: Skill name
            description: Skill description
            system_prompt: System prompt for LLM
            agent_name: Owning agent name
            category: Skill category
            output_format: Expected output format
            
        Returns:
            LLMEnhancedSkill instance
        """
        return LLMEnhancedSkill(
            name=name,
            description=description,
            system_prompt=system_prompt,
            agent_name=agent_name,
            category=category,
            output_format=output_format
        )
