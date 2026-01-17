import shutil
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Any

from agent.sub_agent.sub_agent import SubAgent


class SubAgentService:
    """
    Singleton service to manage sub-agents per project.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SubAgentService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._project_agents: Dict[str, Dict[str, SubAgent]] = {}
        self._initialized = True

    def initialize_project_sub_agents(self, project: Any) -> List[str]:
        """
        Ensure the project's sub_agent directory exists and seeded from system defaults.
        """
        project_path = _resolve_project_path(project)
        if not project_path:
            return []

        sub_agents_dir = Path(project_path) / "agent" / "sub_agents"
        sub_agents_dir.mkdir(parents=True, exist_ok=True)

        system_dir = Path(__file__).parent / "system"
        if not system_dir.exists():
            return []

        initialized_files = []
        for system_file in system_dir.glob("*.md"):
            target_file = sub_agents_dir / system_file.name
            if target_file.exists():
                continue
            shutil.copy2(system_file, target_file)
            initialized_files.append(str(target_file))
        return initialized_files

    def load_project_sub_agents(self, project: Any, refresh: bool = False) -> Dict[str, SubAgent]:
        """
        Load sub-agents for a project, initializing defaults if needed.
        """
        project_key = _resolve_project_key(project)
        if not project_key:
            return {}

        if not refresh and project_key in self._project_agents:
            return self._project_agents[project_key]

        project_path = _resolve_project_path(project)
        if not project_path:
            return {}

        self.initialize_project_sub_agents(project)

        sub_agents_dir = Path(project_path) / "agent" / "sub_agents"
        if not sub_agents_dir.exists():
            self._project_agents[project_key] = {}
            return {}

        workspace = getattr(project, "workspace", None)
        agents: Dict[str, SubAgent] = {}
        for config_path in sub_agents_dir.glob("*.md"):
            agent = SubAgent(
                config_path=str(config_path),
                workspace=workspace,
                project=project,
            )
            agents[agent.config.name] = agent

        self._project_agents[project_key] = agents
        return agents

    def get_sub_agent(self, project: Any, name: str) -> Optional[SubAgent]:
        agents = self.load_project_sub_agents(project)
        return agents.get(name)

    def list_sub_agents(self, project: Any) -> List[SubAgent]:
        return list(self.load_project_sub_agents(project).values())

    def refresh_project_sub_agents(self, project: Any) -> Dict[str, SubAgent]:
        return self.load_project_sub_agents(project, refresh=True)

    def get_project_sub_agent_metadata(self, project: Any) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata for all sub-agents in a project, including color configuration.

        Args:
            project: The project to get sub-agent metadata for

        Returns:
            Dictionary mapping agent names to their metadata (including color)
        """
        agents = self.load_project_sub_agents(project)
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
