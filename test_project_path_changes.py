#!/usr/bin/env python
"""
Test script to verify that project path changes work correctly.
This script tests creating a workspace and project with the new path structure.
"""
import os
import tempfile
import shutil
from app.data.workspace import Workspace

def test_project_path_structure():
    """Test that projects are created and stored in the projects subdirectory."""
    # Create a temporary workspace directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        
        # Create a workspace with a test project
        workspace_path = temp_dir
        project_name = "test_project"
        
        print(f"Creating workspace with project: {project_name}")
        workspace = Workspace(workspace_path, project_name, load_data=True)
        
        # Check that the project was created in the correct location
        expected_project_path = os.path.join(workspace_path, "projects", project_name)
        print(f"Expected project path: {expected_project_path}")
        print(f"Actual project path: {workspace.project_path}")
        
        # Verify the project path is correct
        assert workspace.project_path == expected_project_path, f"Project path mismatch: expected {expected_project_path}, got {workspace.project_path}"
        
        # Verify that the project directory exists
        assert os.path.exists(expected_project_path), f"Project directory does not exist: {expected_project_path}"
        
        # Verify that the project.yaml file exists
        project_config_path = os.path.join(expected_project_path, "project.yaml")
        assert os.path.exists(project_config_path), f"Project config does not exist: {project_config_path}"
        
        # Test creating another project to ensure ProjectManager works correctly
        project_name2 = "test_project_2"
        print(f"Creating second project: {project_name2}")
        workspace.project_manager.create_project(project_name2)
        
        expected_project_path2 = os.path.join(workspace_path, "projects", project_name2)
        assert os.path.exists(expected_project_path2), f"Second project directory does not exist: {expected_project_path2}"
        
        # Test switching between projects
        print(f"Switching to project: {project_name2}")
        workspace.switch_project(project_name2)
        assert workspace.project_name == project_name2, f"Project switch failed: expected {project_name2}, got {workspace.project_name}"
        assert workspace.project_path == expected_project_path2, f"Project path after switch mismatch: expected {expected_project_path2}, got {workspace.project_path}"
        
        # Switch back to first project
        print(f"Switching back to project: {project_name}")
        workspace.switch_project(project_name)
        assert workspace.project_name == project_name, f"Project switch back failed: expected {project_name}, got {workspace.project_name}"
        assert workspace.project_path == expected_project_path, f"Project path after switch back mismatch: expected {expected_project_path}, got {workspace.project_path}"
        
        print("✅ All tests passed! Project path structure is working correctly.")

if __name__ == "__main__":
    test_project_path_structure()