from ..base_tool import BaseTool
from typing import Any, Dict, List
from agent.crew.crew_service import CrewService
from agent.crew.crew_member import CrewMember


class GetProjectCrewMembersTool(BaseTool):
    """
    Tool to get the list of crew members in a project.
    """

    def __init__(self):
        super().__init__(
            name="get_project_crew_members",
            description="Get the list of crew members in the current project"
        )

    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """
        Execute the crew member retrieval using CrewService.

        Args:
            parameters: Additional parameters (currently unused)
            context: Context containing project/workspace info

        Returns:
            List of crew members with their details
        """
        # Extract project information from context
        project = context.get('project') if context else None
        workspace = context.get('workspace') if context else None

        if not project:
            return []

        # Initialize CrewService
        crew_service = CrewService()

        # Get crew members for the project using CrewService
        crew_members_dict = crew_service.get_project_crew_members(project)

        # Convert CrewMember objects to dictionaries
        crew_members_list = []
        for name, crew_member in crew_members_dict.items():
            member_info = {
                "id": name,  # Using name as ID since CrewMember doesn't have a separate ID
                "name": crew_member.config.name,
                "role": getattr(crew_member.config, 'crew_title', 'member'),  # Using crew_title as role
                "description": crew_member.config.description,
                "soul": crew_member.config.soul or "",  # The associated soul name
                "skills": crew_member.config.skills,  # List of skills
                "model": crew_member.config.model,  # Model used by the crew member
                "temperature": crew_member.config.temperature,  # Temperature setting
                "max_steps": crew_member.config.max_steps,  # Max steps for the crew member
                "color": crew_member.config.color,  # Color for UI representation
                "icon": crew_member.config.icon  # Icon for UI representation
            }
            crew_members_list.append(member_info)

        return crew_members_list