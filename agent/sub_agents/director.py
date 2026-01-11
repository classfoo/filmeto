"""Director Agent - Creative vision and scene direction."""

from typing import Any, Dict, List, Optional
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class DirectorAgent(FilmProductionAgent):
    """
    Director Agent - Develops creative vision and directs scenes.
    
    As the director, this agent:
    - Creates the overall visual and artistic vision
    - Develops storyboards from scripts
    - Plans shot compositions and camera angles
    - Directs scene execution
    - Works with actors on performance
    - Collaborates with all departments to realize the vision
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Director Agent."""
        skills = [
            StoryboardSkill(),
            SceneCompositionSkill(),
            SceneDirectionSkill(),
            ShotPlanningSkill(),
            VisualStyleSkill(),
            CameraWorkSkill(),
            ActorDirectionSkill(),
            SceneBlockingSkill(),
        ]
        super().__init__(
            name="Director",
            role="Director",
            description="Develops creative vision, creates storyboards, plans shots, and directs scenes",
            skills=skills,
            llm=llm,
            specialty="production",
            collaborates_with=["Screenwriter", "Actor", "Editor", "MakeupArtist"]
        )


class StoryboardSkill(BaseSkill):
    """Create storyboard for scenes."""
    
    def __init__(self):
        super().__init__(
            name="storyboard",
            description="Create visual storyboard with shot compositions, camera angles, and scene flow",
            required_tools=["create_task", "list_resources"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute storyboard creation."""
        script = context.parameters.get("script", {})
        scene_description = context.parameters.get("scene_description", "")
        
        # Get previous script data if available
        script_data = context.get_previous_result("Screenwriter", "script_detail")
        if script_data:
            script = script_data
        
        storyboard = {
            "based_on_script": script,
            "panels": [
                {
                    "panel_number": 1,
                    "description": "Establishing shot",
                    "camera_angle": "wide",
                    "duration": 3.0
                },
                {
                    "panel_number": 2,
                    "description": "Character introduction",
                    "camera_angle": "medium",
                    "duration": 5.0
                },
                {
                    "panel_number": 3,
                    "description": "Action sequence",
                    "camera_angle": "close-up",
                    "duration": 4.0
                }
            ],
            "visual_notes": [],
            "camera_movements": ["pan", "zoom", "track"],
            "scene_description": scene_description
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=storyboard,
            message=f"Storyboard created with {len(storyboard['panels'])} panels",
            metadata={"panel_count": len(storyboard['panels'])}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate storyboard quality."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            panel_count = len(output.get("panels", []))
            result.quality_score = 0.9 if panel_count >= 3 else 0.7
        return result


class SceneCompositionSkill(BaseSkill):
    """Plan scene composition and visual layout."""
    
    def __init__(self):
        super().__init__(
            name="scene_composition",
            description="Plan scene composition, framing, camera angles, lighting, and visual elements",
            required_tools=["create_task", "list_resources"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute scene composition planning."""
        scene = context.parameters.get("scene", {})
        mood = context.parameters.get("mood", "neutral")
        
        composition = {
            "scene": scene,
            "framing": {
                "type": "rule_of_thirds",
                "focus_point": "center",
                "depth_of_field": "shallow"
            },
            "camera_angles": [
                {"name": "establishing", "type": "wide", "height": "eye_level"},
                {"name": "dialogue", "type": "medium", "height": "eye_level"},
                {"name": "reaction", "type": "close_up", "height": "eye_level"}
            ],
            "lighting": {
                "type": "three_point",
                "mood": mood,
                "key_light_position": "45_degrees"
            },
            "visual_elements": {
                "foreground": [],
                "midground": ["characters"],
                "background": ["setting"]
            },
            "color_palette": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=composition,
            message="Scene composition planned with framing, lighting, and camera angles",
            metadata={"mood": mood}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate scene composition."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class SceneDirectionSkill(BaseSkill):
    """Direct scene execution and filming."""
    
    def __init__(self):
        super().__init__(
            name="scene_direction",
            description="Direct scene execution, coordinate with actors, and oversee filming process",
            required_tools=["create_task", "list_characters"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute scene direction."""
        scene = context.parameters.get("scene", {})
        characters = context.execute_tool("list_characters")
        
        direction = {
            "scene": scene,
            "characters": characters,
            "direction_notes": [
                "Establish setting with wide shot",
                "Focus on character emotions in close-ups",
                "Maintain consistent pacing"
            ],
            "actor_directions": [],
            "camera_directions": [],
            "blocking": {
                "positions": [],
                "movements": []
            },
            "takes_planned": 3
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=direction,
            message="Scene direction prepared",
            metadata={"takes_planned": 3}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate scene direction."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class ShotPlanningSkill(BaseSkill):
    """Plan individual shots and camera setups."""
    
    def __init__(self):
        super().__init__(
            name="shot_planning",
            description="Plan individual shots, camera movements, and technical setups",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute shot planning."""
        scene = context.parameters.get("scene", {})
        
        shots = {
            "scene": scene,
            "shot_list": [
                {"shot_id": 1, "type": "establishing", "duration": 3.0, "camera": "static"},
                {"shot_id": 2, "type": "medium", "duration": 5.0, "camera": "slight_push"},
                {"shot_id": 3, "type": "close_up", "duration": 2.0, "camera": "static"},
                {"shot_id": 4, "type": "reaction", "duration": 2.0, "camera": "handheld"}
            ],
            "camera_setups": [
                {"setup_id": 1, "position": "A", "lens": "35mm"},
                {"setup_id": 2, "position": "B", "lens": "50mm"},
                {"setup_id": 3, "position": "C", "lens": "85mm"}
            ],
            "coverage_plan": "standard"
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=shots,
            message=f"Planned {len(shots['shot_list'])} shots with {len(shots['camera_setups'])} camera setups",
            metadata={"shot_count": len(shots['shot_list'])}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate shot planning."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            shot_count = len(output.get("shot_list", []))
            result.quality_score = 0.85 if shot_count >= 3 else 0.7
        return result


class VisualStyleSkill(BaseSkill):
    """Define visual style for the project."""
    
    def __init__(self):
        super().__init__(
            name="visual_style",
            description="Define the overall visual style, color palette, and aesthetic direction",
            required_tools=["list_resources"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute visual style definition."""
        genre = context.parameters.get("genre", "drama")
        mood = context.parameters.get("mood", "neutral")
        
        style = {
            "genre": genre,
            "mood": mood,
            "color_palette": {
                "primary": "#1a1a2e",
                "secondary": "#16213e",
                "accent": "#e94560"
            },
            "lighting_style": "high_contrast" if genre == "thriller" else "natural",
            "camera_style": "handheld" if mood == "tense" else "steady",
            "aspect_ratio": "2.39:1",
            "visual_references": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=style,
            message=f"Visual style defined for {genre} with {mood} mood",
            metadata={"genre": genre, "mood": mood}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate visual style."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class CameraWorkSkill(BaseSkill):
    """Plan camera work and movements."""
    
    def __init__(self):
        super().__init__(
            name="camera_work",
            description="Plan detailed camera movements, angles, and technical specifications",
            required_tools=["create_task"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute camera work planning."""
        scene = context.parameters.get("scene", {})
        
        camera_work = {
            "scene": scene,
            "movements": [
                {"type": "dolly_in", "start": 0.0, "end": 3.0, "speed": "slow"},
                {"type": "pan", "start": 3.0, "end": 5.0, "direction": "left"},
                {"type": "static", "start": 5.0, "end": 10.0}
            ],
            "lens_choices": {
                "wide": "24mm",
                "medium": "50mm",
                "close": "85mm"
            },
            "exposure_settings": {
                "iso": 400,
                "aperture": "f/2.8",
                "shutter": "1/50"
            }
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=camera_work,
            message="Camera work planned with movements and technical specs",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate camera work."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class ActorDirectionSkill(BaseSkill):
    """Direct actor performances."""
    
    def __init__(self):
        super().__init__(
            name="actor_direction",
            description="Provide direction and guidance to actors for their performances",
            required_tools=["list_characters", "get_character_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute actor direction."""
        characters = context.execute_tool("list_characters")
        scene = context.parameters.get("scene", {})
        
        direction = {
            "scene": scene,
            "characters": characters,
            "performance_notes": {
                "emotion": context.parameters.get("emotion", "neutral"),
                "intensity": context.parameters.get("intensity", "medium"),
                "pacing": context.parameters.get("pacing", "natural")
            },
            "blocking_instructions": [],
            "dialogue_notes": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=direction,
            message="Actor direction prepared",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate actor direction."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class SceneBlockingSkill(BaseSkill):
    """Plan scene blocking and movement."""
    
    def __init__(self):
        super().__init__(
            name="scene_blocking",
            description="Plan actor positions, movements, and spatial relationships in scenes",
            required_tools=["list_characters"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute scene blocking."""
        characters = context.execute_tool("list_characters")
        scene = context.parameters.get("scene", {})
        
        blocking = {
            "scene": scene,
            "characters": characters,
            "positions": [
                {"character": "char_1", "position": "stage_left", "mark": "A"},
                {"character": "char_2", "position": "stage_right", "mark": "B"}
            ],
            "movements": [
                {"character": "char_1", "from": "A", "to": "C", "timing": "line_3"}
            ],
            "spatial_relationships": {
                "distance": "conversational",
                "eye_lines": "matched"
            }
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=blocking,
            message="Scene blocking planned",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate scene blocking."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
