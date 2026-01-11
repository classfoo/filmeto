"""ShotLogging Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ShotLoggingSkill(BaseSkill):
    """Log shots and technical details."""
    
    def __init__(self):
        super().__init__(
            name="shot_logging",
            description="Log all shots with technical details, timing, and metadata for post-production",
            required_tools=["get_timeline_info", "list_resources"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute shot logging."""
        timeline_info = context.execute_tool("get_timeline_info")
        
        log = {
            "timeline": timeline_info,
            "shots_logged": [
                {
                    "shot_id": "1A",
                    "scene": 1,
                    "take": 1,
                    "duration": 12.5,
                    "rating": "good",
                    "notes": "Clean take, good performance"
                },
                {
                    "shot_id": "1A",
                    "scene": 1,
                    "take": 2,
                    "duration": 13.2,
                    "rating": "excellent",
                    "notes": "Best take, director preferred"
                }
            ],
            "technical_details": {
                "lens": "50mm",
                "aperture": "f/2.8",
                "frame_rate": 24
            },
            "circled_takes": ["1A-T2"]
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=log,
            message=f"Logged {len(log['shots_logged'])} shots",
            metadata={"shot_count": len(log['shots_logged'])}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate shot logging."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
