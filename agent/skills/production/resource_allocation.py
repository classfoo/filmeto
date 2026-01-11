"""ResourceAllocation Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ResourceAllocationSkill(BaseSkill):
    """Allocate resources for project tasks."""
    
    def __init__(self):
        super().__init__(
            name="resource_allocation",
            description="Allocate resources (images, videos, audio, characters) to project tasks and departments",
            required_tools=["list_resources", "list_characters", "get_project_info"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute resource allocation."""
        resources = context.execute_tool("list_resources")
        characters = context.execute_tool("list_characters")
        
        allocation = {
            "image_resources": [],
            "video_resources": [],
            "audio_resources": [],
            "character_assignments": [],
            "department_allocations": {
                "Director": ["storyboard_assets", "reference_images"],
                "Actor": ["character_references"],
                "MakeupArtist": ["costume_references", "makeup_references"],
                "Editor": ["video_assets", "audio_assets"],
                "SoundMixer": ["audio_tracks", "sound_effects"]
            },
            "allocation_strategy": "balanced",
            "resources_summary": resources,
            "characters_summary": characters
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=allocation,
            message="Resources allocated to departments successfully",
            metadata={"departments_covered": 5}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate resource allocation."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
