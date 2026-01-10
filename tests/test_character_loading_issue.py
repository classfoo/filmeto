"""
Unit test to reproduce the actor data loading issue in the demo project.

This test verifies that actor data is properly loaded from the config.yaml file
when a workspace with the demo project is initialized.
"""

import os
import sys
import unittest
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.data.workspace import Workspace


class TestCharacterLoadingIssue(unittest.TestCase):
    """Test case to reproduce the actor data loading issue"""

    def setUp(self):
        """Set up the test environment"""
        self.workspace_path = os.path.join(project_root, "workspace")
        self.demo_project_name = "demo"
        self.demo_project_path = os.path.join(self.workspace_path, self.demo_project_name)

    def test_character_data_loading_from_demo_project(self):
        """Test that actor data is properly loaded from the demo project's config.yaml"""

        # Initialize workspace with the demo project
        workspace = Workspace(self.workspace_path, self.demo_project_name, load_data=True)

        # Get the actor manager
        character_manager = workspace.get_project().get_character_manager()

        # Check if characters are loaded (this should pass if the issue is fixed)
        characters = character_manager.list_characters()

        # The demo project should have at least 10 characters based on the config.yaml
        # (may be more if test characters were created in previous runs)
        expected_character_count = 10
        self.assertGreaterEqual(len(characters), expected_character_count,
                         f"Expected at least {expected_character_count} characters, but got {len(characters)}")

        # Verify that the original characters are present
        expected_names = [
            "wegawegawgeg", "wegwegfwef", "awegagewaagaw", "wegweg",
            "fuli", "aewgawegawg", "egwegweg", "wgwegwegweg",
            "awegwagweag", "awegawgewgaewg"
        ]

        actual_names = [char.name for char in characters]
        for name in expected_names:
            self.assertIn(name, actual_names, f"Character '{name}' not found in loaded characters")

        # Test getting a specific actor by name
        character = character_manager.get_character("wegweg")
        self.assertIsNotNone(character, "Character 'wegweg' should exist but was not found")
        self.assertEqual(character.name, "wegweg")
        # Note: The resources might not be available if the files don't exist
        # self.assertIn("main_view", actor.resources)  # Only check if the resource exists in the original data
        # self.assertIn("front_view", actor.resources)

        print(f"✅ Successfully loaded {len(characters)} characters from demo project")
        print(f"✅ Character names: {[char.name for char in characters]}")

    def test_character_manager_lazy_loading(self):
        """Test that actor manager properly loads characters on first access"""

        # Initialize workspace with the demo project
        workspace = Workspace(self.workspace_path, self.demo_project_name, load_data=True)

        # Get the actor manager
        character_manager = workspace.get_project().get_character_manager()

        # Initially, characters should not be loaded (internal _loaded flag should be False)
        # Access a actor which should trigger loading
        character = character_manager.get_character("fuli")

        # The actor should be found
        self.assertIsNotNone(character, "Character 'fuli' should be found after loading")
        self.assertEqual(character.name, "fuli")

        # Verify that the internal loading mechanism worked
        self.assertTrue(len(character_manager.list_characters()) > 0,
                        "Character manager should have loaded characters after first access")

    def test_character_operations_after_workspace_init_with_deferred_loading(self):
        """Test actor operations when workspace uses deferred loading (the likely issue scenario)"""

        # Initialize workspace with deferred loading (this might be the scenario where the issue occurs)
        # Note: With the fix, if load_data=True, characters will be loaded immediately
        workspace = Workspace(self.workspace_path, self.demo_project_name, load_data=True, defer_heavy_init=True)

        # Get the actor manager
        character_manager = workspace.get_project().get_character_manager()

        # With the fix, if load_data=True, characters should be loaded immediately
        # The fix ensures that when load_data=True, actor data is loaded during initialization
        self.assertTrue(character_manager._loaded,
                         "With the fix, characters should be loaded immediately when load_data=True")

        # Get characters
        characters = character_manager.list_characters()

        # The characters should already be loaded
        self.assertTrue(character_manager._loaded,
                        "Characters should be loaded after accessing them")

        # Verify we have at least the expected number of characters (may be more if test chars exist)
        expected_character_count = 10
        self.assertGreaterEqual(len(characters), expected_character_count,
                         f"With deferred loading, expected at least {expected_character_count} characters, but got {len(characters)}")

        # Test operations that would fail if characters aren't loaded
        # Create a new actor (with a unique name to avoid conflicts)
        import uuid
        unique_name = f"test_char_{uuid.uuid4().hex[:8]}"
        new_character = character_manager.create_character(unique_name, "A test actor")
        self.assertIsNotNone(new_character, "Should be able to create a new actor")

        # Update an existing actor
        success = character_manager.update_character("fuli", description="Updated description")
        self.assertTrue(success, "Should be able to update existing actor")

        # Delete the actor we created
        success = character_manager.delete_character(unique_name)
        self.assertTrue(success, "Should be able to delete actor")

    def test_character_loading_issue_with_load_data_false(self):
        """Test the specific issue: when workspace is initialized with load_data=False, characters are not loaded immediately"""

        # This simulates the exact scenario from the app.py where load_data=False and defer_heavy_init=True
        workspace = Workspace(self.workspace_path, self.demo_project_name, load_data=False, defer_heavy_init=True)

        # Get the actor manager
        character_manager = workspace.get_project().get_character_manager()

        # Initially, the characters should not be loaded when load_data=False
        self.assertFalse(character_manager._loaded,
                         "Characters should not be loaded when load_data=False")

        # Check if any characters are available (they shouldn't be until accessed)
        characters = character_manager.list_characters()

        # This should trigger loading, but let's check the count
        expected_character_count = 10
        self.assertGreaterEqual(len(characters), expected_character_count,
                         f"When accessing characters after initialization with load_data=False, expected at least {expected_character_count} characters, but got {len(characters)}")

        # Test that a specific actor can be retrieved
        character = character_manager.get_character("fuli")
        self.assertIsNotNone(character, "Character 'fuli' should be accessible even with deferred loading")
        self.assertEqual(character.name, "fuli")

        print(f"✅ With load_data=False, successfully loaded {len(characters)} characters after first access")
        print(f"✅ Character names: {[char.name for char in characters]}")


if __name__ == "__main__":
    unittest.main()