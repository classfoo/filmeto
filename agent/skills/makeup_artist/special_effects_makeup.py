"""SpecialEffectsMakeup Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class SpecialEffectsMakeupSkill(BaseSkill):
    """Create special effects makeup."""
    
    def __init__(self):
        super().__init__(
            name="special_effects_makeup",
            description="Create special effects makeup including prosthetics, aging, and wounds",
            required_tools=["get_character_info", "create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute special effects makeup."""
        effect_type = context.parameters.get("effect_type", "general")
        character_id = context.parameters.get("character_id")
        
        sfx_makeup = {
            "effect_type": effect_type,
            "character_id": character_id,
            "effects_applied": {
                "prosthetics": [],
                "paint_work": [],
                "textures": []
            },
            "materials_used": [],
            "application_time": "varies",
            "removal_notes": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=sfx_makeup,
            message=f"Special effects makeup prepared for {effect_type}",
            metadata={"effect_type": effect_type}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate special effects makeup."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
