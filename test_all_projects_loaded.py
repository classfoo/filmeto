#!/usr/bin/env python
"""
Test script to verify that all projects in the projects directory are loaded properly.
"""
import os
import tempfile
from app.data.workspace import Workspace
from app.data.project import ProjectManager

def test_all_projects_loaded():
    """Test that all projects in the projects directory are loaded properly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        
        # Create a few test projects manually
        projects_dir = os.path.join(temp_dir, "projects")
        os.makedirs(projects_dir, exist_ok=True)
        
        # Create project 1
        project1_dir = os.path.join(projects_dir, "project1")
        os.makedirs(project1_dir, exist_ok=True)
        # Create project config
        from utils.yaml_utils import save_yaml
        project1_config = {
            "project_name": "project1",
            "created_at": "2023-01-01T00:00:00",
            "timeline_index": 0,
            "timeline_position": 0.0,
            "timeline_duration": 0.0,
            "timeline_item_durations": {}
        }
        save_yaml(os.path.join(project1_dir, "project.yml"), project1_config)
        os.makedirs(os.path.join(project1_dir, "timeline"), exist_ok=True)
        os.makedirs(os.path.join(project1_dir, "prompts"), exist_ok=True)
        
        # Create project 2
        project2_dir = os.path.join(projects_dir, "project2")
        os.makedirs(project2_dir, exist_ok=True)
        # Create project config
        project2_config = {
            "project_name": "project2",
            "created_at": "2023-01-01T00:00:00",
            "timeline_index": 0,
            "timeline_position": 0.0,
            "timeline_duration": 0.0,
            "timeline_item_durations": {}
        }
        save_yaml(os.path.join(project2_dir, "project.yml"), project2_config)
        os.makedirs(os.path.join(project2_dir, "timeline"), exist_ok=True)
        os.makedirs(os.path.join(project2_dir, "prompts"), exist_ok=True)
        
        # Create project 3
        project3_dir = os.path.join(projects_dir, "project3")
        os.makedirs(project3_dir, exist_ok=True)
        # Create project config
        project3_config = {
            "project_name": "project3",
            "created_at": "2023-01-01T00:00:00",
            "timeline_index": 0,
            "timeline_position": 0.0,
            "timeline_duration": 0.0,
            "timeline_item_durations": {}
        }
        save_yaml(os.path.join(project3_dir, "project.yml"), project3_config)
        os.makedirs(os.path.join(project3_dir, "timeline"), exist_ok=True)
        os.makedirs(os.path.join(project3_dir, "prompts"), exist_ok=True)
        
        print(f"Created test projects: project1, project2, project3")
        
        # Test 1: Initialize ProjectManager with defer_scan=True and check if list_projects loads them
        print("\n=== Test 1: ProjectManager with defer_scan=True ===")
        project_manager = ProjectManager(temp_dir, defer_scan=True)
        
        # Initially, projects shouldn't be loaded
        initial_projects = project_manager.list_projects()
        print(f"Projects found: {initial_projects}")
        
        expected_projects = ["project1", "project2", "project3"]
        for proj in expected_projects:
            assert proj in initial_projects, f"Project {proj} not found in list: {initial_projects}"
        
        print("✅ All projects loaded correctly!")
        
        # Test 2: Initialize Workspace with defer_heavy_init=True and check project listing
        print("\n=== Test 2: Workspace with defer_heavy_init=True ===")
        workspace = Workspace(temp_dir, "project1", load_data=False, defer_heavy_init=True)
        
        workspace_projects = workspace.project_manager.list_projects()
        print(f"Workspace projects found: {workspace_projects}")
        
        for proj in expected_projects:
            assert proj in workspace_projects, f"Project {proj} not found in workspace: {workspace_projects}"
        
        print("✅ Workspace correctly lists all projects!")
        
        print("\n🎉 All tests passed! All projects in the projects directory are loaded properly.")

if __name__ == "__main__":
    test_all_projects_loaded()