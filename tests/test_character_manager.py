"""
Unit tests for Character Management System

Tests cover:
- Character creation, update, deletion
- Resource file management
- Character renaming
- Search functionality
- Edge cases and error handling
"""

import os
import tempfile
import shutil
import unittest
from pathlib import Path

# Add app to path
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(current_dir)
app_path = os.path.join(workspace_root, 'app')
if app_path not in sys.path:
    sys.path.insert(0, app_path)

try:
    from app.data.character import Character, CharacterManager
    from app.data.resource import ResourceManager
except ImportError as e:
    print(f"Warning: Could not import CharacterManager or ResourceManager: {e}")
    print("This is expected if dependencies are not installed.")
    raise


class TestCharacter(unittest.TestCase):
    """Test Character class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.character_data = {
            'character_id': 'test-id-123',
            'name': 'TestCharacter',
            'description': 'A test character',
            'story': 'This is a test story',
            'relationships': {'Friend': 'Good friend'},
            'resources': {'main_view': 'resources/images/test_image.png'},
            'metadata': {},
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_character_initialization(self):
        """Test character initialization"""
        character = Character(self.character_data, self.test_dir)
        
        self.assertEqual(character.name, 'TestCharacter')
        self.assertEqual(character.description, 'A test character')
        self.assertEqual(character.story, 'This is a test story')
        self.assertEqual(character.relationships['Friend'], 'Good friend')
        self.assertEqual(character.resources['main_view'], 'resources/images/test_image.png')
    
    def test_character_to_dict(self):
        """Test character serialization"""
        character = Character(self.character_data, self.test_dir)
        data = character.to_dict()
        
        self.assertEqual(data['name'], 'TestCharacter')
        self.assertEqual(data['character_id'], 'test-id-123')
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_character_resource_paths(self):
        """Test character resource path methods"""
        character = Character(self.character_data, self.test_dir)
        
        rel_path = character.get_resource_path('main_view')
        self.assertEqual(rel_path, 'resources/images/test_image.png')
        
        abs_path = character.get_absolute_resource_path('main_view')
        expected = os.path.join(self.test_dir, 'resources/images/test_image.png')
        self.assertEqual(abs_path, expected)
    
    def test_character_set_remove_resource(self):
        """Test setting and removing resources"""
        character = Character(self.character_data, self.test_dir)
        
        # Set new resource
        character.set_resource('front_view', 'resources/images/front_view.png')
        self.assertIn('front_view', character.resources)
        self.assertEqual(character.resources['front_view'], 
                        'resources/images/front_view.png')
        
        # Remove resource
        character.remove_resource('front_view')
        self.assertNotIn('front_view', character.resources)


class TestCharacterManager(unittest.TestCase):
    """Test CharacterManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.resource_manager = ResourceManager(self.test_dir)
        self.manager = CharacterManager(self.test_dir, self.resource_manager)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_create_character(self):
        """Test creating a new character"""
        character = self.manager.create_character(
            'TestChar',
            description='Test description',
            story='Test story'
        )
        
        self.assertIsNotNone(character)
        self.assertEqual(character.name, 'TestChar')
        self.assertEqual(character.description, 'Test description')
        self.assertEqual(character.story, 'Test story')
        
        # Verify central config file exists
        self.assertTrue(os.path.exists(self.manager.config_path))
    
    def test_create_character_duplicate_name(self):
        """Test creating character with duplicate name"""
        self.manager.create_character('TestChar')
        character = self.manager.create_character('TestChar')
        
        self.assertIsNone(character)  # Should fail
    
    def test_create_character_empty_name(self):
        """Test creating character with empty name"""
        character = self.manager.create_character('')
        self.assertIsNone(character)
        
        character = self.manager.create_character('   ')
        self.assertIsNone(character)
    
    def test_get_character(self):
        """Test getting character by name"""
        self.manager.create_character('TestChar')
        
        character = self.manager.get_character('TestChar')
        self.assertIsNotNone(character)
        self.assertEqual(character.name, 'TestChar')
        
        character = self.manager.get_character('NonExistent')
        self.assertIsNone(character)
    
    def test_list_characters(self):
        """Test listing all characters"""
        self.manager.create_character('Char1')
        self.manager.create_character('Char2')
        self.manager.create_character('Char3')
        
        characters = self.manager.list_characters()
        self.assertEqual(len(characters), 3)
        names = [c.name for c in characters]
        self.assertIn('Char1', names)
        self.assertIn('Char2', names)
        self.assertIn('Char3', names)
    
    def test_update_character(self):
        """Test updating character properties"""
        self.manager.create_character('TestChar', description='Old desc')
        
        success = self.manager.update_character(
            'TestChar',
            description='New desc',
            story='New story'
        )
        
        self.assertTrue(success)
        
        character = self.manager.get_character('TestChar')
        self.assertEqual(character.description, 'New desc')
        self.assertEqual(character.story, 'New story')
    
    def test_update_character_relationships(self):
        """Test updating character relationships"""
        self.manager.create_character('TestChar')
        
        relationships = {
            'Friend1': 'Good friend',
            'Enemy1': 'Rival'
        }
        
        success = self.manager.update_character(
            'TestChar',
            relationships=relationships
        )
        
        self.assertTrue(success)
        
        character = self.manager.get_character('TestChar')
        self.assertEqual(character.relationships['Friend1'], 'Good friend')
        self.assertEqual(character.relationships['Enemy1'], 'Rival')
    
    def test_update_nonexistent_character(self):
        """Test updating non-existent character"""
        success = self.manager.update_character('NonExistent', description='New')
        self.assertFalse(success)
    
    def test_delete_character(self):
        """Test deleting a character"""
        self.manager.create_character('TestChar')
        
        success = self.manager.delete_character('TestChar')
        self.assertTrue(success)
        
        character = self.manager.get_character('TestChar')
        self.assertIsNone(character)
    
    def test_delete_nonexistent_character(self):
        """Test deleting non-existent character"""
        success = self.manager.delete_character('NonExistent')
        self.assertFalse(success)
    
    def test_add_resource(self):
        """Test adding resource file to character"""
        self.manager.create_character('TestChar')
        
        # Create a test image file
        test_image = os.path.join(self.test_dir, 'test_image.png')
        with open(test_image, 'wb') as f:
            f.write(b'fake image data')
        
        rel_path = self.manager.add_resource('TestChar', 'main_view', test_image)
        
        self.assertIsNotNone(rel_path)
        
        character = self.manager.get_character('TestChar')
        self.assertIn('main_view', character.resources)
        
        # Verify file exists in ResourceManager's directory
        abs_path = os.path.join(self.test_dir, rel_path)
        self.assertTrue(os.path.exists(abs_path))
    
    def test_add_resource_nonexistent_character(self):
        """Test adding resource to non-existent character"""
        rel_path = self.manager.add_resource('NonExistent', 'main_view', '/fake/path')
        self.assertIsNone(rel_path)
    
    def test_add_resource_nonexistent_file(self):
        """Test adding non-existent resource file"""
        self.manager.create_character('TestChar')
        
        rel_path = self.manager.add_resource('TestChar', 'main_view', '/fake/path.png')
        self.assertIsNone(rel_path)
    
    def test_remove_resource(self):
        """Test removing resource from character"""
        self.manager.create_character('TestChar')
        
        # Add resource
        test_image = os.path.join(self.test_dir, 'test_image.png')
        with open(test_image, 'wb') as f:
            f.write(b'fake image data')
        
        self.manager.add_resource('TestChar', 'main_view', test_image)
        
        # Remove resource
        success = self.manager.remove_resource('TestChar', 'main_view')
        self.assertTrue(success)
        
        character = self.manager.get_character('TestChar')
        self.assertNotIn('main_view', character.resources)
    
    def test_rename_character(self):
        """Test renaming a character"""
        self.manager.create_character('OldName')
        
        # Add a resource
        test_image = os.path.join(self.test_dir, 'test_image.png')
        with open(test_image, 'wb') as f:
            f.write(b'fake image data')
        
        self.manager.add_resource('OldName', 'main_view', test_image)
        
        # Rename
        success = self.manager.rename_character('OldName', 'NewName')
        self.assertTrue(success)
        
        # Verify old name doesn't exist
        old_char = self.manager.get_character('OldName')
        self.assertIsNone(old_char)
        
        # Verify new name exists
        new_char = self.manager.get_character('NewName')
        self.assertIsNotNone(new_char)
        self.assertEqual(new_char.name, 'NewName')
        
        # Verify resource path still exists
        self.assertIn('main_view', new_char.resources)
    
    def test_rename_character_duplicate_name(self):
        """Test renaming to existing name"""
        self.manager.create_character('Char1')
        self.manager.create_character('Char2')
        
        success = self.manager.rename_character('Char1', 'Char2')
        self.assertFalse(success)
    
    def test_search_characters(self):
        """Test searching characters"""
        self.manager.create_character('Alice', description='A friendly character')
        self.manager.create_character('Bob', story='A brave hero')
        self.manager.create_character('Charlie', description='A mysterious figure')
        
        # Search by name
        results = self.manager.search_characters('Alice')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'Alice')
        
        # Search by description
        results = self.manager.search_characters('friendly')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'Alice')
        
        # Search by story
        results = self.manager.search_characters('brave')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'Bob')
        
        # Case insensitive search
        results = self.manager.search_characters('ALICE')
        self.assertEqual(len(results), 1)
    
    def test_load_existing_characters(self):
        """Test loading existing characters from disk"""
        # Create character manually
        self.manager.create_character('TestChar')
        
        # Create new manager instance (simulating restart)
        new_resource_manager = ResourceManager(self.test_dir)
        new_manager = CharacterManager(self.test_dir, new_resource_manager)
        
        # Verify character is loaded
        character = new_manager.get_character('TestChar')
        self.assertIsNotNone(character)
        self.assertEqual(character.name, 'TestChar')


class TestCharacterManagerIntegration(unittest.TestCase):
    """Integration tests for CharacterManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.resource_manager = ResourceManager(self.test_dir)
        self.manager = CharacterManager(self.test_dir, self.resource_manager)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_full_character_lifecycle(self):
        """Test complete character lifecycle"""
        # Create
        character = self.manager.create_character('Hero', description='A hero')
        self.assertIsNotNone(character)
        
        # Add resources
        test_image1 = os.path.join(self.test_dir, 'front.png')
        test_image2 = os.path.join(self.test_dir, 'back.png')
        with open(test_image1, 'wb') as f:
            f.write(b'front')
        with open(test_image2, 'wb') as f:
            f.write(b'back')
        
        self.manager.add_resource('Hero', 'front_view', test_image1)
        self.manager.add_resource('Hero', 'back_view', test_image2)
        
        # Update
        self.manager.update_character('Hero', story='Hero story')
        
        # Verify
        character = self.manager.get_character('Hero')
        self.assertEqual(character.story, 'Hero story')
        self.assertIn('front_view', character.resources)
        self.assertIn('back_view', character.resources)
        
        # Rename
        self.manager.rename_character('Hero', 'SuperHero')
        
        # Verify rename
        character = self.manager.get_character('SuperHero')
        self.assertIsNotNone(character)
        
        # Delete
        success = self.manager.delete_character('SuperHero')
        self.assertTrue(success)
        
        character = self.manager.get_character('SuperHero')
        self.assertIsNone(character)
    
    def test_rename_character_duplicate_name(self):
        """Test renaming to existing name"""
        self.manager.create_character('Char1')
        self.manager.create_character('Char2')
        
        success = self.manager.rename_character('Char1', 'Char2')
        self.assertFalse(success)
    
    def test_rename_nonexistent_character(self):
        """Test renaming non-existent character"""
        success = self.manager.rename_character('NonExistent', 'NewName')
        self.assertFalse(success)
    
    def test_search_characters(self):
        """Test searching characters"""
        self.manager.create_character('Alice', description='A friendly character')
        self.manager.create_character('Bob', story='A brave hero')
        self.manager.create_character('Charlie', description='A mysterious figure')
        
        # Search by name
        results = self.manager.search_characters('Alice')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'Alice')
        
        # Search by description
        results = self.manager.search_characters('friendly')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'Alice')
        
        # Search by story
        results = self.manager.search_characters('brave')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'Bob')
        
        # Case insensitive search
        results = self.manager.search_characters('ALICE')
        self.assertEqual(len(results), 1)
    
    def test_load_existing_characters(self):
        """Test loading existing characters from disk"""
        # Create character manually
        self.manager.create_character('TestChar')
        
        # Create new manager instance (simulating restart)
        new_manager = CharacterManager(self.test_dir)
        
        # Verify character is loaded
        character = new_manager.get_character('TestChar')
        self.assertIsNotNone(character)
        self.assertEqual(character.name, 'TestChar')


class TestCharacterManagerIntegration(unittest.TestCase):
    """Integration tests for CharacterManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.manager = CharacterManager(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_full_character_lifecycle(self):
        """Test complete character lifecycle"""
        # Create
        character = self.manager.create_character('Hero', description='A hero')
        self.assertIsNotNone(character)
        
        # Add resources
        test_image1 = os.path.join(self.test_dir, 'front.png')
        test_image2 = os.path.join(self.test_dir, 'back.png')
        with open(test_image1, 'wb') as f:
            f.write(b'front')
        with open(test_image2, 'wb') as f:
            f.write(b'back')
        
        self.manager.add_resource('Hero', 'front_view', test_image1)
        self.manager.add_resource('Hero', 'back_view', test_image2)
        
        # Update
        self.manager.update_character('Hero', story='Hero story')
        
        # Verify
        character = self.manager.get_character('Hero')
        self.assertEqual(character.story, 'Hero story')
        self.assertIn('front_view', character.resources)
        self.assertIn('back_view', character.resources)
        
        # Rename
        self.manager.rename_character('Hero', 'SuperHero')
        
        # Verify rename
        character = self.manager.get_character('SuperHero')
        self.assertIsNotNone(character)
        
        # Delete
        success = self.manager.delete_character('SuperHero')
        self.assertTrue(success)
        
        character = self.manager.get_character('SuperHero')
        self.assertIsNone(character)


if __name__ == '__main__':
    unittest.main()

