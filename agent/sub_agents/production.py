"""Production Agent - Project planning and coordination (Producer role)."""

from typing import Any
from agent.sub_agents.base import FilmProductionAgent
from agent.skills.production import (
    ProjectPlanningSkill,
    ResourceAllocationSkill,
    TimelineCoordinationSkill,
    BudgetManagementSkill,
    DepartmentCoordinationSkill,
    ProductionSchedulingSkill,
    QualityOversightSkill,
)


class ProductionAgent(FilmProductionAgent):
    """
    Production Agent (Producer) - Oversees the entire film production project.
    
    As the producer, this agent:
    - Plans the overall project structure and timeline
    - Allocates resources across departments
    - Manages budget and scheduling
    - Coordinates between all departments
    - Ensures project stays on track
    """
    
    def __init__(self, llm: Any = None):
        """Initialize Production Agent."""
        skills = [
            ProjectPlanningSkill(),
            ResourceAllocationSkill(),
            TimelineCoordinationSkill(),
            BudgetManagementSkill(),
            DepartmentCoordinationSkill(),
            ProductionSchedulingSkill(),
            QualityOversightSkill(),
        ]
        super().__init__(
            name="Production",
            role="Producer",
            description="Oversees the entire project, secures resources, manages budget and timeline, coordinates all departments",
            skills=skills,
            llm=llm,
            specialty="management",
            collaborates_with=["Director", "Editor", "Screenwriter"]
        )
