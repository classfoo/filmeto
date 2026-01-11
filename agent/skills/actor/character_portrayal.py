"""Character Portrayal Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class CharacterPortrayalSkill(BaseSkill):
    """Portray a character based on character definition."""
    
    def __init__(self):
        super().__init__(
            name="character_portrayal",
            description="Portray a character based on character definition, backstory, and script requirements",
            required_tools=["list_characters", "get_character_info", "create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute character portrayal."""
        character_id = context.parameters.get("character_id")
        
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            characters = context.execute_tool("list_characters")
            character_info = characters
        
        # Get makeup/styling info from shared state
        styling = context.get_previous_result("MakeupArtist", "appearance_styling")
        
        portrayal = {
            "character": character_info,
            "styling": styling,
            "interpretation": {
                "personality_traits": [],
                "motivations": [],
                "mannerisms": [],
                "speech_patterns": []
            },
            "physical_choices": {
                "posture": "confident",
                "gait": "purposeful",
                "gestures": []
            },
            "vocal_choices": {
                "pitch": "natural",
                "pace": "measured",
                "accent": None
            },
            "portrayal_ready": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=portrayal,
            message="Character portrayal prepared",
            metadata={"character_id": character_id}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate character portrayal."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
