"""RoughCut Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class RoughCutSkill(BaseSkill):
    """Create rough cut of the film."""
    
    def __init__(self):
        super().__init__(
            name="rough_cut",
            description="Create initial rough cut assembly for review and feedback",
            required_tools=["list_resources", "get_timeline_info"],
            category="post_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute rough cut creation."""
        resources = context.execute_tool("list_resources")
        timeline_info = context.execute_tool("get_timeline_info")
        
        rough_cut = {
            "resources": resources,
            "timeline": timeline_info,
            "structure": "complete",
            "temp_elements": {
                "temp_audio": True,
                "temp_effects": False
            },
            "review_notes": [],
            "version": "rough_cut_v1"
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=rough_cut,
            message="Rough cut assembled for review",
            metadata={"version": "rough_cut_v1"}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate rough cut."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.75  # Rough cut expected to be refined
        return result
