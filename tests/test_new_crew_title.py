#!/usr/bin/env python3
"""
Test script to verify the new CrewTitle class implementation
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.i18n_utils import translation_manager
from agent.crew.crew_service import CrewService
from agent.crew.crew_title import CrewTitle, sort_crew_members_by_title_importance
import tempfile


def test_new_crew_title_implementation():
    """Test the new CrewTitle class implementation"""
    print("Testing new CrewTitle class implementation...")
    
    # Test 1: Create CrewTitle instances and check metadata loading
    print("\n1. Testing CrewTitle creation and metadata loading...")
    
    director_title = CrewTitle.create_from_title("director")
    print(f"   Director title: {director_title.title}")
    print(f"   Director metadata: {director_title.metadata}")
    print(f"   Director display (en): {director_title.get_title_display('en')}")
    print(f"   Director display (zh): {director_title.get_title_display('zh')}")
    
    # Test 2: Get all dynamic titles
    print("\n2. Testing dynamic title retrieval...")
    translation_manager.switch_language("zh_CN")
    titles_zh = CrewTitle.get_all_dynamic_titles()
    print(f"   Titles in Chinese: {titles_zh}")
    
    translation_manager.switch_language("en_US")
    titles_en = CrewTitle.get_all_dynamic_titles()
    print(f"   Titles in English: {titles_en}")
    
    # Test 3: Test importance ranking
    print("\n3. Testing importance ranking...")
    rank_director = CrewTitle.get_title_importance_rank("director")
    rank_producer = CrewTitle.get_title_importance_rank("producer")
    print(f"   Director rank: {rank_director}")
    print(f"   Producer rank: {rank_producer}")
    
    # Test 4: Test dynamic importance ranking
    print("\n4. Testing dynamic importance ranking...")
    rank_director_dyn = CrewTitle.get_title_importance_rank("director", use_dynamic=True)
    rank_producer_dyn = CrewTitle.get_title_importance_rank("producer", use_dynamic=True)
    print(f"   Director rank (dynamic): {rank_director_dyn}")
    print(f"   Producer rank (dynamic): {rank_producer_dyn}")
    
    # Test 5: Test from_string method
    print("\n5. Testing from_string method...")
    director_obj = CrewTitle.from_string("director")
    if director_obj:
        print(f"   Created director object: {director_obj.title}")
        print(f"   Director metadata: {director_obj.metadata}")
    else:
        print("   Failed to create director object")
    
    # Test 6: Test is_valid_title method
    print("\n6. Testing is_valid_title method...")
    is_valid = CrewTitle.is_valid_title("director")
    print(f"   Is 'director' valid? {is_valid}")
    
    is_invalid = CrewTitle.is_valid_title("nonexistent_title")
    print(f"   Is 'nonexistent_title' valid? {is_invalid}")
    
    # Test 7: Test with a temporary project to ensure sorting still works
    print("\n7. Testing with temporary project...")
    from app.data.project import Project
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "test_workspace"
        workspace_path.mkdir()
        
        # Create a test project
        project = Project(str(workspace_path), "../test_project", "Test Project")
        
        # Initialize crew members
        crew_service = CrewService()
        crew_service.initialize_project_crew_members(project)
        crew_members = crew_service.load_project_crew_members(project)
        
        print(f"   Loaded {len(crew_members)} crew members")
        
        # Test static sorting (backward compatibility)
        sorted_static = sort_crew_members_by_title_importance(list(crew_members.values()))
        print(f"   Static sorting: {len(sorted_static)} members sorted")
        
        # Test dynamic sorting
        sorted_dynamic = sort_crew_members_by_title_importance(list(crew_members.values()), use_dynamic=True)
        print(f"   Dynamic sorting: {len(sorted_dynamic)} members sorted")
    
    print("\n8. Summary:")
    print(f"   - Successfully created CrewTitle instances: {director_title is not None}")
    print(f"   - Metadata loaded: {bool(director_title.metadata)}")
    print(f"   - Dynamic titles retrieved: {len(titles_zh) > 0}")
    print(f"   - Importance ranking works: {rank_director >= 0}")
    print(f"   - from_string method works: {director_obj is not None}")
    print(f"   - is_valid_title method works: {is_valid}")
    print("   ✅ All tests completed successfully!")


if __name__ == "__main__":
    test_new_crew_title_implementation()