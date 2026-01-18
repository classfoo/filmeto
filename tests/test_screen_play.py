"""
Unit tests for the ScreenPlayManager and related classes.

These tests validate the functionality of the screenplay management system,
including creation, retrieval, updating, and deletion of screenplay scenes.
"""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

from app.data.screen_play import ScreenPlayManager, ScreenPlayScene, ScreenPlayFormatter


class TestScreenPlayScene:
    """Test cases for the ScreenPlayScene class."""
    
    def test_screenplay_scene_initialization(self):
        """Test initializing a ScreenPlayScene object."""
        scene_id = "scene_001"
        title = "Opening Scene"
        content = "FADE IN: ..."
        metadata = {"location": "EXT. HOUSE - DAY"}
        
        scene = ScreenPlayScene(scene_id, title, content, metadata)
        
        assert scene.scene_id == scene_id
        assert scene.title == title
        assert scene.content == content
        assert scene.metadata == metadata
    
    def test_screenplay_scene_to_dict(self):
        """Test converting a ScreenPlayScene to a dictionary."""
        scene_id = "scene_001"
        title = "Opening Scene"
        content = "FADE IN: ..."
        metadata = {"location": "EXT. HOUSE - DAY"}
        
        scene = ScreenPlayScene(scene_id, title, content, metadata)
        scene_dict = scene.to_dict()
        
        expected_dict = {
            "scene_id": scene_id,
            "title": title,
            "content": content,
            "metadata": metadata
        }
        
        assert scene_dict == expected_dict
    
    def test_format_hollywood_screenplay_basic(self):
        """Test basic screenplay formatting."""
        formatted = ScreenPlayScene.format_hollywood_screenplay(
            scene_heading="EXT. CITY STREET - NIGHT",
            action="Rain falls heavily on the empty street.",
            character="JACK",
            dialogue="Where is she?",
            parenthetical="(looking around frantically)"
        )
        
        expected_lines = [
            "# EXT. CITY STREET - NIGHT",
            "",
            "Rain falls heavily on the empty street.",
            "",
            "**JACK**",
            "*(looking around frantically)*",
            "Where is she?",
            ""
        ]
        expected = "\n".join(expected_lines).rstrip()
        
        assert formatted == expected
    
    def test_format_hollywood_screenplay_with_transition(self):
        """Test screenplay formatting with transition."""
        formatted = ScreenPlayScene.format_hollywood_screenplay(
            scene_heading="INT. APARTMENT - DAY",
            action="SARAH sits at the kitchen table, staring at her phone.",
            transition="CUT TO:"
        )
        
        expected_lines = [
            "# INT. APARTMENT - DAY",
            "",
            "SARAH sits at the kitchen table, staring at her phone.",
            "",
            "_CUT TO:_",
            ""
        ]
        expected = "\n".join(expected_lines).rstrip()
        
        assert formatted == expected


class TestScreenPlayFormatter:
    """Test cases for the ScreenPlayFormatter class."""
    
    def test_format_scene_content(self):
        """Test formatting a complete scene."""
        scene_content = {
            "scene_heading": "INT. COFFEE SHOP - MORNING",
            "action": "JANET waits in line, checking her watch repeatedly.",
            "dialogue": [
                {
                    "character": "BARISTA",
                    "dialogue": "Next!",
                    "parenthetical": "(cheerfully)"
                },
                {
                    "character": "JANET",
                    "dialogue": "Finally. Can I get a large coffee, black?",
                    "parenthetical": "(sighs)"
                }
            ],
            "transition": "FADE OUT."
        }
        
        formatted = ScreenPlayFormatter.format_scene_content(
            scene_number="1",
            location="COFFEE SHOP",
            time_of_day="MORNING",
            characters=["JANET", "BARISTA"],
            scene_content=scene_content
        )
        
        # Check that the formatted content contains expected elements
        assert "SCENE 1: COFFEE SHOP - MORNING" in formatted
        assert "CHARACTERS PRESENT:" in formatted
        assert "JANET, BARISTA" in formatted
        assert "INT. COFFEE SHOP - MORNING" in formatted
        assert "JANET waits in line, checking her watch repeatedly." in formatted
        assert "BARISTA" in formatted
        assert "Next!" in formatted
        assert "cheerfully" in formatted
        assert "JANET" in formatted
        assert "Can I get a large coffee, black?" in formatted
        assert "sighs" in formatted
        assert "FADE OUT." in formatted


class TestScreenPlayManager:
    """Test cases for the ScreenPlayManager class."""
    
    def setup_method(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = ScreenPlayManager(self.temp_dir)
        self.test_scene_id = "test_scene_001"
        self.test_title = "Test Scene"
        self.test_content = "This is a test scene content."
        self.test_metadata = {
            "location": "EXT. TEST LOCATION - DAY",
            "time_of_day": "DAY",
            "characters": ["TEST_CHARACTER_1", "TEST_CHARACTER_2"]
        }
    
    def teardown_method(self):
        """Clean up the temporary directory after testing."""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization_creates_directories(self):
        """Test that initialization creates the screen_plays directory."""
        assert self.manager.screen_plays_dir.exists()
        assert self.manager.screen_plays_dir.is_dir()
    
    def test_create_scene_success(self):
        """Test creating a new scene successfully."""
        result = self.manager.create_scene(
            self.test_scene_id,
            self.test_title,
            self.test_content,
            self.test_metadata
        )
        
        assert result is True
        
        # Verify the file was created
        scene_file_path = self.manager.screen_plays_dir / f"{self.test_scene_id}.md"
        assert scene_file_path.exists()
    
    def test_get_scene_exists(self):
        """Test retrieving an existing scene."""
        # Create a scene first
        self.manager.create_scene(
            self.test_scene_id,
            self.test_title,
            self.test_content,
            self.test_metadata
        )
        
        # Retrieve the scene
        scene = self.manager.get_scene(self.test_scene_id)
        
        assert scene is not None
        assert scene.scene_id == self.test_scene_id
        assert scene.title == self.test_title
        assert scene.content == self.test_content
        assert scene.metadata["location"] == self.test_metadata["location"]
    
    def test_get_scene_not_exists(self):
        """Test retrieving a non-existing scene."""
        scene = self.manager.get_scene("non_existing_scene")
        
        assert scene is None
    
    def test_update_scene_success(self):
        """Test updating an existing scene."""
        # Create a scene first
        self.manager.create_scene(
            self.test_scene_id,
            self.test_title,
            self.test_content,
            self.test_metadata
        )
        
        # Update the scene
        new_title = "Updated Test Scene"
        new_content = "This is updated test scene content."
        update_result = self.manager.update_scene(
            self.test_scene_id,
            title=new_title,
            content=new_content
        )
        
        assert update_result is True
        
        # Verify the update
        updated_scene = self.manager.get_scene(self.test_scene_id)
        assert updated_scene.title == new_title
        assert updated_scene.content == new_content
        
        # Check that the updated_at timestamp was updated
        assert updated_scene.metadata["updated_at"] != self.test_metadata.get("created_at")
    
    def test_update_scene_metadata_only(self):
        """Test updating only the metadata of a scene."""
        # Create a scene first
        self.manager.create_scene(
            self.test_scene_id,
            self.test_title,
            self.test_content,
            self.test_metadata
        )
        
        # Update only metadata
        metadata_updates = {"location": "INT. NEW LOCATION - NIGHT", "status": "revised"}
        update_result = self.manager.update_scene(
            self.test_scene_id,
            metadata_updates=metadata_updates
        )
        
        assert update_result is True
        
        # Verify the metadata update
        updated_scene = self.manager.get_scene(self.test_scene_id)
        assert updated_scene.metadata["location"] == "INT. NEW LOCATION - NIGHT"
        assert updated_scene.metadata["status"] == "revised"
        # Content should remain unchanged
        assert updated_scene.content == self.test_content
    
    def test_delete_scene_success(self):
        """Test deleting an existing scene."""
        # Create a scene first
        self.manager.create_scene(
            self.test_scene_id,
            self.test_title,
            self.test_content,
            self.test_metadata
        )
        
        # Verify it exists
        scene_before = self.manager.get_scene(self.test_scene_id)
        assert scene_before is not None
        
        # Delete the scene
        delete_result = self.manager.delete_scene(self.test_scene_id)
        
        assert delete_result is True
        
        # Verify it no longer exists
        scene_after = self.manager.get_scene(self.test_scene_id)
        assert scene_after is None
    
    def test_delete_scene_not_exists(self):
        """Test deleting a non-existing scene."""
        delete_result = self.manager.delete_scene("non_existing_scene")
        
        assert delete_result is False
    
    def test_list_scenes(self):
        """Test listing all scenes in the project."""
        # Create multiple scenes
        scenes_data = [
            {"id": "scene_001", "title": "Scene 1", "content": "Content 1"},
            {"id": "scene_002", "title": "Scene 2", "content": "Content 2"},
            {"id": "scene_003", "title": "Scene 3", "content": "Content 3"}
        ]
        
        for scene_data in scenes_data:
            self.manager.create_scene(
                scene_data["id"],
                scene_data["title"],
                scene_data["content"]
            )
        
        # List all scenes
        all_scenes = self.manager.list_scenes()
        
        assert len(all_scenes) == 3
        
        # Verify all scenes are present
        scene_ids = [scene.scene_id for scene in all_scenes]
        for scene_data in scenes_data:
            assert scene_data["id"] in scene_ids
    
    def test_get_scene_by_title(self):
        """Test getting a scene by its title."""
        # Create a scene
        self.manager.create_scene(
            self.test_scene_id,
            self.test_title,
            self.test_content,
            self.test_metadata
        )
        
        # Find the scene by title
        found_scene = self.manager.get_scene_by_title(self.test_title)
        
        assert found_scene is not None
        assert found_scene.scene_id == self.test_scene_id
        assert found_scene.title == self.test_title
    
    def test_get_scene_by_title_case_insensitive(self):
        """Test getting a scene by its title (case insensitive)."""
        # Create a scene
        self.manager.create_scene(
            self.test_scene_id,
            self.test_title,
            self.test_content,
            self.test_metadata
        )
        
        # Find the scene by title with different case
        found_scene = self.manager.get_scene_by_title(self.test_title.lower())
        
        assert found_scene is not None
        assert found_scene.scene_id == self.test_scene_id
        assert found_scene.title == self.test_title
    
    def test_get_scene_by_title_not_found(self):
        """Test getting a scene by a title that doesn't exist."""
        # Create a scene
        self.manager.create_scene(
            self.test_scene_id,
            self.test_title,
            self.test_content,
            self.test_metadata
        )
        
        # Try to find a scene with a non-existing title
        found_scene = self.manager.get_scene_by_title("Non Existing Title")
        
        assert found_scene is None
    
    def test_get_scene_metadata(self):
        """Test getting only the metadata of a scene."""
        # Create a scene
        self.manager.create_scene(
            self.test_scene_id,
            self.test_title,
            self.test_content,
            self.test_metadata
        )
        
        # Get only the metadata
        metadata = self.manager.get_scene_metadata(self.test_scene_id)
        
        assert metadata is not None
        assert metadata["location"] == self.test_metadata["location"]
        assert metadata["time_of_day"] == self.test_metadata["time_of_day"]
        assert metadata["characters"] == self.test_metadata["characters"]
    
    def test_get_scene_content(self):
        """Test getting only the content of a scene."""
        # Create a scene
        self.manager.create_scene(
            self.test_scene_id,
            self.test_title,
            self.test_content,
            self.test_metadata
        )
        
        # Get only the content
        content = self.manager.get_scene_content(self.test_scene_id)
        
        assert content == self.test_content
    
    def test_update_scene_metadata(self):
        """Test updating only the metadata of a scene."""
        # Create a scene
        self.manager.create_scene(
            self.test_scene_id,
            self.test_title,
            self.test_content,
            self.test_metadata
        )
        
        # Update only the metadata
        metadata_updates = {"location": "INT. NEW LOCATION - EVENING", "status": "final"}
        update_result = self.manager.update_scene_metadata(self.test_scene_id, metadata_updates)
        
        assert update_result is True
        
        # Verify the metadata was updated
        updated_scene = self.manager.get_scene(self.test_scene_id)
        assert updated_scene.metadata["location"] == "INT. NEW LOCATION - EVENING"
        assert updated_scene.metadata["status"] == "final"
        # Content should remain unchanged
        assert updated_scene.content == self.test_content
    
    def test_bulk_create_scenes(self):
        """Test creating multiple scenes in bulk."""
        scenes_data = [
            {
                "scene_id": "bulk_scene_001",
                "title": "Bulk Scene 1",
                "content": "Content for bulk scene 1",
                "metadata": {"location": "EXT. LOCATION 1 - DAY"}
            },
            {
                "scene_id": "bulk_scene_002",
                "title": "Bulk Scene 2",
                "content": "Content for bulk scene 2",
                "metadata": {"location": "INT. LOCATION 2 - NIGHT"}
            },
            {
                "scene_id": "bulk_scene_003",
                "title": "Bulk Scene 3",
                "content": "Content for bulk scene 3",
                "metadata": {"location": "EXT. LOCATION 3 - DAWN"}
            }
        ]
        
        results = self.manager.bulk_create_scenes(scenes_data)
        
        # Check that all creations were successful
        assert len(results) == 3
        for scene_id, success in results.items():
            assert success is True
            assert scene_id in [data["scene_id"] for data in scenes_data]
        
        # Verify all scenes were created
        all_scenes = self.manager.list_scenes()
        assert len(all_scenes) == 3
        
        # Verify each scene has correct data
        for scene_data in scenes_data:
            scene = self.manager.get_scene(scene_data["scene_id"])
            assert scene is not None
            assert scene.title == scene_data["title"]
            assert scene.content == scene_data["content"]
            assert scene.metadata["location"] == scene_data["metadata"]["location"]
    
    def test_get_scenes_by_character(self):
        """Test finding scenes by character name."""
        # Create scenes with different characters
        self.manager.create_scene(
            "scene_char_a",
            "Scene with Character A",
            "Content with Character A",
            {"characters": ["CHARACTER_A", "CHARACTER_B"]}
        )
        
        self.manager.create_scene(
            "scene_char_b",
            "Scene with Character B",
            "Content with Character B",
            {"characters": ["CHARACTER_B", "CHARACTER_C"]}
        )
        
        self.manager.create_scene(
            "scene_char_c",
            "Scene with Character C",
            "Content with Character C",
            {"characters": ["CHARACTER_C"]}
        )
        
        # Find scenes with CHARACTER_B
        scenes_with_char_b = self.manager.get_scenes_by_character("CHARACTER_B")
        
        assert len(scenes_with_char_b) == 2
        scene_ids = [scene.scene_id for scene in scenes_with_char_b]
        assert "scene_char_a" in scene_ids
        assert "scene_char_b" in scene_ids
    
    def test_get_scenes_by_location(self):
        """Test finding scenes by location."""
        # Create scenes with different locations
        self.manager.create_scene(
            "scene_loc_1",
            "Scene at Location 1",
            "Content at Location 1",
            {"location": "EXT. FOREST - DAY"}
        )
        
        self.manager.create_scene(
            "scene_loc_2",
            "Scene at Location 2",
            "Content at Location 2",
            {"location": "INT. HOUSE - NIGHT"}
        )
        
        self.manager.create_scene(
            "scene_loc_3",
            "Scene at Location 3",
            "Content at Location 3",
            {"location": "EXT. FOREST - DAWN"}
        )
        
        # Find scenes at forest location
        forest_scenes = self.manager.get_scenes_by_location("FOREST")
        
        assert len(forest_scenes) == 2
        scene_ids = [scene.scene_id for scene in forest_scenes]
        assert "scene_loc_1" in scene_ids
        assert "scene_loc_3" in scene_ids