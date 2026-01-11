"""ShotPlanning Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ShotPlanningSkill(BaseSkill):
    """Plan individual shots and camera setups."""
    
    def __init__(self):
        super().__init__(
            name="shot_planning",
            description="Plan individual shots, camera movements, and technical setups",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute shot planning."""
        scene = context.parameters.get("scene", {})
        
        shots = {
            "scene": scene,
            "shot_list": [
                {"shot_id": 1, "type": "establishing", "duration": 3.0, "camera": "static"},
                {"shot_id": 2, "type": "medium", "duration": 5.0, "camera": "slight_push"},
                {"shot_id": 3, "type": "close_up", "duration": 2.0, "camera": "static"},
                {"shot_id": 4, "type": "reaction", "duration": 2.0, "camera": "handheld"}
            ],
            "camera_setups": [
                {"setup_id": 1, "position": "A", "lens": "35mm"},
                {"setup_id": 2, "position": "B", "lens": "50mm"},
                {"setup_id": 3, "position": "C", "lens": "85mm"}
            ],
            "coverage_plan": "standard"
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=shots,
            message=f"Planned {len(shots['shot_list'])} shots with {len(shots['camera_setups'])} camera setups",
            metadata={"shot_count": len(shots['shot_list'])}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate shot planning."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            shot_count = len(output.get("shot_list", []))
            result.quality_score = 0.85 if shot_count >= 3 else 0.7
        return result
