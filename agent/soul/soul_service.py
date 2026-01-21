from typing import List, Optional, Dict
import os
import glob
from .soul import Soul


class SoulService:
    """
    Singleton service class to manage Souls with CRUD operations.

    This service handles:
    - Loading system and user-defined souls for projects
    - Creating new souls using create_soul with md_with_meta_utils
    - Updating existing souls using update_soul_with_metadata with md_with_meta_utils
    - Deleting souls using delete_soul_file with md_with_meta_utils
    - Managing soul lifecycle per project
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
    
    def load_user_souls(self, project_name: str):
        """
        Load all user-defined souls from the project's agent directory.

        Args:
            project_name: The name of the project to load user souls for
        """
        if not self.workspace:
            return []

        # Get the project object from workspace
        project = self.workspace.get_project()
        if not project or project.project_name != project_name:
            # Try to get project by name from project manager
            project = self.workspace.project_manager.get_project(project_name)

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

    def get_project_language(self, project_name: str) -> str:
        """
        Get the language setting for a specific project.

        Args:
            project_name: The name of the project

        Returns:
            Language code for the project (default: 'en_US')
        """
        if not self.workspace:
            return 'en_US'

        # Try to get project by name from project manager
        project = self.workspace.project_manager.get_project(project_name)

        if not project:
            return 'en_US'

        # Use the method from the Project class
        return project.get_language()

    def load_souls_for_project(self, project_name: str) -> List[Soul]:
        """
        Load all souls for a specific project based on its language setting.

        Args:
            project_name: The name of the project to load souls for

        Returns:
            List of Soul instances for the project
        """
        language = self.get_project_language(project_name)

        # Load system souls for the project
        system_souls = self.load_system_souls(language)

        # Load user souls for the project
        user_souls = self.load_user_souls(project_name)

        # Combine both lists
        all_souls = system_souls + user_souls

        # Store in the project_souls dictionary
        self.project_souls[project_name] = all_souls

        return all_souls
    
    def get_soul_by_name(self, project_name: str, name: str) -> Optional[Soul]:
        """
        Retrieve a soul by its name for a specific project.

        Args:
            project_name: The name of the project
            name: Name of the soul to retrieve

        Returns:
            Soul instance if found, None otherwise
        """
        # Ensure souls are loaded for the project
        if project_name not in self.project_souls:
            self.load_souls_for_project(project_name)

        for soul in self.project_souls[project_name]:
            if soul.name == name:
                return soul
        return None

    def get_all_souls(self, project_name: str) -> List[Soul]:
        """
        Retrieve all available souls for a specific project.

        Args:
            project_name: The name of the project

        Returns:
            List of all Soul instances for the project
        """
        # Ensure souls are loaded for the project
        if project_name not in self.project_souls:
            self.load_souls_for_project(project_name)

        return self.project_souls[project_name].copy()

    def add_soul(self, project_name: str, soul: Soul) -> bool:
        """
        Add a new soul to the service for a specific project.

        Args:
            project_name: The name of the project
            soul: Soul instance to add

        Returns:
            True if added successfully, False if soul with same name already exists
        """
        # Ensure souls are loaded for the project
        if project_name not in self.project_souls:
            self.load_souls_for_project(project_name)

        if self.get_soul_by_name(project_name, soul.name):
            return False  # Soul with this name already exists

        self.project_souls[project_name].append(soul)
        return True

    def update_soul(self, project_name: str, name: str, new_soul: Soul) -> bool:
        """
        Update an existing soul for a specific project.

        Args:
            project_name: The name of the project
            name: Name of the soul to update
            new_soul: New Soul instance to replace the old one

        Returns:
            True if updated successfully, False if soul doesn't exist
        """
        # Ensure souls are loaded for the project
        if project_name not in self.project_souls:
            self.load_souls_for_project(project_name)

        for i, soul in enumerate(self.project_souls[project_name]):
            if soul.name == name:
                self.project_souls[project_name][i] = new_soul
                return True
        return False

    def delete_soul(self, project_name: str, name: str) -> bool:
        """
        Delete a soul by its name for a specific project.

        Args:
            project_name: The name of the project
            name: Name of the soul to delete

        Returns:
            True if deleted successfully, False if soul doesn't exist
        """
        # Ensure souls are loaded for the project
        if project_name not in self.project_souls:
            self.load_souls_for_project(project_name)

        for i, soul in enumerate(self.project_souls[project_name]):
            if soul.name == name:
                del self.project_souls[project_name][i]
                return True
        return False

    def search_souls_by_skill(self, project_name: str, skill: str) -> List[Soul]:
        """
        Find all souls that have a specific skill for a specific project.

        Args:
            project_name: The name of the project
            skill: Skill to search for

        Returns:
            List of Soul instances that have the specified skill
        """
        # Ensure souls are loaded for the project
        if project_name not in self.project_souls:
            self.load_souls_for_project(project_name)

        matching_souls = []
        for soul in self.project_souls[project_name]:
            if skill in soul.skills:
                matching_souls.append(soul)
        return matching_souls

    def refresh_souls_for_project(self, project_name: str) -> bool:
        """
        Refresh/reload souls for a specific project.

        Args:
            project_name: The name of the project to refresh souls for

        Returns:
            True if refresh was successful
        """
        try:
            self.load_souls_for_project(project_name)
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

    def create_soul(self, project_name: str, soul: Soul) -> bool:
        """
        Create a new soul using md_with_meta_utils to write the MD file.

        Args:
            project_name: The name of the project to create the soul for
            soul: Soul object to create

        Returns:
            True if creation was successful, False otherwise
        """
        from utils.md_with_meta_utils import write_md_with_meta

        # Get the project object
        if not self.workspace:
            return False

        project = self.workspace.project_manager.get_project(project_name)
        if not project:
            return False

        # Create the souls directory if it doesn't exist
        souls_dir = os.path.join(project.project_path, "agent", "souls")
        os.makedirs(souls_dir, exist_ok=True)

        # Prepare metadata for the soul
        metadata = {
            'name': soul.name,
            'skills': soul.skills,
            'crew_title': soul.metadata.get('crew_title', '') if soul.metadata else ''
        }

        # Write the soul MD file using md_with_meta_utils
        soul_file_path = os.path.join(souls_dir, f"{soul.name.replace(' ', '_').replace('-', '_').lower()}.md")
        try:
            write_md_with_meta(soul_file_path, metadata, soul.knowledge or "")

            # Add the soul to the project's soul list
            if project_name not in self.project_souls:
                self.project_souls[project_name] = []
            self.project_souls[project_name].append(soul)

            return True
        except Exception as e:
            print(f"Error creating soul {soul.name}: {e}")
            return False

    def update_soul_with_metadata(self, project_name: str, soul_name: str, updated_soul: Soul) -> bool:
        """
        Update an existing soul using md_with_meta_utils to update the MD file.

        Args:
            project_name: The name of the project containing the soul
            soul_name: Name of the soul to update
            updated_soul: Updated Soul object

        Returns:
            True if update was successful, False otherwise
        """
        from utils.md_with_meta_utils import update_md_with_meta

        # Get the project object
        if not self.workspace:
            return False

        project = self.workspace.project_manager.get_project(project_name)
        if not project:
            return False

        # Find the existing soul file
        souls_dir = os.path.join(project.project_path, "agent", "souls")
        soul_file_path = os.path.join(souls_dir, f"{soul_name.replace(' ', '_').replace('-', '_').lower()}.md")

        if not os.path.exists(soul_file_path):
            return False

        # Prepare metadata for the updated soul
        metadata = {
            'name': updated_soul.name,
            'skills': updated_soul.skills,
            'crew_title': updated_soul.metadata.get('crew_title', '') if updated_soul.metadata else ''
        }

        try:
            # Update the soul MD file using md_with_meta_utils
            success = update_md_with_meta(soul_file_path, metadata, updated_soul.knowledge or "")

            if success:
                # Update the soul in the project's soul list
                for i, soul in enumerate(self.project_souls.get(project_name, [])):
                    if soul.name == soul_name:
                        self.project_souls[project_name][i] = updated_soul
                        break

            return success
        except Exception as e:
            print(f"Error updating soul {soul_name}: {e}")
            return False

    def delete_soul_file(self, project_name: str, soul_name: str) -> bool:
        """
        Delete a soul by removing its MD file.

        Args:
            project_name: The name of the project containing the soul
            soul_name: Name of the soul to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        import os

        # Get the project object
        if not self.workspace:
            return False

        project = self.workspace.project_manager.get_project(project_name)
        if not project:
            return False

        # Find the soul file
        souls_dir = os.path.join(project.project_path, "agent", "souls")
        soul_file_path = os.path.join(souls_dir, f"{soul_name.replace(' ', '_').replace('-', '_').lower()}.md")

        if not os.path.exists(soul_file_path):
            return False

        try:
            # Remove the soul file
            os.remove(soul_file_path)

            # Remove the soul from the project's soul list
            if project_name in self.project_souls:
                self.project_souls[project_name] = [
                    soul for soul in self.project_souls[project_name]
                    if soul.name != soul_name
                ]

            return True
        except Exception as e:
            print(f"Error deleting soul {soul_name}: {e}")
            return False