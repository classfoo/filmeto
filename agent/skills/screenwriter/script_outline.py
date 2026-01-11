"""ScriptOutline Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ScriptOutlineSkill(BaseSkill):
    """Create script outline/structure."""
    
    def __init__(self):
        super().__init__(
            name="script_outline",
            description="Write comprehensive script outline with acts, scenes, and story structure",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute script outline creation."""
        topic = context.parameters.get("topic", "")
        genre = context.parameters.get("genre", "drama")
        duration = context.parameters.get("duration", 60)  # seconds
        
        outline = {
            "title": context.parameters.get("title", "Untitled"),
            "genre": genre,
            "target_duration": duration,
            "logline": f"A story about {topic}" if topic else "A compelling story",
            "structure": {
                "act_1": {
                    "name": "Setup",
                    "percentage": 25,
                    "beats": ["Opening Image", "Theme Stated", "Setup", "Catalyst", "Debate"]
                },
                "act_2a": {
                    "name": "Rising Action",
                    "percentage": 25,
                    "beats": ["Break into Two", "B Story", "Fun and Games", "Midpoint"]
                },
                "act_2b": {
                    "name": "Complications",
                    "percentage": 25,
                    "beats": ["Bad Guys Close In", "All Is Lost", "Dark Night of the Soul"]
                },
                "act_3": {
                    "name": "Resolution",
                    "percentage": 25,
                    "beats": ["Break into Three", "Finale", "Final Image"]
                }
            },
            "scenes_outline": [],
            "character_introductions": [],
            "key_moments": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=outline,
            message=f"Script outline created for {genre} film",
            metadata={"genre": genre, "structure": "four_act"}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate script outline quality."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            has_structure = "structure" in output
            has_logline = bool(output.get("logline"))
            result.quality_score = 0.9 if (has_structure and has_logline) else 0.7
        return result
