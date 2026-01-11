"""Screenwriter Agent - Script writing and story development."""

from typing import Any, Dict, List, Optional
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class ScreenwriterAgent(FilmProductionAgent):
    """
    Screenwriter Agent - Writes scripts and develops stories.
    
    As the screenwriter, this agent:
    - Creates script outlines and story structures
    - Writes detailed scripts with scenes and dialogue
    - Develops character arcs and relationships
    - Creates dialogue for all characters
    - Works with director on script revisions
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Screenwriter Agent."""
        skills = [
            ScriptOutlineSkill(),
            ScriptDetailSkill(),
            DialogueWritingSkill(),
            StoryDevelopmentSkill(),
            CharacterArcSkill(),
            SceneWritingSkill(),
            ScriptRevisionSkill(),
            TreatmentWritingSkill(),
        ]
        super().__init__(
            name="Screenwriter",
            role="Screenwriter",
            description="Creates scripts, develops storylines, writes dialogue, and structures narratives",
            skills=skills,
            llm=llm,
            specialty="pre_production",
            collaborates_with=["Director", "Production", "Actor"]
        )


class ScriptOutlineSkill(BaseSkill):
    """Create script outline/structure."""
    
    def __init__(self):
        super().__init__(
            name="script_outline",
            description="Write comprehensive script outline with acts, scenes, and story structure",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute script outline creation."""
        topic = context.parameters.get("topic", "")
        genre = context.parameters.get("genre", "drama")
        duration = context.parameters.get("duration", 60)  # seconds
        
        outline = {
            "title": context.parameters.get("title", "Untitled"),
            "genre": genre,
            "target_duration": duration,
            "logline": f"A story about {topic}" if topic else "A compelling story",
            "structure": {
                "act_1": {
                    "name": "Setup",
                    "percentage": 25,
                    "beats": ["Opening Image", "Theme Stated", "Setup", "Catalyst", "Debate"]
                },
                "act_2a": {
                    "name": "Rising Action",
                    "percentage": 25,
                    "beats": ["Break into Two", "B Story", "Fun and Games", "Midpoint"]
                },
                "act_2b": {
                    "name": "Complications",
                    "percentage": 25,
                    "beats": ["Bad Guys Close In", "All Is Lost", "Dark Night of the Soul"]
                },
                "act_3": {
                    "name": "Resolution",
                    "percentage": 25,
                    "beats": ["Break into Three", "Finale", "Final Image"]
                }
            },
            "scenes_outline": [],
            "character_introductions": [],
            "key_moments": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=outline,
            message=f"Script outline created for {genre} film",
            metadata={"genre": genre, "structure": "four_act"}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate script outline quality."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            has_structure = "structure" in output
            has_logline = bool(output.get("logline"))
            result.quality_score = 0.9 if (has_structure and has_logline) else 0.7
        return result


class ScriptDetailSkill(BaseSkill):
    """Develop detailed script with scenes and actions."""
    
    def __init__(self):
        super().__init__(
            name="script_detail",
            description="Develop detailed script with scene descriptions, actions, dialogue, and transitions",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute script detail development."""
        outline = context.parameters.get("outline", {})
        
        # Get outline from shared state if not provided
        if not outline:
            outline = context.get_previous_result("Screenwriter", "script_outline") or {}
        
        script = {
            "based_on_outline": outline,
            "title": outline.get("title", "Untitled"),
            "scenes": [
                {
                    "scene_number": 1,
                    "heading": "INT. LOCATION - DAY",
                    "description": "Scene description with setting and atmosphere",
                    "action": ["Character enters", "Dialogue exchange", "Exit"],
                    "characters": [],
                    "dialogue": [],
                    "duration_estimate": 15
                },
                {
                    "scene_number": 2,
                    "heading": "EXT. LOCATION - DAY",
                    "description": "Exterior scene description",
                    "action": [],
                    "characters": [],
                    "dialogue": [],
                    "duration_estimate": 20
                }
            ],
            "transitions": ["CUT TO:", "DISSOLVE TO:", "FADE TO:"],
            "detailed": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=script,
            message=f"Detailed script developed with {len(script['scenes'])} scenes",
            metadata={"scene_count": len(script['scenes'])}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate script detail quality."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            scene_count = len(output.get("scenes", []))
            result.quality_score = 0.85 if scene_count >= 2 else 0.7
        return result


class DialogueWritingSkill(BaseSkill):
    """Write dialogue for scenes."""
    
    def __init__(self):
        super().__init__(
            name="dialogue_writing",
            description="Write natural, character-appropriate dialogue for scenes",
            required_tools=["list_characters", "create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute dialogue writing."""
        characters = context.execute_tool("list_characters")
        scene = context.parameters.get("scene", {})
        tone = context.parameters.get("tone", "natural")
        
        dialogue = {
            "scene": scene,
            "characters": characters,
            "tone": tone,
            "dialogue_lines": [
                {
                    "character": "Character A",
                    "line": "Sample dialogue line",
                    "parenthetical": "(thoughtfully)",
                    "subtext": "Hidden meaning"
                },
                {
                    "character": "Character B",
                    "line": "Response line",
                    "parenthetical": None,
                    "subtext": None
                }
            ],
            "dialogue_notes": {
                "rhythm": "conversational",
                "conflict_level": "medium"
            }
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=dialogue,
            message=f"Dialogue written with {len(dialogue['dialogue_lines'])} lines",
            metadata={"line_count": len(dialogue['dialogue_lines'])}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate dialogue quality."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            line_count = len(output.get("dialogue_lines", []))
            result.quality_score = 0.85 if line_count >= 2 else 0.7
        return result


class StoryDevelopmentSkill(BaseSkill):
    """Develop story concepts and narratives."""
    
    def __init__(self):
        super().__init__(
            name="story_development",
            description="Develop story concepts, themes, narrative arcs, and emotional beats",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute story development."""
        concept = context.parameters.get("concept", "")
        genre = context.parameters.get("genre", "drama")
        
        story = {
            "concept": concept,
            "genre": genre,
            "themes": [
                {"name": "Primary Theme", "description": "Main thematic element"},
                {"name": "Secondary Theme", "description": "Supporting theme"}
            ],
            "narrative_arc": {
                "type": "hero_journey",
                "stages": [
                    "Ordinary World",
                    "Call to Adventure",
                    "Refusal",
                    "Meeting the Mentor",
                    "Crossing the Threshold",
                    "Tests and Allies",
                    "Approach",
                    "Ordeal",
                    "Reward",
                    "The Road Back",
                    "Resurrection",
                    "Return"
                ]
            },
            "emotional_beats": [
                {"beat": "Hope", "position": 0.1},
                {"beat": "Tension", "position": 0.3},
                {"beat": "Despair", "position": 0.6},
                {"beat": "Triumph", "position": 0.9}
            ],
            "world_building": {}
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=story,
            message=f"Story developed with {len(story['themes'])} themes",
            metadata={"genre": genre}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate story development."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class CharacterArcSkill(BaseSkill):
    """Develop character arcs and growth."""
    
    def __init__(self):
        super().__init__(
            name="character_arc",
            description="Develop character arcs, growth, and transformation throughout the story",
            required_tools=["list_characters", "get_character_info"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute character arc development."""
        characters = context.execute_tool("list_characters")
        
        arcs = {
            "characters": characters,
            "arcs": [
                {
                    "character": "Protagonist",
                    "arc_type": "positive_change",
                    "starting_point": "Flawed/limited state",
                    "midpoint": "Confronting truth",
                    "ending_point": "Transformed/growth",
                    "key_moments": ["Inciting incident", "Dark moment", "Transformation"]
                }
            ],
            "relationships": {
                "protagonist-antagonist": "conflict",
                "protagonist-mentor": "guidance"
            }
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=arcs,
            message="Character arcs developed",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate character arc development."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class SceneWritingSkill(BaseSkill):
    """Write individual scenes in detail."""
    
    def __init__(self):
        super().__init__(
            name="scene_writing",
            description="Write detailed individual scenes with action, dialogue, and stage directions",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute scene writing."""
        scene_number = context.parameters.get("scene_number", 1)
        location = context.parameters.get("location", "INTERIOR - ROOM")
        time = context.parameters.get("time", "DAY")
        
        scene = {
            "scene_number": scene_number,
            "slug_line": f"{location} - {time}",
            "action_lines": [
                "Scene opens with establishing shot.",
                "Character enters from stage left.",
                "Tension builds as characters interact."
            ],
            "dialogue": [],
            "visual_cues": [],
            "sound_cues": [],
            "transitions": {
                "in": "CUT FROM:",
                "out": "CUT TO:"
            }
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=scene,
            message=f"Scene {scene_number} written",
            metadata={"scene_number": scene_number}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate scene writing."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class ScriptRevisionSkill(BaseSkill):
    """Revise and polish scripts."""
    
    def __init__(self):
        super().__init__(
            name="script_revision",
            description="Revise and polish scripts based on feedback and requirements",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute script revision."""
        original_script = context.parameters.get("script", {})
        feedback = context.parameters.get("feedback", [])
        
        revision = {
            "original_script": original_script,
            "feedback_addressed": feedback,
            "changes_made": [
                "Dialogue tightened",
                "Scene pacing improved",
                "Character motivations clarified"
            ],
            "revision_number": context.parameters.get("revision_number", 1),
            "revised": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=revision,
            message="Script revision completed",
            metadata={"revision_number": revision["revision_number"]}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate script revision."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class TreatmentWritingSkill(BaseSkill):
    """Write script treatment/synopsis."""
    
    def __init__(self):
        super().__init__(
            name="treatment_writing",
            description="Write script treatment or synopsis for project pitching",
            required_tools=["create_task"],
            category="pre_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute treatment writing."""
        title = context.parameters.get("title", "Untitled")
        genre = context.parameters.get("genre", "drama")
        
        treatment = {
            "title": title,
            "genre": genre,
            "logline": "",
            "synopsis": {
                "short": "One paragraph summary",
                "long": "Full treatment with story details"
            },
            "tone": "",
            "visual_style": "",
            "target_audience": ""
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=treatment,
            message="Treatment written",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate treatment writing."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
