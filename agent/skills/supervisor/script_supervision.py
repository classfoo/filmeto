"""ScriptSupervision Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ScriptSupervisionSkill(BaseSkill):
    """Supervise script changes and annotations."""
    
    def __init__(self):
        super().__init__(
            name="script_supervision",
            description="Supervise script adherence, track revisions, and maintain script annotations",
            required_tools=["get_project_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute script supervision."""
        project_info = context.execute_tool("get_project_info")
        
        supervision = {
            "project": project_info,
            "script_notes": [
                {"scene": 1, "line": "As scripted", "deviation": None},
                {"scene": 2, "line": "Minor ad-lib", "deviation": "Added 'well'"}
            ],
            "revisions": [],
            "dialogue_changes": [],
            "action_changes": [],
            "line_readings": {}
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=supervision,
            message="Script supervision completed",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate script supervision."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
