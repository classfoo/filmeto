"""TimingNotes Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class TimingNotesSkill(BaseSkill):
    """Track timing for scenes and takes."""
    
    def __init__(self):
        super().__init__(
            name="timing_notes",
            description="Track scene and take timing for pacing and editing reference",
            required_tools=["get_timeline_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute timing notes."""
        timeline_info = context.execute_tool("get_timeline_info")
        
        timing = {
            "timeline": timeline_info,
            "scene_timings": [
                {"scene": 1, "scripted_duration": 30, "actual_duration": 28},
                {"scene": 2, "scripted_duration": 45, "actual_duration": 52}
            ],
            "pacing_notes": [
                "Scene 1: Slightly faster than scripted",
                "Scene 2: Running long, may need trimming"
            ],
            "total_screen_time": 80
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=timing,
            message="Timing notes recorded",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate timing notes."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
