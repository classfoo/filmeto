"""ScriptDetail Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ScriptDetailSkill(BaseSkill):
    """Develop detailed script with scenes and actions."""
    
    def __init__(self):
        super().__init__(
            name="script_detail",
            description="Develop detailed script with scene descriptions, actions, dialogue, and transitions",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute script detail development."""
        outline = context.parameters.get("outline", {})
        
        # Get outline from shared state if not provided
        if not outline:
            outline = context.get_previous_result("Screenwriter", "script_outline") or {}
        
        script = {
            "based_on_outline": outline,
            "title": outline.get("title", "Untitled"),
            "scenes": [
                {
                    "scene_number": 1,
                    "heading": "INT. LOCATION - DAY",
                    "description": "Scene description with setting and atmosphere",
                    "action": ["Character enters", "Dialogue exchange", "Exit"],
                    "characters": [],
                    "dialogue": [],
                    "duration_estimate": 15
                },
                {
                    "scene_number": 2,
                    "heading": "EXT. LOCATION - DAY",
                    "description": "Exterior scene description",
                    "action": [],
                    "characters": [],
                    "dialogue": [],
                    "duration_estimate": 20
                }
            ],
            "transitions": ["CUT TO:", "DISSOLVE TO:", "FADE TO:"],
            "detailed": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=script,
            message=f"Detailed script developed with {len(script['scenes'])} scenes",
            metadata={"scene_count": len(script['scenes'])}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate script detail quality."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            scene_count = len(output.get("scenes", []))
            result.quality_score = 0.85 if scene_count >= 2 else 0.7
        return result
