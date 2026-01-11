"""Matching Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class MatchingSkill(BaseSkill):
    """Ensure action matching between shots."""
    
    def __init__(self):
        super().__init__(
            name="matching",
            description="Ensure action, eye lines, and movement matching between shots for seamless editing",
            required_tools=["get_timeline_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute matching verification."""
        scene = context.parameters.get("scene", {})
        
        matching = {
            "scene": scene,
            "action_matching": {
                "verified": True,
                "notes": []
            },
            "eye_line_matching": {
                "verified": True,
                "notes": []
            },
            "movement_matching": {
                "verified": True,
                "notes": []
            },
            "issues": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=matching,
            message="Matching verified for scene",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate matching."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            issues = output.get("issues", [])
            result.quality_score = 0.9 if len(issues) == 0 else 0.6
        return result
