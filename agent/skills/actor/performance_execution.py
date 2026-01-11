"""Performance Execution Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class PerformanceExecutionSkill(BaseSkill):
    """Execute a performance for a scene."""
    
    def __init__(self):
        super().__init__(
            name="performance_execution",
            description="Execute a complete performance based on script, direction, and character interpretation",
            required_tools=["list_characters", "create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute performance."""
        scene = context.parameters.get("scene", {})
        character_id = context.parameters.get("character_id")
        
        # Get direction from Director
        direction = context.get_previous_result("Director", "scene_direction")
        
        performance = {
            "scene": scene,
            "character_id": character_id,
            "direction_followed": direction,
            "takes": [
                {
                    "take_number": 1,
                    "notes": "First take - establishing",
                    "quality": "good"
                }
            ],
            "emotional_arc": {
                "start": "neutral",
                "peak": "intense",
                "end": "resolved"
            },
            "performance_complete": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=performance,
            message="Performance executed successfully",
            metadata={"takes": 1}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate performance quality."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
