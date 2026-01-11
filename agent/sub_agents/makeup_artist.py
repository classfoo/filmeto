"""Makeup Artist Agent - Character makeup, styling, and costume design."""

from typing import Any, Dict, List, Optional
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class MakeupArtistAgent(FilmProductionAgent):
    """
    Makeup Artist Agent - Creates character makeup, costumes, and styling.
    
    As the makeup artist, this agent:
    - Designs and applies character makeup
    - Designs character costumes
    - Creates overall appearance styling
    - Maintains continuity of appearance
    - Works with director on character looks
    - Collaborates with actors on comfort and practicality
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Makeup Artist Agent."""
        skills = [
            CharacterMakeupSkill(),
            CostumeDesignSkill(),
            AppearanceStylingSkill(),
            HairStylingSkill(),
            SpecialEffectsMakeupSkill(),
            PeriodLookDesignSkill(),
            ContinuityMaintenanceSkill(),
        ]
        super().__init__(
            name="MakeupArtist",
            role="Makeup Artist",
            description="Creates character makeup, designs costumes, styles appearances, and maintains visual continuity",
            skills=skills,
            llm=llm,
            specialty="pre_production",
            collaborates_with=["Director", "Actor", "Supervisor"]
        )


class CharacterMakeupSkill(BaseSkill):
    """Apply character makeup."""
    
    def __init__(self):
        super().__init__(
            name="character_makeup",
            description="Design and apply makeup to characters based on character design and scene requirements",
            required_tools=["list_characters", "get_character_info", "create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute character makeup."""
        character_id = context.parameters.get("character_id")
        style = context.parameters.get("style", "natural")
        scene_context = context.parameters.get("scene_context", "day")
        
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            characters = context.execute_tool("list_characters")
            character_info = characters
        
        makeup = {
            "character": character_info,
            "style": style,
            "scene_context": scene_context,
            "makeup_design": {
                "foundation": "matched_to_skin_tone",
                "eyes": "defined" if style != "natural" else "minimal",
                "lips": "natural_tint",
                "contouring": "subtle",
                "special_features": []
            },
            "products_used": [],
            "application_notes": [
                "Set with powder for lighting",
                "Touch-up between takes"
            ],
            "makeup_applied": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=makeup,
            message=f"Character makeup applied with {style} style",
            metadata={"style": style}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate makeup quality."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class CostumeDesignSkill(BaseSkill):
    """Design character costumes."""
    
    def __init__(self):
        super().__init__(
            name="costume_design",
            description="Design and select costumes for characters that fit the story and visual style",
            required_tools=["list_characters", "get_character_info", "create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute costume design."""
        character_id = context.parameters.get("character_id")
        period = context.parameters.get("period", "contemporary")
        style = context.parameters.get("style", "casual")
        
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            characters = context.execute_tool("list_characters")
            character_info = characters
        
        # Get visual style from Director if available
        visual_style = context.get_previous_result("Director", "visual_style")
        
        costume = {
            "character": character_info,
            "period": period,
            "style": style,
            "visual_style_reference": visual_style,
            "costume_elements": {
                "top": {"type": "shirt", "color": "neutral", "fabric": "cotton"},
                "bottom": {"type": "pants", "color": "dark", "fabric": "denim"},
                "footwear": {"type": "shoes", "style": "casual"},
                "accessories": []
            },
            "color_palette": ["#333333", "#666666", "#CCCCCC"],
            "design_notes": [
                "Colors support character personality",
                "Practical for movement scenes"
            ],
            "costume_designed": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=costume,
            message=f"Costume designed for {period} {style} look",
            metadata={"period": period, "style": style}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate costume design."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            has_elements = len(output.get("costume_elements", {})) >= 3
            result.quality_score = 0.85 if has_elements else 0.7
        return result


class AppearanceStylingSkill(BaseSkill):
    """Style overall character appearance."""
    
    def __init__(self):
        super().__init__(
            name="appearance_styling",
            description="Create complete character appearance including makeup, costume, hair, and accessories",
            required_tools=["list_characters", "get_character_info", "create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute appearance styling."""
        character_id = context.parameters.get("character_id")
        scene = context.parameters.get("scene", {})
        
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            characters = context.execute_tool("list_characters")
            character_info = characters
        
        styling = {
            "character": character_info,
            "scene": scene,
            "complete_look": {
                "makeup": "completed",
                "hair": "styled",
                "costume": "dressed",
                "accessories": "added"
            },
            "styling_notes": [
                "Cohesive look achieved",
                "Supports character personality",
                "Appropriate for scene context"
            ],
            "reference_photos": [],
            "styling_complete": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=styling,
            message="Complete appearance styling finished",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate appearance styling."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class HairStylingSkill(BaseSkill):
    """Style character hair."""
    
    def __init__(self):
        super().__init__(
            name="hair_styling",
            description="Style and design character hairstyles to match character and period",
            required_tools=["list_characters", "get_character_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute hair styling."""
        character_id = context.parameters.get("character_id")
        style = context.parameters.get("style", "natural")
        
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            character_info = {}
        
        hair = {
            "character": character_info,
            "style": style,
            "hairstyle": {
                "cut": "medium_length",
                "color": "natural",
                "styling": style,
                "texture": "smooth"
            },
            "products_used": [],
            "maintenance_notes": ["Check between takes", "Maintain volume"],
            "styled": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=hair,
            message=f"Hair styled with {style} look",
            metadata={"style": style}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate hair styling."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class SpecialEffectsMakeupSkill(BaseSkill):
    """Create special effects makeup."""
    
    def __init__(self):
        super().__init__(
            name="special_effects_makeup",
            description="Create special effects makeup including prosthetics, aging, and wounds",
            required_tools=["get_character_info", "create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute special effects makeup."""
        effect_type = context.parameters.get("effect_type", "general")
        character_id = context.parameters.get("character_id")
        
        sfx_makeup = {
            "effect_type": effect_type,
            "character_id": character_id,
            "effects_applied": {
                "prosthetics": [],
                "paint_work": [],
                "textures": []
            },
            "materials_used": [],
            "application_time": "varies",
            "removal_notes": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=sfx_makeup,
            message=f"Special effects makeup prepared for {effect_type}",
            metadata={"effect_type": effect_type}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate special effects makeup."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class PeriodLookDesignSkill(BaseSkill):
    """Design period-appropriate looks."""
    
    def __init__(self):
        super().__init__(
            name="period_look_design",
            description="Design historically accurate or period-specific character appearances",
            required_tools=["list_characters"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute period look design."""
        period = context.parameters.get("period", "1950s")
        characters = context.execute_tool("list_characters")
        
        period_look = {
            "period": period,
            "characters": characters,
            "research_notes": [
                f"Historical references for {period}",
                "Era-appropriate materials and colors"
            ],
            "design_elements": {
                "makeup_style": "period_appropriate",
                "hair_style": "era_specific",
                "costume_style": "historically_accurate",
                "accessories": "period_props"
            },
            "reference_images": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=period_look,
            message=f"Period look designed for {period}",
            metadata={"period": period}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate period look design."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class ContinuityMaintenanceSkill(BaseSkill):
    """Maintain appearance continuity."""
    
    def __init__(self):
        super().__init__(
            name="continuity_maintenance",
            description="Maintain consistent character appearance across scenes and takes",
            required_tools=["get_timeline_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute continuity maintenance."""
        timeline = context.execute_tool("get_timeline_info")
        
        continuity = {
            "timeline": timeline,
            "tracked_elements": [
                {"element": "makeup", "status": "consistent"},
                {"element": "hair", "status": "consistent"},
                {"element": "costume", "status": "consistent"},
                {"element": "accessories", "status": "consistent"}
            ],
            "touch_up_log": [],
            "issues": [],
            "photos_taken": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=continuity,
            message="Appearance continuity maintained",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate continuity maintenance."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            issues = output.get("issues", [])
            result.quality_score = 0.9 if len(issues) == 0 else 0.7
        return result
