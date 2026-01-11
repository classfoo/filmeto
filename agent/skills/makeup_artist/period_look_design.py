"""PeriodLookDesign Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class PeriodLookDesignSkill(BaseSkill):
    """Design period-appropriate looks."""
    
    def __init__(self):
        super().__init__(
            name="period_look_design",
            description="Design historically accurate or period-specific character appearances",
            required_tools=["list_characters"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute period look design."""
        period = context.parameters.get("period", "1950s")
        characters = context.execute_tool("list_characters")
        
        period_look = {
            "period": period,
            "characters": characters,
            "research_notes": [
                f"Historical references for {period}",
                "Era-appropriate materials and colors"
            ],
            "design_elements": {
                "makeup_style": "period_appropriate",
                "hair_style": "era_specific",
                "costume_style": "historically_accurate",
                "accessories": "period_props"
            },
            "reference_images": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=period_look,
            message=f"Period look designed for {period}",
            metadata={"period": period}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate period look design."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
