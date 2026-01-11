"""ActorDirection Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ActorDirectionSkill(BaseSkill):
    """Direct actor performances."""
    
    def __init__(self):
        super().__init__(
            name="actor_direction",
            description="Provide direction and guidance to actors for their performances",
            required_tools=["list_characters", "get_character_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute actor direction."""
        characters = context.execute_tool("list_characters")
        scene = context.parameters.get("scene", {})
        
        direction = {
            "scene": scene,
            "characters": characters,
            "performance_notes": {
                "emotion": context.parameters.get("emotion", "neutral"),
                "intensity": context.parameters.get("intensity", "medium"),
                "pacing": context.parameters.get("pacing", "natural")
            },
            "blocking_instructions": [],
            "dialogue_notes": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=direction,
            message="Actor direction prepared",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate actor direction."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
