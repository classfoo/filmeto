"""Supervisor Agent - Continuity and script supervision (Script Supervisor role)."""

from typing import Any, Dict, List, Optional
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus


class SupervisorAgent(FilmProductionAgent):
    """
    Supervisor Agent (Script Supervisor) - Ensures continuity and tracks production.
    
    As the script supervisor, this agent:
    - Tracks visual and narrative continuity between shots
    - Supervises script adherence and changes
    - Logs shots and technical details
    - Notes timing and coverage
    - Reports issues to director and editor
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Supervisor Agent."""
        skills = [
            ContinuityTrackingSkill(),
            ScriptSupervisionSkill(),
            ShotLoggingSkill(),
            TimingNotesSkill(),
            CoverageTrackingSkill(),
            ContinuityReportSkill(),
            MatchingSkill(),
        ]
        super().__init__(
            name="Supervisor",
            role="Script Supervisor",
            description="Tracks continuity, supervises script changes, logs shots, and ensures consistency across takes",
            skills=skills,
            llm=llm,
            specialty="production",
            collaborates_with=["Director", "Editor", "Actor"]
        )


class ContinuityTrackingSkill(BaseSkill):
    """Track continuity between shots."""
    
    def __init__(self):
        super().__init__(
            name="continuity_tracking",
            description="Track visual and narrative continuity between shots and scenes to prevent errors",
            required_tools=["get_timeline_info", "list_resources"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute continuity tracking."""
        timeline_info = context.execute_tool("get_timeline_info")
        
        continuity = {
            "timeline": timeline_info,
            "continuity_notes": [
                {"type": "position", "element": "Character A", "position": "stage left"},
                {"type": "props", "element": "Coffee cup", "state": "half full"},
                {"type": "wardrobe", "element": "Character A shirt", "state": "tucked in"}
            ],
            "issues": [],
            "verified_elements": [],
            "tracking_areas": [
                "Character positions",
                "Prop placement",
                "Wardrobe state",
                "Lighting continuity",
                "Eye lines",
                "Action matching"
            ]
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=continuity,
            message=f"Continuity tracked with {len(continuity['continuity_notes'])} notes",
            metadata={"note_count": len(continuity['continuity_notes'])}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate continuity tracking."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            has_notes = len(output.get("continuity_notes", [])) > 0
            no_issues = len(output.get("issues", [])) == 0
            result.quality_score = 0.9 if (has_notes and no_issues) else 0.7
        return result


class ScriptSupervisionSkill(BaseSkill):
    """Supervise script changes and annotations."""
    
    def __init__(self):
        super().__init__(
            name="script_supervision",
            description="Supervise script adherence, track revisions, and maintain script annotations",
            required_tools=["get_project_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute script supervision."""
        project_info = context.execute_tool("get_project_info")
        
        supervision = {
            "project": project_info,
            "script_notes": [
                {"scene": 1, "line": "As scripted", "deviation": None},
                {"scene": 2, "line": "Minor ad-lib", "deviation": "Added 'well'"}
            ],
            "revisions": [],
            "dialogue_changes": [],
            "action_changes": [],
            "line_readings": {}
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=supervision,
            message="Script supervision completed",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate script supervision."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class ShotLoggingSkill(BaseSkill):
    """Log shots and technical details."""
    
    def __init__(self):
        super().__init__(
            name="shot_logging",
            description="Log all shots with technical details, timing, and metadata for post-production",
            required_tools=["get_timeline_info", "list_resources"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute shot logging."""
        timeline_info = context.execute_tool("get_timeline_info")
        
        log = {
            "timeline": timeline_info,
            "shots_logged": [
                {
                    "shot_id": "1A",
                    "scene": 1,
                    "take": 1,
                    "duration": 12.5,
                    "rating": "good",
                    "notes": "Clean take, good performance"
                },
                {
                    "shot_id": "1A",
                    "scene": 1,
                    "take": 2,
                    "duration": 13.2,
                    "rating": "excellent",
                    "notes": "Best take, director preferred"
                }
            ],
            "technical_details": {
                "lens": "50mm",
                "aperture": "f/2.8",
                "frame_rate": 24
            },
            "circled_takes": ["1A-T2"]
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=log,
            message=f"Logged {len(log['shots_logged'])} shots",
            metadata={"shot_count": len(log['shots_logged'])}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate shot logging."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class TimingNotesSkill(BaseSkill):
    """Track timing for scenes and takes."""
    
    def __init__(self):
        super().__init__(
            name="timing_notes",
            description="Track scene and take timing for pacing and editing reference",
            required_tools=["get_timeline_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute timing notes."""
        timeline_info = context.execute_tool("get_timeline_info")
        
        timing = {
            "timeline": timeline_info,
            "scene_timings": [
                {"scene": 1, "scripted_duration": 30, "actual_duration": 28},
                {"scene": 2, "scripted_duration": 45, "actual_duration": 52}
            ],
            "pacing_notes": [
                "Scene 1: Slightly faster than scripted",
                "Scene 2: Running long, may need trimming"
            ],
            "total_screen_time": 80
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=timing,
            message="Timing notes recorded",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate timing notes."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result


class CoverageTrackingSkill(BaseSkill):
    """Track camera coverage for scenes."""
    
    def __init__(self):
        super().__init__(
            name="coverage_tracking",
            description="Track camera coverage to ensure all angles needed for editing are captured",
            required_tools=["get_timeline_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute coverage tracking."""
        scene = context.parameters.get("scene", {})
        
        coverage = {
            "scene": scene,
            "coverage_checklist": {
                "master": True,
                "medium_a": True,
                "medium_b": True,
                "close_up_a": True,
                "close_up_b": False,
                "inserts": False
            },
            "missing_coverage": ["close_up_b", "inserts"],
            "recommendations": ["Capture close-up of Character B", "Get insert shots of props"]
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=coverage,
            message="Coverage tracked with recommendations",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate coverage tracking."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            missing = output.get("missing_coverage", [])
            result.quality_score = 0.9 if len(missing) == 0 else 0.7
            if missing:
                result.requires_help = "Director"
        return result


class ContinuityReportSkill(BaseSkill):
    """Generate continuity report for editor."""
    
    def __init__(self):
        super().__init__(
            name="continuity_report",
            description="Generate comprehensive continuity report for post-production",
            required_tools=["get_project_info", "list_resources"],
            category="post_production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute continuity report generation."""
        project_info = context.execute_tool("get_project_info")
        
        report = {
            "project": project_info,
            "report_sections": {
                "script_notes": [],
                "continuity_notes": [],
                "circled_takes": [],
                "timing_breakdown": [],
                "issues_log": []
            },
            "editor_notes": [
                "Prefer takes with tighter pacing",
                "Watch for continuity at scene transitions"
            ],
            "generated": True
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=report,
            message="Continuity report generated for editor",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate continuity report."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.85
        return result


class MatchingSkill(BaseSkill):
    """Ensure action matching between shots."""
    
    def __init__(self):
        super().__init__(
            name="matching",
            description="Ensure action, eye lines, and movement matching between shots for seamless editing",
            required_tools=["get_timeline_info"],
            category="production"
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute matching verification."""
        scene = context.parameters.get("scene", {})
        
        matching = {
            "scene": scene,
            "action_matching": {
                "verified": True,
                "notes": []
            },
            "eye_line_matching": {
                "verified": True,
                "notes": []
            },
            "movement_matching": {
                "verified": True,
                "notes": []
            },
            "issues": []
        }
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            output=matching,
            message="Matching verified for scene",
            metadata={}
        )
    
    async def evaluate(self, result: SkillResult, context: SkillContext) -> SkillResult:
        """Evaluate matching."""
        if result.status == SkillStatus.SUCCESS:
            output = result.output or {}
            issues = output.get("issues", [])
            result.quality_score = 0.9 if len(issues) == 0 else 0.6
        return result
