"""CameraWork Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class CameraWorkSkill(BaseSkill):
    """Plan camera work and movements."""
    
    def __init__(self):
        super().__init__(
            name="camera_work",
            description="Plan detailed camera movements, angles, and technical specifications",
            required_tools=["create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute camera work planning."""
        scene = context.parameters.get("scene", {})
        
        camera_work = {
            "scene": scene,
            "movements": [
                {"type": "dolly_in", "start": 0.0, "end": 3.0, "speed": "slow"},
                {"type": "pan", "start": 3.0, "end": 5.0, "direction": "left"},
                {"type": "static", "start": 5.0, "end": 10.0}
            ],
            "lens_choices": {
                "wide": "24mm",
                "medium": "50mm",
                "close": "85mm"
            },
            "exposure_settings": {
                "iso": 400,
                "aperture": "f/2.8",
                "shutter": "1/50"
            }
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=camera_work,
            message="Camera work planned with movements and technical specs",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate camera work."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
