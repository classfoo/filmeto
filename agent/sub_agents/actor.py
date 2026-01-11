"""Actor Agent - Character portrayal and performance."""

from typing import Any, Dict, List, Optional
from agent.sub_agents.base import BaseSubAgent
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ActorAgent(BaseSubAgent):
    """Actor Agent - Portrays characters and performs scenes."""
    
    def __init__(self, llm: Any = None):
        """Initialize Actor Agent."""
        skills = [
            CharacterPortrayalSkill(),
            PerformanceExecutionSkill(),
        ]
        super().__init__(
            name="Actor",
            role="Actor",
            description="Portrays characters, executes performances, and brings characters to life",
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


class CharacterPortrayalSkill(BaseSkill):
    """Portray a character based on character definition."""
    
    def __init__(self):
        super().__init__(
            name="character_portrayal",
            description="Portray a character based on character definition and script requirements",
            required_tools=["list_characters", "get_character_info", "create_task"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute character portrayal."""
        character_id = context.parameters.get("character_id")
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            characters = context.execute_tool("list_characters")
            character_info = characters
        
        portrayal = {
            "character": character_info,
            "portrayal_ready": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=portrayal,
            message="Character portrayal prepared successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate character portrayal."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class PerformanceExecutionSkill(BaseSkill):
    """Execute a performance for a scene."""
    
    def __init__(self):
        super().__init__(
            name="performance_execution",
            description="Execute a performance based on script and direction",
            required_tools=["list_characters", "create_task"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute performance."""
        scene = context.parameters.get("scene", {})
        character_id = context.parameters.get("character_id")
        
        performance = {
            "scene": scene,
            "character_id": character_id,
            "performance_complete": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=performance,
            message="Performance executed successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate performance quality."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.75
        return result
