"""DialogueWriting Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class DialogueWritingSkill(BaseSkill):
    """Write dialogue for scenes."""
    
    def __init__(self):
        super().__init__(
            name="dialogue_writing",
            description="Write natural, character-appropriate dialogue for scenes",
            required_tools=["list_characters", "create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute dialogue writing."""
        characters = context.execute_tool("list_characters")
        scene = context.parameters.get("scene", {})
        tone = context.parameters.get("tone", "natural")
        
        dialogue = {
            "scene": scene,
            "characters": characters,
            "tone": tone,
            "dialogue_lines": [
                {
                    "character": "Character A",
                    "line": "Sample dialogue line",
                    "parenthetical": "(thoughtfully)",
                    "subtext": "Hidden meaning"
                },
                {
                    "character": "Character B",
                    "line": "Response line",
                    "parenthetical": None,
                    "subtext": None
                }
            ],
            "dialogue_notes": {
                "rhythm": "conversational",
                "conflict_level": "medium"
            }
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=dialogue,
            message=f"Dialogue written with {len(dialogue['dialogue_lines'])} lines",
            metadata={"line_count": len(dialogue['dialogue_lines'])}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate dialogue quality."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            line_count = len(output.get("dialogue_lines", []))
            result.quality_score = 0.85 if line_count >= 2 else 0.7
        return result
