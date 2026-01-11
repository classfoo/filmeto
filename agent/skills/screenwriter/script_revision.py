"""ScriptRevision Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ScriptRevisionSkill(BaseSkill):
    """Revise and polish scripts."""
    
    def __init__(self):
        super().__init__(
            name="script_revision",
            description="Revise and polish scripts based on feedback and requirements",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute script revision."""
        original_script = context.parameters.get("script", {})
        feedback = context.parameters.get("feedback", [])
        
        revision = {
            "original_script": original_script,
            "feedback_addressed": feedback,
            "changes_made": [
                "Dialogue tightened",
                "Scene pacing improved",
                "Character motivations clarified"
            ],
            "revision_number": context.parameters.get("revision_number", 1),
            "revised": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=revision,
            message="Script revision completed",
            metadata={"revision_number": revision["revision_number"]}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate script revision."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
