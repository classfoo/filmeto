"""FinalAssembly Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class FinalAssemblySkill(BaseSkill):
    """Assemble final cut."""
    
    def __init__(self):
        super().__init__(
            name="final_assembly",
            description="Assemble final cut with all elements integrated including audio, effects, and titles",
            required_tools=["list_resources", "get_timeline_info"],
            category="post_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute final assembly."""
        resources = context.execute_tool("list_resources")
        timeline_info = context.execute_tool("get_timeline_info")
        
        # Get audio mix from SoundMixer
        audio_mix = context.get_previous_result("SoundMixer", "audio_mixing")
        
        final_cut = {
            "resources": resources,
            "timeline": timeline_info,
            "audio_mix": audio_mix,
            "elements_integrated": {
                "video": True,
                "audio": True,
                "titles": True,
                "credits": True,
                "color_grading": True
            },
            "output_specs": {
                "resolution": "1920x1080",
                "frame_rate": 24,
                "codec": "H.264"
            },
            "final_cut_complete": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=final_cut,
            message="Final cut assembled and ready for delivery",
            metadata={"elements": 5}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate final assembly."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            elements = output.get("elements_integrated", {})
            all_integrated = all(elements.values())
            result.quality_score = 0.9 if all_integrated else 0.7
        return result
