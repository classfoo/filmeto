"""Makeup Artist Agent - Character makeup, styling, and costume design."""

from typing import Any
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.makeupartist import (
    CharacterMakeupSkill,
    CostumeDesignSkill,
    AppearanceStylingSkill,
    HairStylingSkill,
    SpecialEffectsMakeupSkill,
    PeriodLookDesignSkill,
    ContinuityMaintenanceSkill,
)


class MakeupArtistAgent(FilmProductionAgent):
    """
    Makeup Artist Agent - Creates character makeup, costumes, and styling.
    
    As the makeup artist, this agent:
    - Designs and applies character makeup
    - Designs character costumes
    - Creates overall appearance styling
    - Maintains continuity of appearance
    - Works with director on character looks
    - Collaborates with actors on comfort and practicality
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Makeup Artist Agent."""
        skills = [
            CharacterMakeupSkill(),
            CostumeDesignSkill(),
            AppearanceStylingSkill(),
            HairStylingSkill(),
            SpecialEffectsMakeupSkill(),
            PeriodLookDesignSkill(),
            ContinuityMaintenanceSkill(),
        ]
        super().__init__(
            name="MakeupArtist",
            role="Makeup Artist",
            description="Creates character makeup, designs costumes, styles appearances, and maintains visual continuity",
            skills=skills,
            llm=llm,
            specialty="pre_production",
            collaborates_with=["Director", "Actor", "Supervisor"]
        )
