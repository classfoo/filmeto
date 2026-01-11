"""ProjectPlanning Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ProjectPlanningSkill(BaseSkill):
    """Plan project structure and workflow."""
    
    def __init__(self):
        super().__init__(
            name="project_planning",
            description="Create comprehensive project plan with phases, milestones, and dependencies",
            required_tools=["get_project_info", "list_resources"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute project planning."""
        # Get project info
        project_info = context.execute_tool("get_project_info")
        resources = context.execute_tool("list_resources")
        
        # Get parameters
        project_type = context.parameters.get("project_type", "short_film")
        target_duration = context.parameters.get("target_duration", 60)  # seconds
        
        # Create comprehensive plan
        plan = {
            "project_info": project_info,
            "available_resources": resources,
            "project_type": project_type,
            "target_duration": target_duration,
            "phases": [
                {
                    "name": "Pre-Production",
                    "duration_days": 7,
                    "tasks": [
                        "Script development",
                        "Storyboard creation",
                        "Character design",
                        "Costume design",
                        "Location scouting"
                    ]
                },
                {
                    "name": "Production",
                    "duration_days": 14,
                    "tasks": [
                        "Scene setup",
                        "Actor preparation",
                        "Scene shooting",
                        "Audio recording"
                    ]
                },
                {
                    "name": "Post-Production",
                    "duration_days": 10,
                    "tasks": [
                        "Video editing",
                        "Audio mixing",
                        "Color grading",
                        "Final assembly"
                    ]
                }
            ],
            "milestones": [
                "Script approval",
                "Storyboard completion",
                "Principal photography wrap",
                "Rough cut",
                "Final cut"
            ]
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=plan,
            message="Project plan created successfully with 3 phases and 5 milestones",
            metadata={"plan_type": "comprehensive", "phases": 3}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate project plan quality."""
        if result.status == SkillStatus.SUCCESS:
            plan = result.output or {}
            # Check plan completeness
            has_phases = len(plan.get("phases", [])) >= 3
            has_milestones = len(plan.get("milestones", [])) >= 3
            result.quality_score = 0.9 if (has_phases and has_milestones) else 0.7
        return result
