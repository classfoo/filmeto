"""CoverageTracking Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class CoverageTrackingSkill(BaseSkill):
    """Track camera coverage for scenes."""
    
    def __init__(self):
        super().__init__(
            name="coverage_tracking",
            description="Track camera coverage to ensure all angles needed for editing are captured",
            required_tools=["get_timeline_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute coverage tracking."""
        scene = context.parameters.get("scene", {})
        
        coverage = {
            "scene": scene,
            "coverage_checklist": {
                "master": True,
                "medium_a": True,
                "medium_b": True,
                "close_up_a": True,
                "close_up_b": False,
                "inserts": False
            },
            "missing_coverage": ["close_up_b", "inserts"],
            "recommendations": ["Capture close-up of Character B", "Get insert shots of props"]
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=coverage,
            message="Coverage tracked with recommendations",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate coverage tracking."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            missing = output.get("missing_coverage", [])
            result.quality_score = 0.9 if len(missing) == 0 else 0.7
            if missing:
                result.requires_help = "Director"
        return result
