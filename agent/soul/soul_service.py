from typing import List, Optional, Dict
import os
import glob
from .soul import Soul


class SoulService:
    """
    Singleton service class to manage Souls with CRUD operations.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoulService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the SoulService singleton.
        Use the setup method to configure with workspace.
        """
        if not self._initialized:
            self.workspace = None
            self.system_souls_dir = os.path.join(
                os.path.dirname(__file__), 'system'
            )
            self.project_souls: Dict[str, List[Soul]] = {}  # Store souls per project
            self._initialized = True

    def setup(self, workspace):
        """
        Setup the SoulService with a workspace object.

        Args:
            workspace: The workspace object to use for project management
        """
        self.workspace = workspace
    
    def load_system_souls(self, language: str = 'en_US'):
        """
        Load all system souls from the system directory based on language.

        Args:
            language: Language code for selecting appropriate souls (default: 'en_US')
        """
        # Construct path to language-specific directory
        lang_system_dir = os.path.join(self.system_souls_dir, language)

        if not os.path.exists(lang_system_dir):
            return []

        souls = []
        md_files = glob.glob(os.path.join(lang_system_dir, '*.md'))
        for md_file in md_files:
            soul = self._create_soul_from_file(md_file)
            if soul:
                souls.append(soul)
        return souls
    
    def load_user_souls(self, project_id: str):
        """
        Load all user-defined souls from the project's agent directory.

        Args:
            project_id: The ID of the project to load user souls for
        """
        if not self.workspace:
            return []

        # Get the project object from workspace
        project = self.workspace.get_project()
        if not project or project.project_name != project_id:
            # Try to get project by name from project manager
            project = self.workspace.project_manager.get_project(project_id)

        if not project:
            return []

        # User souls are stored in the project's agent/souls directory
        project_souls_dir = os.path.join(project.project_path, "agent", "souls")

        if not os.path.exists(project_souls_dir):
            return []

        souls = []
        md_files = glob.glob(os.path.join(project_souls_dir, '*.md'))
        for md_file in md_files:
            soul = self._create_soul_from_file(md_file)
            if soul:
                souls.append(soul)
        return souls
    
    def _create_soul_from_file(self, file_path: str) -> Optional[Soul]:
        """
        Create a Soul instance from an MD file.

        Args:
            file_path: Path to the MD file containing soul definition

        Returns:
            Soul instance or None if creation failed
        """
        filename = os.path.basename(file_path)
        # Extract name from filename (without extension) as fallback
        fallback_name = os.path.splitext(filename)[0]

        # Create a basic soul with the fallback name initially
        soul = Soul(name=fallback_name, skills=[], description_file=file_path)

        # Get the actual name from the metadata if available
        actual_name = fallback_name
        if soul.metadata and 'name' in soul.metadata:
            actual_name = soul.metadata['name']

        # Update the soul's name to the one from metadata
        soul.name = actual_name

        # If the soul has metadata with skills, update the skills list
        if soul.metadata and 'skills' in soul.metadata:
            soul.skills = soul.metadata['skills']

        return soul

    def get_project_language(self, project_id: str) -> str:
        """
        Get the language setting for a specific project.

        Args:
            project_id: The ID of the project

        Returns:
            Language code for the project (default: 'en_US')
        """
        if not self.workspace:
            return 'en_US'

        # Try to get project by name from project manager
        project = self.workspace.project_manager.get_project(project_id)

        if not project:
            return 'en_US'

        # Use the method from the Project class
        return project.get_language()

    def load_souls_for_project(self, project_id: str) -> List[Soul]:
        """
        Load all souls for a specific project based on its language setting.

        Args:
            project_id: The ID of the project to load souls for

        Returns:
            List of Soul instances for the project
        """
        language = self.get_project_language(project_id)

        # Load system souls for the project
        system_souls = self.load_system_souls(language)

        # Load user souls for the project
        user_souls = self.load_user_souls(project_id)

        # Combine both lists
        all_souls = system_souls + user_souls

        # Store in the project_souls dictionary
        self.project_souls[project_id] = all_souls

        return all_souls
    
    def get_soul_by_name(self, project_id: str, name: str) -> Optional[Soul]:
        """
        Retrieve a soul by its name for a specific project.

        Args:
            project_id: The ID of the project
            name: Name of the soul to retrieve

        Returns:
            Soul instance if found, None otherwise
        """
        # Ensure souls are loaded for the project
        if project_id not in self.project_souls:
            self.load_souls_for_project(project_id)

        for soul in self.project_souls[project_id]:
            if soul.name == name:
                return soul
        return None

    def get_all_souls(self, project_id: str) -> List[Soul]:
        """
        Retrieve all available souls for a specific project.

        Args:
            project_id: The ID of the project

        Returns:
            List of all Soul instances for the project
        """
        # Ensure souls are loaded for the project
        if project_id not in self.project_souls:
            self.load_souls_for_project(project_id)

        return self.project_souls[project_id].copy()

    def add_soul(self, project_id: str, soul: Soul) -> bool:
        """
        Add a new soul to the service for a specific project.

        Args:
            project_id: The ID of the project
            soul: Soul instance to add

        Returns:
            True if added successfully, False if soul with same name already exists
        """
        # Ensure souls are loaded for the project
        if project_id not in self.project_souls:
            self.load_souls_for_project(project_id)

        if self.get_soul_by_name(project_id, soul.name):
            return False  # Soul with this name already exists

        self.project_souls[project_id].append(soul)
        return True

    def update_soul(self, project_id: str, name: str, new_soul: Soul) -> bool:
        """
        Update an existing soul for a specific project.

        Args:
            project_id: The ID of the project
            name: Name of the soul to update
            new_soul: New Soul instance to replace the old one

        Returns:
            True if updated successfully, False if soul doesn't exist
        """
        # Ensure souls are loaded for the project
        if project_id not in self.project_souls:
            self.load_souls_for_project(project_id)

        for i, soul in enumerate(self.project_souls[project_id]):
            if soul.name == name:
                self.project_souls[project_id][i] = new_soul
                return True
        return False

    def delete_soul(self, project_id: str, name: str) -> bool:
        """
        Delete a soul by its name for a specific project.

        Args:
            project_id: The ID of the project
            name: Name of the soul to delete

        Returns:
            True if deleted successfully, False if soul doesn't exist
        """
        # Ensure souls are loaded for the project
        if project_id not in self.project_souls:
            self.load_souls_for_project(project_id)

        for i, soul in enumerate(self.project_souls[project_id]):
            if soul.name == name:
                del self.project_souls[project_id][i]
                return True
        return False

    def search_souls_by_skill(self, project_id: str, skill: str) -> List[Soul]:
        """
        Find all souls that have a specific skill for a specific project.

        Args:
            project_id: The ID of the project
            skill: Skill to search for

        Returns:
            List of Soul instances that have the specified skill
        """
        # Ensure souls are loaded for the project
        if project_id not in self.project_souls:
            self.load_souls_for_project(project_id)

        matching_souls = []
        for soul in self.project_souls[project_id]:
            if skill in soul.skills:
                matching_souls.append(soul)
        return matching_souls

    def refresh_souls_for_project(self, project_id: str) -> bool:
        """
        Refresh/reload souls for a specific project.

        Args:
            project_id: The ID of the project to refresh souls for

        Returns:
            True if refresh was successful
        """
        try:
            self.load_souls_for_project(project_id)
            return True
        except Exception:
            return False

    def get_available_languages(self) -> List[str]:
        """
        Get a list of available languages for souls.

        Returns:
            List of available language codes
        """
        if not os.path.exists(self.system_souls_dir):
            return []

        languages = []
        for item in os.listdir(self.system_souls_dir):
            item_path = os.path.join(self.system_souls_dir, item)
            if os.path.isdir(item_path):
                languages.append(item)
        return languages