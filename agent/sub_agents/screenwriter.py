"""Screenwriter Agent - Script writing and story development."""

from typing import Any
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.screenwriter import (
    ScriptOutlineSkill,
    ScriptDetailSkill,
    DialogueWritingSkill,
    StoryDevelopmentSkill,
    CharacterArcSkill,
    SceneWritingSkill,
    ScriptRevisionSkill,
    TreatmentWritingSkill,
)


class ScreenwriterAgent(FilmProductionAgent):
    """
    Screenwriter Agent - Writes scripts and develops stories.
    
    As the screenwriter, this agent:
    - Creates script outlines and story structures
    - Writes detailed scripts with scenes and dialogue
    - Develops character arcs and relationships
    - Creates dialogue for all characters
    - Works with director on script revisions
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Screenwriter Agent."""
        skills = [
            ScriptOutlineSkill(),
            ScriptDetailSkill(),
            DialogueWritingSkill(),
            StoryDevelopmentSkill(),
            CharacterArcSkill(),
            SceneWritingSkill(),
            ScriptRevisionSkill(),
            TreatmentWritingSkill(),
        ]
        super().__init__(
            name="Screenwriter",
            role="Screenwriter",
            description="Creates scripts, develops storylines, writes dialogue, and structures narratives",
            skills=skills,
            llm=llm,
            specialty="pre_production",
            collaborates_with=["Director", "Production", "Actor"]
        )
