"""Actor Agent - Character portrayal and performance."""

from typing import Any
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.actor import (
    CharacterPortrayalSkill,
    PerformanceExecutionSkill,
    EmotionalExpressionSkill,
    DialogueDeliverySkill,
    PhysicalActingSkill,
    CharacterStudySkill,
    SceneRehearsalSkill,
)


class ActorAgent(FilmProductionAgent):
    """
    Actor Agent - Portrays characters and performs scenes.
    
    As the actor, this agent:
    - Portrays characters based on character definitions
    - Executes performances as directed
    - Interprets dialogue and emotions
    - Works with director on scene execution
    - Coordinates with makeup artist for appearance
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Actor Agent."""
        skills = [
            CharacterPortrayalSkill(),
            PerformanceExecutionSkill(),
            EmotionalExpressionSkill(),
            DialogueDeliverySkill(),
            PhysicalActingSkill(),
            CharacterStudySkill(),
            SceneRehearsalSkill(),
        ]
        super().__init__(
            name="Actor",
            role="Actor",
            description="Portrays characters, executes performances, and brings characters to life through acting",
            skills=skills,
            llm=llm,
            specialty="production",
            collaborates_with=["Director", "MakeupArtist", "Screenwriter"]
        )



