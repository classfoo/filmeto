"""Actor Agent - Character portrayal and performance."""

from typing import Any, Dict, List, Optional
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ActorAgent(FilmProductionAgent):
    """
    Actor Agent - Portrays characters and performs scenes.
    
    As the actor, this agent:
    - Portrays characters based on character definitions
    - Executes performances as directed
    - Interprets dialogue and emotions
    - Works with director on scene execution
    - Coordinates with makeup artist for appearance
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Actor Agent."""
        skills = [
            CharacterPortrayalSkill(),
            PerformanceExecutionSkill(),
            EmotionalExpressionSkill(),
            DialogueDeliverySkill(),
            PhysicalActingSkill(),
            CharacterStudySkill(),
            SceneRehearsalSkill(),
        ]
        super().__init__(
            name="Actor",
            role="Actor",
            description="Portrays characters, executes performances, and brings characters to life through acting",
            skills=skills,
            llm=llm,
            specialty="production",
            collaborates_with=["Director", "MakeupArtist", "Screenwriter"]
        )


class CharacterPortrayalSkill(BaseSkill):
    """Portray a character based on character definition."""
    
    def __init__(self):
        super().__init__(
            name="character_portrayal",
            description="Portray a character based on character definition, backstory, and script requirements",
            required_tools=["list_characters", "get_character_info", "create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute character portrayal."""
        character_id = context.parameters.get("character_id")
        
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            characters = context.execute_tool("list_characters")
            character_info = characters
        
        # Get makeup/styling info from shared state
        styling = context.get_previous_result("MakeupArtist", "appearance_styling")
        
        portrayal = {
            "character": character_info,
            "styling": styling,
            "interpretation": {
                "personality_traits": [],
                "motivations": [],
                "mannerisms": [],
                "speech_patterns": []
            },
            "physical_choices": {
                "posture": "confident",
                "gait": "purposeful",
                "gestures": []
            },
            "vocal_choices": {
                "pitch": "natural",
                "pace": "measured",
                "accent": None
            },
            "portrayal_ready": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=portrayal,
            message="Character portrayal prepared",
            metadata={"character_id": character_id}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate character portrayal."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class PerformanceExecutionSkill(BaseSkill):
    """Execute a performance for a scene."""
    
    def __init__(self):
        super().__init__(
            name="performance_execution",
            description="Execute a complete performance based on script, direction, and character interpretation",
            required_tools=["list_characters", "create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute performance."""
        scene = context.parameters.get("scene", {})
        character_id = context.parameters.get("character_id")
        
        # Get direction from Director
        direction = context.get_previous_result("Director", "scene_direction")
        
        performance = {
            "scene": scene,
            "character_id": character_id,
            "direction_followed": direction,
            "takes": [
                {
                    "take_number": 1,
                    "notes": "First take - establishing",
                    "quality": "good"
                }
            ],
            "emotional_arc": {
                "start": "neutral",
                "peak": "intense",
                "end": "resolved"
            },
            "performance_complete": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=performance,
            message="Performance executed successfully",
            metadata={"takes": 1}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate performance quality."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class EmotionalExpressionSkill(BaseSkill):
    """Express emotions in performance."""
    
    def __init__(self):
        super().__init__(
            name="emotional_expression",
            description="Express specific emotions through facial expressions, body language, and voice",
            required_tools=["create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute emotional expression."""
        emotion = context.parameters.get("emotion", "neutral")
        intensity = context.parameters.get("intensity", "medium")
        
        expression = {
            "emotion": emotion,
            "intensity": intensity,
            "facial_elements": {
                "eyes": "focused",
                "eyebrows": "raised" if emotion == "surprise" else "neutral",
                "mouth": "slight_smile" if emotion == "happy" else "neutral"
            },
            "body_language": {
                "posture": "open" if emotion == "happy" else "closed",
                "tension": intensity
            },
            "vocal_quality": {
                "tone": "warm" if emotion == "happy" else "measured",
                "volume": "normal",
                "pace": "natural"
            }
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=expression,
            message=f"Emotional expression prepared for {emotion}",
            metadata={"emotion": emotion, "intensity": intensity}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate emotional expression."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class DialogueDeliverySkill(BaseSkill):
    """Deliver dialogue effectively."""
    
    def __init__(self):
        super().__init__(
            name="dialogue_delivery",
            description="Deliver dialogue with appropriate emotion, timing, and character voice",
            required_tools=["create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute dialogue delivery."""
        lines = context.parameters.get("lines", [])
        emotion = context.parameters.get("emotion", "neutral")
        
        delivery = {
            "lines": lines,
            "emotion": emotion,
            "delivery_choices": {
                "pacing": "natural",
                "emphasis": [],
                "pauses": [],
                "subtext": []
            },
            "voice_modulation": {
                "pitch_variation": "moderate",
                "volume_changes": [],
                "breath_marks": []
            },
            "delivered": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=delivery,
            message="Dialogue delivered",
            metadata={"line_count": len(lines)}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate dialogue delivery."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class PhysicalActingSkill(BaseSkill):
    """Execute physical performance and movement."""
    
    def __init__(self):
        super().__init__(
            name="physical_acting",
            description="Execute physical performance including movement, stunts, and choreography",
            required_tools=["create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute physical acting."""
        action_type = context.parameters.get("action_type", "standard")
        
        physical = {
            "action_type": action_type,
            "movements": [],
            "choreography": {
                "sequence": [],
                "timing": [],
                "marks": []
            },
            "safety_notes": [],
            "executed": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=physical,
            message="Physical acting executed",
            metadata={"action_type": action_type}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate physical acting."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class CharacterStudySkill(BaseSkill):
    """Study and analyze character for portrayal."""
    
    def __init__(self):
        super().__init__(
            name="character_study",
            description="Study and analyze character background, motivations, and relationships",
            required_tools=["get_character_info"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute character study."""
        character_id = context.parameters.get("character_id")
        
        if character_id:
            character_info = context.execute_tool("get_character_info", character_id=character_id)
        else:
            character_info = {}
        
        study = {
            "character": character_info,
            "analysis": {
                "wants": "What the character consciously desires",
                "needs": "What the character truly needs",
                "fear": "What the character fears most",
                "secret": "What the character hides"
            },
            "backstory_notes": [],
            "relationship_map": {},
            "transformation_arc": {
                "beginning": "starting state",
                "end": "transformed state"
            }
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=study,
            message="Character study completed",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate character study."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class SceneRehearsalSkill(BaseSkill):
    """Rehearse scenes before filming."""
    
    def __init__(self):
        super().__init__(
            name="scene_rehearsal",
            description="Rehearse scenes to perfect performance before final takes",
            required_tools=["list_characters"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute scene rehearsal."""
        scene = context.parameters.get("scene", {})
        characters = context.execute_tool("list_characters")
        
        rehearsal = {
            "scene": scene,
            "characters": characters,
            "rehearsal_notes": [
                "Blocking reviewed",
                "Lines practiced",
                "Timing adjusted"
            ],
            "adjustments_made": [],
            "ready_for_take": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=rehearsal,
            message="Scene rehearsal completed",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate scene rehearsal."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
