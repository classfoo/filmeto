"""
Skill Package for Filmeto Agent

This package contains the skill management system for the Filmeto agent.
It follows the Claude skill specification and provides a way to manage
skills as extensions to the agent's capabilities.
"""

from agent.skill.skill_service import Skill, SkillParameter, SkillService
from agent.skill.skill_executor import SkillContext, SkillExecutor, get_skill_executor

__all__ = [
    'Skill',
    'SkillParameter',
    'SkillService',
    'SkillContext',
    'SkillExecutor',
    'get_skill_executor',
]