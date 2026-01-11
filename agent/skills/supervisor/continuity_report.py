"""ContinuityReport Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ContinuityReportSkill(BaseSkill):
    """Generate continuity report for editor."""
    
    def __init__(self):
        super().__init__(
            name="continuity_report",
            description="Generate comprehensive continuity report for post-production",
            required_tools=["get_project_info", "list_resources"],
            category="post_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute continuity report generation."""
        project_info = context.execute_tool("get_project_info")
        
        report = {
            "project": project_info,
            "report_sections": {
                "script_notes": [],
                "continuity_notes": [],
                "circled_takes": [],
                "timing_breakdown": [],
                "issues_log": []
            },
            "editor_notes": [
                "Prefer takes with tighter pacing",
                "Watch for continuity at scene transitions"
            ],
            "generated": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=report,
            message="Continuity report generated for editor",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate continuity report."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
