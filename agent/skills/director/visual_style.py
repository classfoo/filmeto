"""VisualStyle Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class VisualStyleSkill(BaseSkill):
    """Define visual style for the project."""
    
    def __init__(self):
        super().__init__(
            name="visual_style",
            description="Define the overall visual style, color palette, and aesthetic direction",
            required_tools=["list_resources"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute visual style definition."""
        genre = context.parameters.get("genre", "drama")
        mood = context.parameters.get("mood", "neutral")
        
        style = {
            "genre": genre,
            "mood": mood,
            "color_palette": {
                "primary": "#1a1a2e",
                "secondary": "#16213e",
                "accent": "#e94560"
            },
            "lighting_style": "high_contrast" if genre == "thriller" else "natural",
            "camera_style": "handheld" if mood == "tense" else "steady",
            "aspect_ratio": "2.39:1",
            "visual_references": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=style,
            message=f"Visual style defined for {genre} with {mood} mood",
            metadata={"genre": genre, "mood": mood}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate visual style."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
