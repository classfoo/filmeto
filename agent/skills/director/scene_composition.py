"""SceneComposition Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class SceneCompositionSkill(BaseSkill):
    """Plan scene composition and visual layout."""
    
    def __init__(self):
        super().__init__(
            name="scene_composition",
            description="Plan scene composition, framing, camera angles, lighting, and visual elements",
            required_tools=["create_task", "list_resources"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute scene composition planning."""
        scene = context.parameters.get("scene", {})
        mood = context.parameters.get("mood", "neutral")
        
        composition = {
            "scene": scene,
            "framing": {
                "type": "rule_of_thirds",
                "focus_point": "center",
                "depth_of_field": "shallow"
            },
            "camera_angles": [
                {"name": "establishing", "type": "wide", "height": "eye_level"},
                {"name": "dialogue", "type": "medium", "height": "eye_level"},
                {"name": "reaction", "type": "close_up", "height": "eye_level"}
            ],
            "lighting": {
                "type": "three_point",
                "mood": mood,
                "key_light_position": "45_degrees"
            },
            "visual_elements": {
                "foreground": [],
                "midground": ["characters"],
                "background": ["setting"]
            },
            "color_palette": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=composition,
            message="Scene composition planned with framing, lighting, and camera angles",
            metadata={"mood": mood}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate scene composition."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
