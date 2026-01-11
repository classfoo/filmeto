"""Screenwriter Agent Skills."""

from agent.skills.screenwriter.script_outline import ScriptOutlineSkill
from agent.skills.screenwriter.script_detail import ScriptDetailSkill
from agent.skills.screenwriter.dialogue_writing import DialogueWritingSkill
from agent.skills.screenwriter.story_development import StoryDevelopmentSkill
from agent.skills.screenwriter.character_arc import CharacterArcSkill
from agent.skills.screenwriter.scene_writing import SceneWritingSkill
from agent.skills.screenwriter.script_revision import ScriptRevisionSkill
from agent.skills.screenwriter.treatment_writing import TreatmentWritingSkill

__all__ = [
    "ScriptOutlineSkill",
    "ScriptDetailSkill",
    "DialogueWritingSkill",
    "StoryDevelopmentSkill",
    "CharacterArcSkill",
    "SceneWritingSkill",
    "ScriptRevisionSkill",
    "TreatmentWritingSkill",
]
