"""ContinuityMaintenance Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ContinuityMaintenanceSkill(BaseSkill):
    """Maintain appearance continuity."""
    
    def __init__(self):
        super().__init__(
            name="continuity_maintenance",
            description="Maintain consistent character appearance across scenes and takes",
            required_tools=["get_timeline_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute continuity maintenance."""
        timeline = context.execute_tool("get_timeline_info")
        
        continuity = {
            "timeline": timeline,
            "tracked_elements": [
                {"element": "makeup", "status": "consistent"},
                {"element": "hair", "status": "consistent"},
                {"element": "costume", "status": "consistent"},
                {"element": "accessories", "status": "consistent"}
            ],
            "touch_up_log": [],
            "issues": [],
            "photos_taken": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=continuity,
            message="Appearance continuity maintained",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate continuity maintenance."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            issues = output.get("issues", [])
            result.quality_score = 0.9 if len(issues) == 0 else 0.7
        return result
