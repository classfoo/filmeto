import shutil
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Any

from agent.crew.crew_member import CrewMember


class CrewService:
    """
    Singleton service to manage crew members per project.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CrewService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._project_agents: Dict[str, Dict[str, CrewMember]] = {}
        self._initialized = True

    def initialize_project_crew_members(self, project: Any) -> List[str]:
        """
        Ensure the project's crew directory exists and seeded from system defaults.
        """
        project_path = _resolve_project_path(project)
        if not project_path:
            return []

        crew_members_dir = Path(project_path) / "agent" / "crew_members"
        crew_members_dir.mkdir(parents=True, exist_ok=True)

        system_dir = Path(__file__).parent / "system"
        if not system_dir.exists():
            return []

        initialized_files = []
        for system_file in system_dir.glob("*.md"):
            target_file = crew_members_dir / system_file.name
            if target_file.exists():
                continue
            shutil.copy2(system_file, target_file)
            initialized_files.append(str(target_file))
        return initialized_files

    def load_project_crew_members_with_backward_compatibility(self, project: Any, refresh: bool = False) -> Dict[str, CrewMember]:
        """
        Load crew members for a project with backward compatibility for old sub_agents directory.
        """
        project_key = _resolve_project_key(project)
        if not project_key:
            return {}

        if not refresh and project_key in self._project_agents:
            return self._project_agents[project_key]

        project_path = _resolve_project_path(project)
        if not project_path:
            return {}

        # First, initialize new crew_members directory
        self.initialize_project_crew_members(project)

        # Check for new crew_members directory first
        crew_members_dir = Path(project_path) / "agent" / "crew_members"
        if not crew_members_dir.exists():
            self._project_agents[project_key] = {}
            return {}

        # Also check for old sub_agents directory for backward compatibility
        old_sub_agents_dir = Path(project_path) / "agent" / "sub_agents"

        workspace = getattr(project, "workspace", None)
        agents: Dict[str, CrewMember] = {}

        # Load from new directory first
        for config_path in crew_members_dir.glob("*.md"):
            agent = CrewMember(
                config_path=str(config_path),
                workspace=workspace,
                project=project,
            )
            agents[agent.config.name] = agent

        # Then load from old directory if it exists, but don't overwrite new ones
        if old_sub_agents_dir.exists():
            for config_path in old_sub_agents_dir.glob("*.md"):
                agent_name = config_path.stem  # Get the filename without extension
                if agent_name not in agents:  # Only add if not already loaded from new directory
                    agent = CrewMember(
                        config_path=str(config_path),
                        workspace=workspace,
                        project=project,
                    )
                    agents[agent.config.name] = agent

        self._project_agents[project_key] = agents
        return agents

    def load_project_crew_members(self, project: Any, refresh: bool = False) -> Dict[str, CrewMember]:
        """
        Load crew members for a project, initializing defaults if needed.
        Includes backward compatibility for old sub_agents directory.
        """
        project_key = _resolve_project_key(project)
        if not project_key:
            return {}

        if not refresh and project_key in self._project_agents:
            return self._project_agents[project_key]

        project_path = _resolve_project_path(project)
        if not project_path:
            return {}

        self.initialize_project_crew_members(project)

        # Check for new crew_members directory
        crew_members_dir = Path(project_path) / "agent" / "crew_members"
        # Also check for old sub_agents directory for backward compatibility
        old_sub_agents_dir = Path(project_path) / "agent" / "sub_agents"

        if not crew_members_dir.exists() and not old_sub_agents_dir.exists():
            self._project_agents[project_key] = {}
            return {}

        workspace = getattr(project, "workspace", None)
        agents: Dict[str, CrewMember] = {}

        # Load from new directory first if it exists
        if crew_members_dir.exists():
            for config_path in crew_members_dir.glob("*.md"):
                agent = CrewMember(
                    config_path=str(config_path),
                    workspace=workspace,
                    project=project,
                )
                agents[agent.config.name] = agent

        # Then load from old directory if it exists, but don't overwrite new ones
        if old_sub_agents_dir.exists():
            for config_path in old_sub_agents_dir.glob("*.md"):
                agent_name = config_path.stem  # Get the filename without extension
                if agent_name not in agents:  # Only add if not already loaded from new directory
                    agent = CrewMember(
                        config_path=str(config_path),
                        workspace=workspace,
                        project=project,
                    )
                    agents[agent.config.name] = agent

        self._project_agents[project_key] = agents
        return agents

    def get_crew_member(self, project: Any, name: str) -> Optional[CrewMember]:
        agents = self.load_project_crew_members(project)
        return agents.get(name)

    def list_crew_members(self, project: Any) -> List[CrewMember]:
        return list(self.load_project_crew_members(project).values())

    def refresh_project_crew_members(self, project: Any) -> Dict[str, CrewMember]:
        return self.load_project_crew_members(project, refresh=True)

    def get_project_crew_member_metadata(self, project: Any) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata for all crew members in a project, including color configuration.
        Includes backward compatibility for old sub_agents directory.

        Args:
            project: The project to get crew member metadata for

        Returns:
            Dictionary mapping agent names to their metadata (including color)
        """
        agents = self.load_project_crew_members(project)
        metadata = {}

        for name, agent in agents.items():
            metadata[name] = {
                'name': agent.config.name,
                'description': agent.config.description,
                'color': agent.config.color,  # This is the color we added earlier
                'icon': agent.config.icon,   # This is the icon we added
                'soul': agent.config.soul,
                'skills': agent.config.skills,
                'model': agent.config.model,
                'temperature': agent.config.temperature,
                'max_steps': agent.config.max_steps,
                'config_path': agent.config.config_path,
            }

        return metadata


def _resolve_project_path(project: Any) -> Optional[str]:
    if project is None:
        return None
    if hasattr(project, "project_path"):
        return project.project_path
    if isinstance(project, str):
        return project
    return None


def _resolve_project_key(project: Any) -> Optional[str]:
    if project is None:
        return None
    if hasattr(project, "project_path"):
        return project.project_path
    if hasattr(project, "project_name"):
        return project.project_name
    if isinstance(project, str):
        return project
    return None
