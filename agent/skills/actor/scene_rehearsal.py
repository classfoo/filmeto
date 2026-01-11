"""Scene Rehearsal Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class SceneRehearsalSkill(BaseSkill):
    """Rehearse scenes before filming."""
    
    def __init__(self):
        super().__init__(
            name="scene_rehearsal",
            description="Rehearse scenes to perfect performance before final takes",
            required_tools=["list_characters"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute scene rehearsal."""
        scene = context.parameters.get("scene", {})
        characters = context.execute_tool("list_characters")
        
        rehearsal = {
            "scene": scene,
            "characters": characters,
            "rehearsal_notes": [
                "Blocking reviewed",
                "Lines practiced",
                "Timing adjusted"
            ],
            "adjustments_made": [],
            "ready_for_take": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=rehearsal,
            message="Scene rehearsal completed",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate scene rehearsal."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
