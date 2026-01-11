"""Sound Mixer Agent - Audio mixing and sound design."""

from typing import Any
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.soundmixer import (
    AudioMixingSkill,
    SoundDesignSkill,
    AudioQualityControlSkill,
    DialogueMixingSkill,
    MusicIntegrationSkill,
    FoleyDesignSkill,
    FinalMixSkill,
)


class SoundMixerAgent(FilmProductionAgent):
    """
    Sound Mixer Agent - Handles audio mixing and sound design.
    
    As the sound mixer, this agent:
    - Designs sound effects and ambient audio
    - Mixes multiple audio tracks
    - Controls audio quality and levels
    - Creates atmospheric soundscapes
    - Syncs audio with video
    - Delivers final audio mix
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Sound Mixer Agent."""
        skills = [
            AudioMixingSkill(),
            SoundDesignSkill(),
            AudioQualityControlSkill(),
            DialogueMixingSkill(),
            MusicIntegrationSkill(),
            FoleyDesignSkill(),
            FinalMixSkill(),
        ]
        super().__init__(
            name="SoundMixer",
            role="Sound Mixer",
            description="Mixes audio, designs sound effects, controls audio quality, and delivers final audio mix",
            skills=skills,
            llm=llm,
            specialty="post_production",
            collaborates_with=["Editor", "Director", "Actor"]
        )
