"""SceneDirection Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class SceneDirectionSkill(BaseSkill):
    """Direct scene execution and filming."""
    
    def __init__(self):
        super().__init__(
            name="scene_direction",
            description="Direct scene execution, coordinate with actors, and oversee filming process",
            required_tools=["create_task", "list_characters"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute scene direction."""
        scene = context.parameters.get("scene", {})
        characters = context.execute_tool("list_characters")
        
        direction = {
            "scene": scene,
            "characters": characters,
            "direction_notes": [
                "Establish setting with wide shot",
                "Focus on character emotions in close-ups",
                "Maintain consistent pacing"
            ],
            "actor_directions": [],
            "camera_directions": [],
            "blocking": {
                "positions": [],
                "movements": []
            },
            "takes_planned": 3
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=direction,
            message="Scene direction prepared",
            metadata={"takes_planned": 3}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate scene direction."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
