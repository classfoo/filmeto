from typing import List, Optional
import os
import glob
from .soul import Soul


class SoulService:
    """
    Service class to manage Souls with CRUD operations.
    """
    
    def __init__(self, system_souls_dir: str = None, user_souls_dir: str = None):
        """
        Initialize the SoulService.
        
        Args:
            system_souls_dir: Directory containing system soul definitions
            user_souls_dir: Directory containing user-defined soul definitions
        """
        self.system_souls_dir = system_souls_dir or os.path.join(
            os.path.dirname(__file__), 'system'
        )
        self.user_souls_dir = user_souls_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'workspace', 'agent', 'skills'
        )
        self.souls: List[Soul] = []
        
        # Load all souls on initialization
        self.load_system_souls()
        self.load_user_souls()
    
    def load_system_souls(self):
        """Load all system souls from the system directory."""
        if not os.path.exists(self.system_souls_dir):
            return
            
        md_files = glob.glob(os.path.join(self.system_souls_dir, '*.md'))
        for md_file in md_files:
            soul = self._create_soul_from_file(md_file)
            if soul:
                self.souls.append(soul)
    
    def load_user_souls(self):
        """Load all user-defined souls from the user directory."""
        if not os.path.exists(self.user_souls_dir):
            return
            
        md_files = glob.glob(os.path.join(self.user_souls_dir, '*.md'))
        for md_file in md_files:
            soul = self._create_soul_from_file(md_file)
            if soul:
                self.souls.append(soul)
    
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
    
    def get_soul_by_name(self, name: str) -> Optional[Soul]:
        """
        Retrieve a soul by its name.
        
        Args:
            name: Name of the soul to retrieve
            
        Returns:
            Soul instance if found, None otherwise
        """
        for soul in self.souls:
            if soul.name == name:
                return soul
        return None
    
    def get_all_souls(self) -> List[Soul]:
        """
        Retrieve all available souls.
        
        Returns:
            List of all Soul instances
        """
        return self.souls.copy()
    
    def add_soul(self, soul: Soul) -> bool:
        """
        Add a new soul to the service.
        
        Args:
            soul: Soul instance to add
            
        Returns:
            True if added successfully, False if soul with same name already exists
        """
        if self.get_soul_by_name(soul.name):
            return False  # Soul with this name already exists
        
        self.souls.append(soul)
        return True
    
    def update_soul(self, name: str, new_soul: Soul) -> bool:
        """
        Update an existing soul.
        
        Args:
            name: Name of the soul to update
            new_soul: New Soul instance to replace the old one
            
        Returns:
            True if updated successfully, False if soul doesn't exist
        """
        for i, soul in enumerate(self.souls):
            if soul.name == name:
                self.souls[i] = new_soul
                return True
        return False
    
    def delete_soul(self, name: str) -> bool:
        """
        Delete a soul by its name.
        
        Args:
            name: Name of the soul to delete
            
        Returns:
            True if deleted successfully, False if soul doesn't exist
        """
        for i, soul in enumerate(self.souls):
            if soul.name == name:
                del self.souls[i]
                return True
        return False
    
    def search_souls_by_skill(self, skill: str) -> List[Soul]:
        """
        Find all souls that have a specific skill.
        
        Args:
            skill: Skill to search for
            
        Returns:
            List of Soul instances that have the specified skill
        """
        matching_souls = []
        for soul in self.souls:
            if skill in soul.skills:
                matching_souls.append(soul)
        return matching_souls