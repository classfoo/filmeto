"""TreatmentWriting Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class TreatmentWritingSkill(BaseSkill):
    """Write script treatment/synopsis."""
    
    def __init__(self):
        super().__init__(
            name="treatment_writing",
            description="Write script treatment or synopsis for project pitching",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute treatment writing."""
        title = context.parameters.get("title", "Untitled")
        genre = context.parameters.get("genre", "drama")
        
        treatment = {
            "title": title,
            "genre": genre,
            "logline": "",
            "synopsis": {
                "short": "One paragraph summary",
                "long": "Full treatment with story details"
            },
            "tone": "",
            "visual_style": "",
            "target_audience": ""
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=treatment,
            message="Treatment written",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate treatment writing."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
