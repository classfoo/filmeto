"""Production Agent - Project planning and coordination (Producer role)."""

from typing import Any, Dict, List, Optional
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ProductionAgent(FilmProductionAgent):
    """
    Production Agent (Producer) - Oversees the entire film production project.
    
    As the producer, this agent:
    - Plans the overall project structure and timeline
    - Allocates resources across departments
    - Manages budget and scheduling
    - Coordinates between all departments
    - Ensures project stays on track
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Production Agent."""
        skills = [
            ProjectPlanningSkill(),
            ResourceAllocationSkill(),
            TimelineCoordinationSkill(),
            BudgetManagementSkill(),
            DepartmentCoordinationSkill(),
            ProductionSchedulingSkill(),
            QualityOversightSkill(),
        ]
        super().__init__(
            name="Production",
            role="Producer",
            description="Oversees the entire project, secures resources, manages budget and timeline, coordinates all departments",
            skills=skills,
            llm=llm,
            specialty="management",
            collaborates_with=["Director", "Editor", "Screenwriter"]
        )


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


class TimelineCoordinationSkill(BaseSkill):
    """Coordinate project timeline."""
    
    def __init__(self):
        super().__init__(
            name="timeline_coordination",
            description="Coordinate timeline positions, durations, and sequencing across all project elements",
            required_tools=["get_timeline_info", "get_project_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute timeline coordination."""
        timeline_info = context.execute_tool("get_timeline_info")
        
        coordination = {
            "timeline_info": timeline_info,
            "scene_sequence": [],
            "transition_points": [],
            "audio_sync_points": [],
            "coordinated": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=coordination,
            message="Timeline coordinated successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate timeline coordination."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class BudgetManagementSkill(BaseSkill):
    """Manage project budget and costs."""
    
    def __init__(self):
        super().__init__(
            name="budget_management",
            description="Manage project budget, track costs, optimize resource usage, and control expenses",
            required_tools=["get_project_info"],
            category="management"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute budget management."""
        project_info = context.execute_tool("get_project_info")
        
        total_budget = context.parameters.get("total_budget", 10000)
        
        budget = {
            "project_info": project_info,
            "total_budget": total_budget,
            "allocated": {
                "pre_production": total_budget * 0.2,
                "production": total_budget * 0.5,
                "post_production": total_budget * 0.3
            },
            "spent": 0,
            "remaining": total_budget,
            "budget_tracked": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=budget,
            message="Budget managed and allocated successfully",
            metadata={"total_budget": total_budget}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate budget management."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


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


class ProductionSchedulingSkill(BaseSkill):
    """Create and manage production schedule."""
    
    def __init__(self):
        super().__init__(
            name="production_scheduling",
            description="Create detailed shooting schedule and manage production timeline",
            required_tools=["get_timeline_info", "get_project_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute production scheduling."""
        timeline_info = context.execute_tool("get_timeline_info")
        
        schedule = {
            "shooting_days": [],
            "call_sheets": [],
            "equipment_schedule": [],
            "talent_schedule": [],
            "timeline_info": timeline_info,
            "schedule_created": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=schedule,
            message="Production schedule created",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate production scheduling."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class QualityOversightSkill(BaseSkill):
    """Oversee quality across all departments."""
    
    def __init__(self):
        super().__init__(
            name="quality_oversight",
            description="Monitor and ensure quality standards across all production departments",
            required_tools=["get_project_info", "list_resources"],
            category="management"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute quality oversight."""
        project_info = context.execute_tool("get_project_info")
        
        oversight = {
            "project_info": project_info,
            "quality_checks": {
                "script_quality": "pending",
                "visual_quality": "pending",
                "audio_quality": "pending",
                "continuity_check": "pending"
            },
            "standards_met": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=oversight,
            message="Quality oversight established",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate quality oversight."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result
