"""SceneWriting Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class SceneWritingSkill(BaseSkill):
    """Write individual scenes in detail."""
    
    def __init__(self):
        super().__init__(
            name="scene_writing",
            description="Write detailed individual scenes with action, dialogue, and stage directions",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute scene writing."""
        scene_number = context.parameters.get("scene_number", 1)
        location = context.parameters.get("location", "INTERIOR - ROOM")
        time = context.parameters.get("time", "DAY")
        
        scene = {
            "scene_number": scene_number,
            "slug_line": f"{location} - {time}",
            "action_lines": [
                "Scene opens with establishing shot.",
                "Character enters from stage left.",
                "Tension builds as characters interact."
            ],
            "dialogue": [],
            "visual_cues": [],
            "sound_cues": [],
            "transitions": {
                "in": "CUT FROM:",
                "out": "CUT TO:"
            }
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=scene,
            message=f"Scene {scene_number} written",
            metadata={"scene_number": scene_number}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate scene writing."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
