"""Supervisor Agent - Continuity and script supervision (Script Supervisor role)."""

from typing import Any
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.supervisor import (
    ContinuityTrackingSkill,
    ScriptSupervisionSkill,
    ShotLoggingSkill,
    TimingNotesSkill,
    CoverageTrackingSkill,
    ContinuityReportSkill,
    MatchingSkill,
)


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
