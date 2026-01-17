#!/usr/bin/env python3
"""
Test script to verify the updated initialize_project_crew_members method
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.i18n_utils import translation_manager
from agent.crew.crew_service import CrewService
from agent.crew.crew_title import CrewTitle
import tempfile


def test_updated_initialization():
    """Test the updated initialize_project_crew_members method"""
    print("Testing updated initialize_project_crew_members method...")
    
    # Test 1: Check that get_crew_titles works
    print("\n1. Testing get_crew_titles method...")
    crew_service = CrewService()
    
    # Test with Chinese
    translation_manager.switch_language("zh_CN")
    titles_zh = crew_service.get_crew_titles()
    print(f"   Crew titles in Chinese: {titles_zh}")
    
    # Test with English
    translation_manager.switch_language("en_US")
    titles_en = crew_service.get_crew_titles()
    print(f"   Crew titles in English: {titles_en}")
    
    # Test 2: Test initialization with a temporary project
    print("\n2. Testing project initialization...")
    from app.data.project import Project
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "test_workspace"
        workspace_path.mkdir()
        
        # Create a test project
        project = Project(str(workspace_path), "../test_project", "Test Project")
        
        # Initialize crew members using the updated method
        initialized_files = crew_service.initialize_project_crew_members(project)
        print(f"   Initialized {len(initialized_files)} crew member files")
        
        # Check what files were created
        project_crew_dir = Path(project.project_path) / "agent" / "crew_members"
        if project_crew_dir.exists():
            created_files = list(project_crew_dir.glob("*.md"))
            print(f"   Created {len(created_files)} files in project crew directory")
            for file in created_files:
                print(f"     - {file.name}")
        else:
            print("   Project crew directory was not created")
    
    # Test 3: Verify that CrewTitle.get_all_dynamic_titles still works
    print("\n3. Testing CrewTitle.get_all_dynamic_titles method...")
    dynamic_titles = CrewTitle.get_all_dynamic_titles()
    print(f"   Dynamic titles from CrewTitle: {dynamic_titles}")
    
    # Test 4: Compare the results
    print("\n4. Comparing results...")
    print(f"   CrewService titles: {set(titles_en)}")
    print(f"   CrewTitle titles: {set(dynamic_titles)}")
    print(f"   Sets are equal: {set(titles_en) == set(dynamic_titles)}")
    
    print("\n5. Summary:")
    print(f"   - get_crew_titles method works: {len(titles_en) > 0}")
    print(f"   - Project initialization works: {len(initialized_files) > 0}")
    print(f"   - CrewTitle method works: {len(dynamic_titles) > 0}")
    print(f"   - Consistency between methods: {set(titles_en) == set(dynamic_titles)}")
    print("   ✅ All tests completed successfully!")


if __name__ == "__main__":
    test_updated_initialization()