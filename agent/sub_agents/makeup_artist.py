"""Makeup Artist Agent - Character makeup and styling."""

from typing import Any, Dict, List, Optional
from agent.sub_agents.base import BaseSubAgent
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class MakeupArtistAgent(BaseSubAgent):
    """Makeup Artist Agent - Creates character makeup and styling."""
    
    def __init__(self, llm: Any = None):
        """Initialize Makeup Artist Agent."""
        skills = [
            CharacterMakeupSkill(),
            CostumeDesignSkill(),
            AppearanceStylingSkill(),
        ]
        super().__init__(
            name="MakeupArtist",
            role="Makeup Artist",
            description="Creates character makeup, designs costumes, and styles appearances",
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


class CharacterMakeupSkill(BaseSkill):
    """Apply character makeup."""
    
    def __init__(self):
        super().__init__(
            name="character_makeup",
            description="Apply makeup to characters based on character design and scene requirements",
            required_tools=["list_characters", "get_character_info", "create_task"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute character makeup."""
        character_id = context.parameters.get("character_id")
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            characters = context.execute_tool("list_characters")
            character_info = characters
        
        makeup = {
            "character": character_info,
            "makeup_applied": True,
            "makeup_style": context.parameters.get("style", "natural")
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=makeup,
            message="Character makeup applied successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate makeup quality."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class CostumeDesignSkill(BaseSkill):
    """Design character costumes."""
    
    def __init__(self):
        super().__init__(
            name="costume_design",
            description="Design and select costumes for characters",
            required_tools=["list_characters", "get_character_info", "create_task"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute costume design."""
        character_id = context.parameters.get("character_id")
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            characters = context.execute_tool("list_characters")
            character_info = characters
        
        costume = {
            "character": character_info,
            "costume_designed": True,
            "costume_style": context.parameters.get("style", "period")
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=costume,
            message="Costume designed successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate costume design."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.75
        return result


class AppearanceStylingSkill(BaseSkill):
    """Style character appearance."""
    
    def __init__(self):
        super().__init__(
            name="appearance_styling",
            description="Style overall character appearance including makeup, costume, and accessories",
            required_tools=["list_characters", "get_character_info", "create_task"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute appearance styling."""
        character_id = context.parameters.get("character_id")
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            characters = context.execute_tool("list_characters")
            character_info = characters
        
        styling = {
            "character": character_info,
            "styling_complete": True,
            "appearance_elements": ["makeup", "costume", "accessories"]
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=styling,
            message="Appearance styled successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate appearance styling."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
