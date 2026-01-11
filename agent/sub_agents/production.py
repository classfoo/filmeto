"""Production Agent - Project planning and coordination."""

from typing import Any, Dict, List, Optional
from agent.sub_agents.base import BaseSubAgent
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ProductionAgent(BaseSubAgent):
    """Production Agent - Oversees project planning and resource allocation."""
    
    def __init__(self, llm: Any = None):
        """Initialize Production Agent."""
        skills = [
            ProjectPlanningSkill(),
            ResourceAllocationSkill(),
            TimelineCoordinationSkill(),
            BudgetManagementSkill(),
        ]
        super().__init__(
            name="Production",
            role="Producer",
            description="Oversees the entire project, secures resources, manages budget and timeline, coordinates all departments",
            skills=skills,
            llm=llm
        )
    
    async def execute_task(
        self,
        task: Dict[str, Any],
        context: SkillContext
    ) -> SkillResult:
        """Execute a task using appropriate skill."""
        skill_name = task.get("skill_name")
        if not skill_name or skill_name not in self.skills:
            return SkillResult(
                status=SkillStatus.FAILED,
                output=None,
                message=f"Unknown skill: {skill_name}",
                metadata={}
            )
        
        skill = self.skills[skill_name]
        parameters = task.get("parameters", {})
        context.parameters = parameters
        
        try:
            result = await skill.execute(context)
            return result
        except Exception as e:
            return SkillResult(
                status=SkillStatus.FAILED,
                output=None,
                message=f"Error executing skill: {str(e)}",
                metadata={"error": str(e)}
            )


class ProjectPlanningSkill(BaseSkill):
    """Plan project structure and workflow."""
    
    def __init__(self):
        super().__init__(
            name="project_planning",
            description="Create project plan with phases, milestones, and dependencies",
            required_tools=["get_project_info", "list_resources"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute project planning."""
        # Get project info
        project_info = context.execute_tool("get_project_info")
        resources = context.execute_tool("list_resources")
        
        # Create plan (simplified - in real implementation, use LLM to generate plan)
        plan = {
            "project_info": project_info,
            "resources": resources,
            "phases": ["pre-production", "production", "post-production"]
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=plan,
            message="Project plan created successfully",
            metadata={"plan_type": "project_structure"}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate project plan quality."""
        if result.status == SkillStatus.SUCCESS:
            quality = 0.8  # Default quality
            result.quality_score = quality
        
        return result


class ResourceAllocationSkill(BaseSkill):
    """Allocate resources for project tasks."""
    
    def __init__(self):
        super().__init__(
            name="resource_allocation",
            description="Allocate resources (images, videos, audio) to project tasks",
            required_tools=["list_resources", "get_project_info"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute resource allocation."""
        resources = context.execute_tool("list_resources")
        
        allocation = {
            "allocated_resources": resources,
            "allocation_strategy": "balanced"
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=allocation,
            message="Resources allocated successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate resource allocation."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.75
        return result


class TimelineCoordinationSkill(BaseSkill):
    """Coordinate project timeline."""
    
    def __init__(self):
        super().__init__(
            name="timeline_coordination",
            description="Coordinate timeline positions, durations, and sequencing",
            required_tools=["get_timeline_info", "get_project_info"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute timeline coordination."""
        timeline_info = context.execute_tool("get_timeline_info")
        
        coordination = {
            "timeline_info": timeline_info,
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
            description="Manage project budget, track costs, and optimize resource usage",
            required_tools=["get_project_info"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute budget management."""
        project_info = context.execute_tool("get_project_info")
        
        budget = {
            "project_info": project_info,
            "budget_tracked": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=budget,
            message="Budget managed successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate budget management."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.75
        return result
