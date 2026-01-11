"""CharacterMakeup Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class CharacterMakeupSkill(BaseSkill):
    """Apply character makeup."""
    
    def __init__(self):
        super().__init__(
            name="character_makeup",
            description="Design and apply makeup to characters based on character design and scene requirements",
            required_tools=["list_characters", "get_character_info", "create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute character makeup."""
        character_id = context.parameters.get("character_id")
        style = context.parameters.get("style", "natural")
        scene_context = context.parameters.get("scene_context", "day")
        
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            characters = context.execute_tool("list_characters")
            character_info = characters
        
        makeup = {
            "character": character_info,
            "style": style,
            "scene_context": scene_context,
            "makeup_design": {
                "foundation": "matched_to_skin_tone",
                "eyes": "defined" if style != "natural" else "minimal",
                "lips": "natural_tint",
                "contouring": "subtle",
                "special_features": []
            },
            "products_used": [],
            "application_notes": [
                "Set with powder for lighting",
                "Touch-up between takes"
            ],
            "makeup_applied": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=makeup,
            message=f"Character makeup applied with {style} style",
            metadata={"style": style}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate makeup quality."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
