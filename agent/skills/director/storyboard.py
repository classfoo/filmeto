"""Storyboard Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class StoryboardSkill(BaseSkill):
    """Create storyboard for scenes."""
    
    def __init__(self):
        super().__init__(
            name="storyboard",
            description="Create visual storyboard with shot compositions, camera angles, and scene flow",
            required_tools=["create_task", "list_resources"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute storyboard creation."""
        script = context.parameters.get("script", {})
        scene_description = context.parameters.get("scene_description", "")
        
        # Get previous script data if available
        script_data = context.get_previous_result("Screenwriter", "script_detail")
        if script_data:
            script = script_data
        
        storyboard = {
            "based_on_script": script,
            "panels": [
                {
                    "panel_number": 1,
                    "description": "Establishing shot",
                    "camera_angle": "wide",
                    "duration": 3.0
                },
                {
                    "panel_number": 2,
                    "description": "Character introduction",
                    "camera_angle": "medium",
                    "duration": 5.0
                },
                {
                    "panel_number": 3,
                    "description": "Action sequence",
                    "camera_angle": "close-up",
                    "duration": 4.0
                }
            ],
            "visual_notes": [],
            "camera_movements": ["pan", "zoom", "track"],
            "scene_description": scene_description
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=storyboard,
            message=f"Storyboard created with {len(storyboard['panels'])} panels",
            metadata={"panel_count": len(storyboard['panels'])}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate storyboard quality."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            panel_count = len(output.get("panels", []))
            result.quality_score = 0.9 if panel_count >= 3 else 0.7
        return result
