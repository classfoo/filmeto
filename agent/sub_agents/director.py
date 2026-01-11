"""Director Agent - Creative vision and scene direction."""

from typing import Any
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.director import (
    StoryboardSkill,
    SceneCompositionSkill,
    SceneDirectionSkill,
    ShotPlanningSkill,
    VisualStyleSkill,
    CameraWorkSkill,
    ActorDirectionSkill,
    SceneBlockingSkill,
)


class DirectorAgent(FilmProductionAgent):
    """
    Director Agent - Develops creative vision and directs scenes.
    
    As the director, this agent:
    - Creates the overall visual and artistic vision
    - Develops storyboards from scripts
    - Plans shot compositions and camera angles
    - Directs scene execution
    - Works with actors on performance
    - Collaborates with all departments to realize the vision
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Director Agent."""
        skills = [
            StoryboardSkill(),
            SceneCompositionSkill(),
            SceneDirectionSkill(),
            ShotPlanningSkill(),
            VisualStyleSkill(),
            CameraWorkSkill(),
            ActorDirectionSkill(),
            SceneBlockingSkill(),
        ]
        super().__init__(
            name="Director",
            role="Director",
            description="Develops creative vision, creates storyboards, plans shots, and directs scenes",
            skills=skills,
            llm=llm,
            specialty="production",
            collaborates_with=["Screenwriter", "Actor", "Editor", "MakeupArtist"]
        )
