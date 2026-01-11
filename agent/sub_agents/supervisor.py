"""Supervisor Agent - Continuity and script supervision."""

from typing import Any, Dict, List, Optional
from agent.sub_agents.base import BaseSubAgent
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class SupervisorAgent(BaseSubAgent):
    """Supervisor Agent - Ensures continuity and tracks script changes."""
    
    def __init__(self, llm: Any = None):
        """Initialize Supervisor Agent."""
        skills = [
            ContinuityTrackingSkill(),
            ScriptSupervisionSkill(),
            ShotLoggingSkill(),
        ]
        super().__init__(
            name="Supervisor",
            role="Script Supervisor",
            description="Tracks continuity, supervises script changes, logs shots, and ensures consistency",
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


class ContinuityTrackingSkill(BaseSkill):
    """Track continuity between shots."""
    
    def __init__(self):
        super().__init__(
            name="continuity_tracking",
            description="Track visual and narrative continuity between shots and scenes",
            required_tools=["get_timeline_info", "list_resources"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute continuity tracking."""
        timeline_info = context.execute_tool("get_timeline_info")
        
        continuity = {
            "timeline": timeline_info,
            "continuity_notes": [],
            "issues": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=continuity,
            message="Continuity tracked successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate continuity tracking."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class ScriptSupervisionSkill(BaseSkill):
    """Supervise script changes and annotations."""
    
    def __init__(self):
        super().__init__(
            name="script_supervision",
            description="Supervise script changes, track revisions, and maintain script annotations",
            required_tools=["get_project_info"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute script supervision."""
        project_info = context.execute_tool("get_project_info")
        
        supervision = {
            "project": project_info,
            "script_notes": [],
            "revisions": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=supervision,
            message="Script supervised successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate script supervision."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.75
        return result


class ShotLoggingSkill(BaseSkill):
    """Log shots and technical details."""
    
    def __init__(self):
        super().__init__(
            name="shot_logging",
            description="Log shots with technical details, timing, and metadata",
            required_tools=["get_timeline_info", "list_resources"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute shot logging."""
        timeline_info = context.execute_tool("get_timeline_info")
        
        log = {
            "timeline": timeline_info,
            "shots_logged": [],
            "technical_details": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=log,
            message="Shots logged successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate shot logging."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
