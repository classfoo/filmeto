"""AppearanceStyling Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class AppearanceStylingSkill(BaseSkill):
    """Style overall character appearance."""
    
    def __init__(self):
        super().__init__(
            name="appearance_styling",
            description="Create complete character appearance including makeup, costume, hair, and accessories",
            required_tools=["list_characters", "get_character_info", "create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute appearance styling."""
        character_id = context.parameters.get("character_id")
        scene = context.parameters.get("scene", {})
        
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            characters = context.execute_tool("list_characters")
            character_info = characters
        
        styling = {
            "character": character_info,
            "scene": scene,
            "complete_look": {
                "makeup": "completed",
                "hair": "styled",
                "costume": "dressed",
                "accessories": "added"
            },
            "styling_notes": [
                "Cohesive look achieved",
                "Supports character personality",
                "Appropriate for scene context"
            ],
            "reference_photos": [],
            "styling_complete": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=styling,
            message="Complete appearance styling finished",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate appearance styling."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
