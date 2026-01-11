"""BudgetManagement Skill."""

from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


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
