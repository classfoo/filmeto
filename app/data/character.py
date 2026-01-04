"""
Character Management System

Manages character data for projects with support for:
- Character metadata (name, story, relationships, etc.)
- Character resource files (images: main view, front, back, left, right, poses, costumes, etc.)
- Project-scoped character organization
"""

import os
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from blinker import signal

from utils.yaml_utils import load_yaml, save_yaml


class Character:
    """Represents a single character in the project"""
    
    # Resource file types
    RESOURCE_TYPES = {
        'main_view': '主视图',
        'front_view': '前视图',
        'back_view': '后视图',
        'left_view': '左视图',
        'right_view': '右视图',
        'pose': '姿势图',
        'costume': '服装图',
        'other': '其他'
    }
    
    def __init__(self, data: Dict[str, Any], project_path: str):
        """Initialize character from metadata dictionary
        
        Args:
            data: Character metadata dictionary
            project_path: Absolute path to the project directory
        """
        self.project_path = project_path
        self.character_id = data.get('character_id', str(uuid.uuid4()))
        self.name = data.get('name', '')
        self.description = data.get('description', '')
        self.story = data.get('story', '')
        self.relationships = data.get('relationships', {})  # Dict of character_name -> relationship_description
        self.resources = data.get('resources', {})  # Dict of resource_type -> file_path (relative)
        self.metadata = data.get('metadata', {})  # Additional metadata
        self.created_at = data.get('created_at', datetime.now().isoformat())
        self.updated_at = data.get('updated_at', datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert character to dictionary for serialization"""
        return {
            'character_id': self.character_id,
            'name': self.name,
            'description': self.description,
            'story': self.story,
            'relationships': self.relationships,
            'resources': self.resources,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def get_directory(self) -> str:
        """Get character directory path (relative to project root)"""
        return os.path.join('characters', self.name)
    
    def get_absolute_directory(self) -> str:
        """Get absolute character directory path"""
        return os.path.join(self.project_path, self.get_directory())
    
    def get_config_path(self) -> str:
        """Get character config.yaml path (relative to project root)"""
        return os.path.join(self.get_directory(), 'config.yaml')
    
    def get_absolute_config_path(self) -> str:
        """Get absolute character config.yaml path"""
        return os.path.join(self.project_path, self.get_config_path())
    
    def get_resource_path(self, resource_type: str) -> Optional[str]:
        """Get resource file path (relative to project root)
        
        Args:
            resource_type: Type of resource (main_view, front_view, etc.)
            
        Returns:
            Relative file path or None if not set
        """
        return self.resources.get(resource_type)
    
    def get_absolute_resource_path(self, resource_type: str) -> Optional[str]:
        """Get absolute resource file path
        
        Args:
            resource_type: Type of resource
            
        Returns:
            Absolute file path or None if not set
        """
        rel_path = self.get_resource_path(resource_type)
        if rel_path:
            return os.path.join(self.project_path, rel_path)
        return None
    
    def resource_exists(self, resource_type: str) -> bool:
        """Check if resource file exists
        
        Args:
            resource_type: Type of resource
            
        Returns:
            True if resource exists, False otherwise
        """
        abs_path = self.get_absolute_resource_path(resource_type)
        return abs_path is not None and os.path.exists(abs_path)
    
    def set_resource(self, resource_type: str, file_path: str):
        """Set resource file path
        
        Args:
            resource_type: Type of resource
            file_path: Relative file path from project root
        """
        self.resources[resource_type] = file_path
        self.updated_at = datetime.now().isoformat()
    
    def remove_resource(self, resource_type: str):
        """Remove resource file reference
        
        Args:
            resource_type: Type of resource
        """
        if resource_type in self.resources:
            del self.resources[resource_type]
            self.updated_at = datetime.now().isoformat()


class CharacterManager:
    """Manages project characters with directory-based storage"""
    
    # Signals for character events
    character_added = signal('character_added')
    character_updated = signal('character_updated')
    character_deleted = signal('character_deleted')
    
    def __init__(self, project_path: str):
        """Initialize character manager for a project
        
        Args:
            project_path: Absolute path to the project directory
        """
        self.project_path = project_path
        self.characters_dir = os.path.join(project_path, 'characters')
        
        # In-memory index: character_name -> Character
        self._characters: Dict[str, Character] = {}
        
        # Initialize directory structure
        self._ensure_directories()
        
        # Load existing characters
        self._load_characters()
    
    def _ensure_directories(self):
        """Create characters directory if it doesn't exist"""
        os.makedirs(self.characters_dir, exist_ok=True)
    
    def _load_characters(self):
        """Load all characters from disk"""
        if not os.path.exists(self.characters_dir):
            return
        
        for item in os.listdir(self.characters_dir):
            character_dir = os.path.join(self.characters_dir, item)
            if os.path.isdir(character_dir):
                config_path = os.path.join(character_dir, 'config.yaml')
                if os.path.exists(config_path):
                    try:
                        data = load_yaml(config_path)
                        if data:
                            character = Character(data, self.project_path)
                            self._characters[character.name] = character
                            print(f"✅ Loaded character: {character.name}")
                    except Exception as e:
                        print(f"❌ Error loading character {item}: {e}")
    
    def _save_character(self, character: Character) -> bool:
        """Save character to disk
        
        Args:
            character: Character instance to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure character directory exists
            char_dir = character.get_absolute_directory()
            os.makedirs(char_dir, exist_ok=True)
            
            # Save config.yaml
            config_path = character.get_absolute_config_path()
            save_yaml(config_path, character.to_dict())
            
            return True
        except Exception as e:
            print(f"❌ Error saving character {character.name}: {e}")
            return False
    
    def create_character(self, name: str, description: str = '', story: str = '') -> Optional[Character]:
        """Create a new character
        
        Args:
            name: Character name (must be unique)
            description: Character description
            story: Character story/background
            
        Returns:
            Character instance if successful, None if name already exists
        """
        # Validate name
        if not name or not name.strip():
            print("❌ Character name cannot be empty")
            return None
        
        name = name.strip()
        
        # Check if character already exists
        if name in self._characters:
            print(f"❌ Character '{name}' already exists")
            return None
        
        # Create character instance
        character_data = {
            'character_id': str(uuid.uuid4()),
            'name': name,
            'description': description,
            'story': story,
            'relationships': {},
            'resources': {},
            'metadata': {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        character = Character(character_data, self.project_path)
        
        # Save to disk
        if not self._save_character(character):
            return None
        
        # Add to index
        self._characters[name] = character
        
        # Send signal
        self.character_added.send(character)
        
        print(f"✅ Created character: {name}")
        return character
    
    def get_character(self, name: str) -> Optional[Character]:
        """Get character by name
        
        Args:
            name: Character name
            
        Returns:
            Character instance or None if not found
        """
        return self._characters.get(name)
    
    def list_characters(self) -> List[Character]:
        """List all characters
        
        Returns:
            List of Character instances
        """
        return list(self._characters.values())
    
    def update_character(self, name: str, **kwargs) -> bool:
        """Update character properties
        
        Args:
            name: Character name
            **kwargs: Properties to update (description, story, relationships, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        character = self.get_character(name)
        if not character:
            print(f"❌ Character '{name}' not found")
            return False
        
        # Update allowed fields
        allowed_fields = ['description', 'story', 'relationships', 'metadata']
        updated = False
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(character, field):
                setattr(character, field, value)
                updated = True
        
        if updated:
            character.updated_at = datetime.now().isoformat()
            
            # Save to disk
            if not self._save_character(character):
                return False
            
            # Send signal
            self.character_updated.send(character)
            
            print(f"✅ Updated character: {name}")
            return True
        
        return False
    
    def delete_character(self, name: str, remove_files: bool = True) -> bool:
        """Delete a character
        
        Args:
            name: Character name
            remove_files: Whether to remove character directory (default: True)
            
        Returns:
            True if successful, False otherwise
        """
        character = self.get_character(name)
        if not character:
            print(f"❌ Character '{name}' not found")
            return False
        
        try:
            # Remove character directory if requested
            if remove_files:
                char_dir = character.get_absolute_directory()
                if os.path.exists(char_dir):
                    shutil.rmtree(char_dir)
            
            # Remove from index
            del self._characters[name]
            
            # Send signal
            self.character_deleted.send(name)
            
            print(f"✅ Deleted character: {name}")
            return True
        except Exception as e:
            print(f"❌ Error deleting character {name}: {e}")
            return False
    
    def add_resource(self, character_name: str, resource_type: str, source_file_path: str) -> Optional[str]:
        """Add a resource file to a character
        
        Args:
            character_name: Character name
            resource_type: Type of resource (main_view, front_view, etc.)
            source_file_path: Path to source file (absolute or relative)
            
        Returns:
            Relative path to the resource file if successful, None otherwise
        """
        character = self.get_character(character_name)
        if not character:
            print(f"❌ Character '{character_name}' not found")
            return None
        
        # Validate source file exists
        if not os.path.isabs(source_file_path):
            source_file_path = os.path.join(self.project_path, source_file_path)
        
        if not os.path.exists(source_file_path):
            print(f"❌ Source file does not exist: {source_file_path}")
            return None
        
        try:
            # Get file extension
            _, ext = os.path.splitext(os.path.basename(source_file_path))
            
            # Generate resource filename
            resource_filename = f"{resource_type}{ext}"
            
            # Determine destination path
            char_dir = character.get_absolute_directory()
            resources_dir = os.path.join(char_dir, 'resources')
            os.makedirs(resources_dir, exist_ok=True)
            
            destination_path = os.path.join(resources_dir, resource_filename)
            
            # Handle filename conflicts
            counter = 1
            base_name, ext = os.path.splitext(resource_filename)
            while os.path.exists(destination_path):
                resource_filename = f"{base_name}_{counter}{ext}"
                destination_path = os.path.join(resources_dir, resource_filename)
                counter += 1
            
            # Copy file to character resources directory
            shutil.copy2(source_file_path, destination_path)
            
            # Set resource path (relative to project root)
            relative_path = os.path.join(character.get_directory(), 'resources', resource_filename)
            character.set_resource(resource_type, relative_path)
            
            # Save character config
            if not self._save_character(character):
                # Cleanup copied file if save failed
                if os.path.exists(destination_path):
                    os.remove(destination_path)
                return None
            
            # Send signal
            self.character_updated.send(character)
            
            print(f"✅ Added resource '{resource_type}' to character '{character_name}'")
            return relative_path
            
        except Exception as e:
            print(f"❌ Error adding resource to character {character_name}: {e}")
            return None
    
    def remove_resource(self, character_name: str, resource_type: str, remove_file: bool = True) -> bool:
        """Remove a resource from a character
        
        Args:
            character_name: Character name
            resource_type: Type of resource
            remove_file: Whether to delete the physical file (default: True)
            
        Returns:
            True if successful, False otherwise
        """
        character = self.get_character(character_name)
        if not character:
            print(f"❌ Character '{character_name}' not found")
            return False
        
        # Get resource path
        abs_path = character.get_absolute_resource_path(resource_type)
        
        # Remove file if requested
        if remove_file and abs_path and os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception as e:
                print(f"⚠️ Warning: Could not remove resource file: {e}")
        
        # Remove resource reference
        character.remove_resource(resource_type)
        
        # Save character config
        if not self._save_character(character):
            return False
        
        # Send signal
        self.character_updated.send(character)
        
        print(f"✅ Removed resource '{resource_type}' from character '{character_name}'")
        return True
    
    def rename_character(self, old_name: str, new_name: str) -> bool:
        """Rename a character
        
        Args:
            old_name: Current character name
            new_name: New character name
            
        Returns:
            True if successful, False otherwise
        """
        character = self.get_character(old_name)
        if not character:
            print(f"❌ Character '{old_name}' not found")
            return False
        
        new_name = new_name.strip()
        if not new_name:
            print("❌ New character name cannot be empty")
            return False
        
        if new_name in self._characters:
            print(f"❌ Character '{new_name}' already exists")
            return False
        
        try:
            # Update character name
            old_dir = character.get_absolute_directory()
            character.name = new_name
            new_dir = character.get_absolute_directory()
            
            # Rename directory
            if os.path.exists(old_dir):
                os.rename(old_dir, new_dir)
            
            # Update resource paths in character data
            updated_resources = {}
            for resource_type, rel_path in character.resources.items():
                # Update path to reflect new directory name
                parts = rel_path.split(os.sep)
                if len(parts) >= 2 and parts[0] == 'characters':
                    parts[0] = 'characters'
                    parts[1] = new_name
                    updated_resources[resource_type] = os.sep.join(parts)
                else:
                    updated_resources[resource_type] = rel_path
            character.resources = updated_resources
            
            # Save updated character
            if not self._save_character(character):
                return False
            
            # Update index
            del self._characters[old_name]
            self._characters[new_name] = character
            
            # Send signal
            self.character_updated.send(character)
            
            print(f"✅ Renamed character '{old_name}' to '{new_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Error renaming character {old_name}: {e}")
            return False
    
    def search_characters(self, query: str) -> List[Character]:
        """Search characters by name or description
        
        Args:
            query: Search query string
            
        Returns:
            List of matching Character instances
        """
        query_lower = query.lower()
        results = []
        
        for character in self._characters.values():
            if (query_lower in character.name.lower() or 
                query_lower in character.description.lower() or
                query_lower in character.story.lower()):
                results.append(character)
        
        return results

