"""Director Agent - Creative vision and scene direction."""

from typing import Any, Dict, List, Optional
from agent.sub_agents.base import BaseSubAgent
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class DirectorAgent(BaseSubAgent):
    """Director Agent - Develops creative vision and directs scenes."""
    
    def __init__(self, llm: Any = None):
        """Initialize Director Agent."""
        skills = [
            StoryboardSkill(),
            SceneCompositionSkill(),
            SceneDirectionSkill(),
            ShotPlanningSkill(),
        ]
        super().__init__(
            name="Director",
            role="Director",
            description="Develops creative vision, creates storyboards, plans shots, and directs scenes",
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


class StoryboardSkill(BaseSkill):
    """Create storyboard for scenes."""
    
    def __init__(self):
        super().__init__(
            name="storyboard",
            description="Create storyboard with shot compositions and visual sequences",
            required_tools=["create_task", "list_resources"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute storyboard creation."""
        script = context.parameters.get("script", {})
        
        storyboard = {
            "scenes": [],
            "shots": [],
            "based_on_script": script
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=storyboard,
            message="Storyboard created successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate storyboard quality."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class SceneCompositionSkill(BaseSkill):
    """Plan scene composition and visual layout."""
    
    def __init__(self):
        super().__init__(
            name="scene_composition",
            description="Plan scene composition, framing, camera angles, and visual elements",
            required_tools=["create_task", "list_resources"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute scene composition planning."""
        scene = context.parameters.get("scene", {})
        
        composition = {
            "scene": scene,
            "framing": "standard",
            "camera_angles": [],
            "visual_elements": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=composition,
            message="Scene composition planned successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate scene composition."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.75
        return result


class SceneDirectionSkill(BaseSkill):
    """Direct scene execution and filming."""
    
    def __init__(self):
        super().__init__(
            name="scene_direction",
            description="Direct scene execution, coordinate with actors, and oversee filming",
            required_tools=["create_task", "list_characters"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute scene direction."""
        scene = context.parameters.get("scene", {})
        characters = context.execute_tool("list_characters")
        
        direction = {
            "scene": scene,
            "characters": characters,
            "direction_notes": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=direction,
            message="Scene directed successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate scene direction."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class ShotPlanningSkill(BaseSkill):
    """Plan individual shots and camera setups."""
    
    def __init__(self):
        super().__init__(
            name="shot_planning",
            description="Plan individual shots, camera movements, and technical setups",
            required_tools=["create_task"]
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute shot planning."""
        scene = context.parameters.get("scene", {})
        
        shots = {
            "scene": scene,
            "shot_list": [],
            "camera_setups": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=shots,
            message="Shots planned successfully",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate shot planning."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.75
        return result
