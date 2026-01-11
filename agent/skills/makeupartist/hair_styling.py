"""HairStyling Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class HairStylingSkill(BaseSkill):
    """Style character hair."""
    
    def __init__(self):
        super().__init__(
            name="hair_styling",
            description="Style and design character hairstyles to match character and period",
            required_tools=["list_characters", "get_character_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute hair styling."""
        character_id = context.parameters.get("character_id")
        style = context.parameters.get("style", "natural")
        
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            character_info = {}
        
        hair = {
            "character": character_info,
            "style": style,
            "hairstyle": {
                "cut": "medium_length",
                "color": "natural",
                "styling": style,
                "texture": "smooth"
            },
            "products_used": [],
            "maintenance_notes": ["Check between takes", "Maintain volume"],
            "styled": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=hair,
            message=f"Hair styled with {style} look",
            metadata={"style": style}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate hair styling."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
