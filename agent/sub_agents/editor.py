"""Editor Agent - Video editing and post-production."""

from typing import Any
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.editor import (
    VideoEditingSkill,
    SceneAssemblySkill,
    PacingControlSkill,
    FinalAssemblySkill,
    ColorGradingSkill,
    TransitionDesignSkill,
    RoughCutSkill,
    FineCutSkill,
)


class EditorAgent(FilmProductionAgent):
    """
    Editor Agent - Edits video and assembles the final film.
    
    As the editor, this agent:
    - Edits raw footage into scenes
    - Assembles scenes into sequences
    - Controls pacing and rhythm
    - Creates transitions and effects
    - Works with sound mixer on audio-video sync
    - Delivers final cut
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Editor Agent."""
        skills = [
            VideoEditingSkill(),
            SceneAssemblySkill(),
            PacingControlSkill(),
            FinalAssemblySkill(),
            ColorGradingSkill(),
            TransitionDesignSkill(),
            RoughCutSkill(),
            FineCutSkill(),
        ]
        super().__init__(
            name="Editor",
            role="Editor",
            description="Edits video, assembles scenes, controls pacing, creates transitions, and delivers final cut",
            skills=skills,
            llm=llm,
            specialty="post_production",
            collaborates_with=["Director", "SoundMixer", "Supervisor"]
        )
