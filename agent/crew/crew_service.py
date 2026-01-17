import shutil
import random
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Any

from agent.crew.crew_member import CrewMember
from agent.crew.crew_title import sort_crew_members_by_title_importance
from agent.soul.soul_service import SoulService


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
        Creates default crew members based on crew titles with randomly assigned matching souls.
        """
        import yaml

        project_path = _resolve_project_path(project)
        if not project_path:
            return []

        crew_members_dir = Path(project_path) / "agent" / "crew_members"
        crew_members_dir.mkdir(parents=True, exist_ok=True)

        # Get all available souls
        soul_service = SoulService()
        all_souls = soul_service.get_all_souls()

        # Get all crew titles from system directory
        system_dir = Path(__file__).parent / "system"
        if not system_dir.exists():
            return []

        initialized_files = []

        # Create crew members based on crew titles with randomly assigned matching souls
        for system_file in system_dir.glob("*.md"):
            # Extract crew title from filename (without extension)
            crew_title = system_file.stem

            # Read the original crew member file to check if it already specifies a soul
            with open(system_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the frontmatter to check for existing soul
            original_soul = None
            original_name = crew_title  # Default to crew_title if no name found in frontmatter

            if content.startswith('---'):
                end_marker_idx = content.find('---', 3)
                if end_marker_idx != -1:
                    yaml_str = content[3:end_marker_idx].strip()

                    try:
                        metadata = yaml.safe_load(yaml_str)
                        if metadata:
                            original_soul = metadata.get('soul')
                            original_name = metadata.get('name', crew_title)
                    except yaml.YAMLError:
                        pass  # If YAML parsing fails, continue with defaults

            # If the crew member already has a specific soul assigned, use it
            if original_soul:
                # First try exact match
                selected_soul = next((soul for soul in all_souls if soul.name == original_soul), None)

                # If no exact match, try to find by comparing the soul name in different formats
                if not selected_soul:
                    # Normalize the original_soul name to compare with soul names
                    normalized_original = original_soul.replace('_', ' ').replace('-', ' ').strip().lower()
                    selected_soul = next((soul for soul in all_souls
                                         if soul.name.lower() == normalized_original or
                                            soul.name.replace(' ', '_').replace('-', '_').lower() == original_soul.lower()), None)

                # If still no match, fall back to matching by crew title
                if not selected_soul:
                    matching_souls = [soul for soul in all_souls if
                                      soul.metadata and soul.metadata.get('crew_title') == crew_title]

                    if matching_souls:
                        selected_soul = random.choice(matching_souls)
            else:
                # Find souls that match the crew title
                matching_souls = [soul for soul in all_souls if
                                  soul.metadata and soul.metadata.get('crew_title') == crew_title]

                # If no matching souls found, use any soul with the crew title in its name
                if not matching_souls:
                    matching_souls = [soul for soul in all_souls if
                                      crew_title in soul.name.lower() or
                                      (soul.metadata and crew_title in soul.metadata.get('name', '').lower())]

                # If still no matching souls, use all souls
                if not matching_souls:
                    matching_souls = all_souls

                # Randomly select a soul from matching souls
                selected_soul = random.choice(matching_souls) if matching_souls else None

            # Create new content with the selected soul
            if selected_soul:
                # Update the soul field in the metadata
                if content.startswith('---'):
                    end_marker_idx = content.find('---', 3)
                    if end_marker_idx != -1:
                        yaml_str = content[3:end_marker_idx].strip()

                        try:
                            metadata = yaml.safe_load(yaml_str)
                            if metadata is None:
                                metadata = {}

                            # Update the soul in metadata
                            metadata['soul'] = selected_soul.name

                            # Use the name from the soul's metadata if available, otherwise keep original name
                            if selected_soul.metadata and 'name' in selected_soul.metadata:
                                metadata['name'] = selected_soul.metadata['name']
                            else:
                                # Fallback to the processed soul name if no name in metadata
                                soul_name_for_filename = selected_soul.name.replace(' ', '_').replace('-', '_').lower()
                                metadata['name'] = soul_name_for_filename

                            # Preserve the crew title in the metadata
                            metadata['crew_title'] = crew_title

                            # Convert back to YAML string
                            new_yaml_str = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)

                            # Reconstruct the content with updated metadata
                            content = f"---\n{new_yaml_str}\n---{content[end_marker_idx+3:]}"
                        except yaml.YAMLError:
                            # If YAML parsing fails, just add soul to metadata
                            soul_name_for_filename = selected_soul.name.replace(' ', '_').replace('-', '_').lower()
                            name_from_soul_meta = selected_soul.metadata.get('name', soul_name_for_filename) if selected_soul.metadata else soul_name_for_filename
                            metadata = {
                                'name': name_from_soul_meta,
                                'soul': selected_soul.name,
                                'crew_title': crew_title
                            }
                            new_yaml_str = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
                            content = f"---\n{new_yaml_str}\n---{content[end_marker_idx+3:]}"

                # Generate the new filename based on the original system crew member file name
                new_filename = system_file.name
            else:
                # If no soul is selected, use the original filename
                new_filename = system_file.name

            target_file = crew_members_dir / new_filename
            if target_file.exists():
                continue

            # Write the updated content to the target file
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(content)

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
        crew_members = self.load_project_crew_members(project)
        return sort_crew_members_by_title_importance(crew_members)

    def refresh_project_crew_members(self, project: Any) -> Dict[str, CrewMember]:
        return self.load_project_crew_members(project, refresh=True)

    def get_project_crew_members(self, project: Any) -> Dict[str, 'CrewMember']:
        """
        Get all crew members for a project.
        Includes backward compatibility for old sub_agents directory.

        Args:
            project: The project to get crew members for

        Returns:
            Dictionary mapping agent names to their CrewMember objects
        """
        return self.load_project_crew_members(project)


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
