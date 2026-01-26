"""
Skill Package for Filmeto Agent

This package contains the skill management system for the Filmeto agent.
It follows the Claude skill specification and provides a way to manage
skills as extensions to the agent's capabilities.
"""

# Import data models
from agent.skill.skill_models import Skill, SkillParameter, SkillContext

# Import service
from agent.skill.skill_service import SkillService

__all__ = [
    'Skill',
    'SkillParameter',
    'SkillContext',
    'SkillService',
]
