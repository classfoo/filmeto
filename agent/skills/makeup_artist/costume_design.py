"""CostumeDesign Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class CostumeDesignSkill(BaseSkill):
    """Design character costumes."""
    
    def __init__(self):
        super().__init__(
            name="costume_design",
            description="Design and select costumes for characters that fit the story and visual style",
            required_tools=["list_characters", "get_character_info", "create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute costume design."""
        character_id = context.parameters.get("character_id")
        period = context.parameters.get("period", "contemporary")
        style = context.parameters.get("style", "casual")
        
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            characters = context.execute_tool("list_characters")
            character_info = characters
        
        # Get visual style from Director if available
        visual_style = context.get_previous_result("Director", "visual_style")
        
        costume = {
            "character": character_info,
            "period": period,
            "style": style,
            "visual_style_reference": visual_style,
            "costume_elements": {
                "top": {"type": "shirt", "color": "neutral", "fabric": "cotton"},
                "bottom": {"type": "pants", "color": "dark", "fabric": "denim"},
                "footwear": {"type": "shoes", "style": "casual"},
                "accessories": []
            },
            "color_palette": ["#333333", "#666666", "#CCCCCC"],
            "design_notes": [
                "Colors support character personality",
                "Practical for movement scenes"
            ],
            "costume_designed": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=costume,
            message=f"Costume designed for {period} {style} look",
            metadata={"period": period, "style": style}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate costume design."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            has_elements = len(output.get("costume_elements", {})) >= 3
            result.quality_score = 0.85 if has_elements else 0.7
        return result
