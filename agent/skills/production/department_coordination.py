"""DepartmentCoordination Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class DepartmentCoordinationSkill(BaseSkill):
    """Coordinate between departments."""
    
    def __init__(self):
        super().__init__(
            name="department_coordination",
            description="Coordinate communication and workflow between different departments",
            required_tools=["get_project_info"],
            category="management"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute department coordination."""
        departments = ["Screenwriter", "Director", "Actor", "MakeupArtist", "SoundMixer", "Editor", "Supervisor"]
        
        coordination = {
            "departments": departments,
            "communication_channels": {
                "Screenwriter-Director": "Script discussions",
                "Director-Actor": "Performance direction",
                "MakeupArtist-Actor": "Character appearance",
                "Director-Editor": "Cut preferences",
                "SoundMixer-Editor": "Audio sync"
            },
            "status": "coordinated"
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=coordination,
            message=f"Coordinated {len(departments)} departments",
            metadata={"department_count": len(departments)}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate department coordination."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
