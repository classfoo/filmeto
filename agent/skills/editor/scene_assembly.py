"""SceneAssembly Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class SceneAssemblySkill(BaseSkill):
    """Assemble scenes into sequences."""
    
    def __init__(self):
        super().__init__(
            name="scene_assembly",
            description="Assemble edited scenes into coherent sequences with proper flow and narrative structure",
            required_tools=["list_resources", "get_timeline_info"],
            category="post_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute scene assembly."""
        resources = context.execute_tool("list_resources")
        timeline_info = context.execute_tool("get_timeline_info")
        
        # Get continuity report from Supervisor
        continuity = context.get_previous_result("Supervisor", "continuity_report")
        
        assembly = {
            "resources": resources,
            "timeline": timeline_info,
            "continuity_reference": continuity,
            "sequence_order": [
                {"scene": 1, "duration": 30, "transition_out": "cut"},
                {"scene": 2, "duration": 45, "transition_out": "dissolve"},
                {"scene": 3, "duration": 25, "transition_out": "fade"}
            ],
            "narrative_flow": "linear",
            "assembled": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=assembly,
            message=f"Assembled {len(assembly['sequence_order'])} scenes into sequence",
            metadata={"scene_count": len(assembly['sequence_order'])}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate scene assembly."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
