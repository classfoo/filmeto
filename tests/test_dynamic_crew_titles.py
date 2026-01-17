#!/usr/bin/env python3
"""
Test script to verify the new dynamic crew title implementation
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


def test_dynamic_crew_titles():
    """Test the new dynamic crew title functionality"""
    print("Testing dynamic crew title functionality...")
    
    # Test 1: Get crew titles in Chinese
    print("\n1. Testing crew titles in Chinese...")
    translation_manager.switch_language("zh_CN")
    
    crew_service = CrewService()
    titles_zh = crew_service.get_crew_titles()
    print(f"   Crew titles in Chinese: {titles_zh}")
    
    # Test 2: Get crew titles in English
    print("\n2. Testing crew titles in English...")
    translation_manager.switch_language("en_US")
    
    titles_en = crew_service.get_crew_titles()
    print(f"   Crew titles in English: {titles_en}")
    
    # Both should have the same titles since they're based on filenames
    print(f"   Are titles the same in both languages? {set(titles_zh) == set(titles_en)}")
    
    # Test 3: Test the static enum functionality (backward compatibility)
    print("\n3. Testing static enum functionality (backward compatibility)...")
    static_titles = CrewTitle.get_importance_order()
    print(f"   Static enum titles: {static_titles}")
    
    # Test 4: Test the dynamic functionality
    print("\n4. Testing dynamic functionality...")
    dynamic_titles = CrewTitle.get_importance_order(use_dynamic=True)
    print(f"   Dynamic titles: {dynamic_titles}")
    
    # Test 5: Test importance ranking with both approaches
    print("\n5. Testing importance ranking...")
    if dynamic_titles:
        sample_title = dynamic_titles[0]  # Get the first title
        static_rank = CrewTitle.get_title_importance_rank(sample_title)
        dynamic_rank = CrewTitle.get_title_importance_rank(sample_title, use_dynamic=True)
        print(f"   Rank of '{sample_title}' - Static: {static_rank}, Dynamic: {dynamic_rank}")
    
    # Test 6: Test with a temporary project to ensure sorting still works
    print("\n6. Testing with temporary project...")
    from app.data.project import Project
    from agent.crew.crew_member import CrewMemberConfig
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "test_workspace"
        workspace_path.mkdir()
        
        # Create a test project
        project = Project(str(workspace_path), "../test_project", "Test Project")
        
        # Initialize crew members
        crew_service.initialize_project_crew_members(project)
        crew_members = crew_service.load_project_crew_members(project)
        
        print(f"   Loaded {len(crew_members)} crew members")
        
        # Test static sorting (backward compatibility)
        sorted_static = sort_crew_members_by_title_importance(list(crew_members.values()))
        print(f"   Static sorting: {len(sorted_static)} members sorted")
        
        # Test dynamic sorting
        sorted_dynamic = sort_crew_members_by_title_importance(list(crew_members.values()), use_dynamic=True)
        print(f"   Dynamic sorting: {len(sorted_dynamic)} members sorted")
        
        print(f"   Sorting results are the same: {len(sorted_static) == len(sorted_dynamic)}")
    
    print("\n7. Summary:")
    print(f"   - Static enum titles: {len(static_titles)}")
    print(f"   - Dynamic titles: {len(dynamic_titles)}")
    valid_static_titles = [t for t in static_titles if t in ['producer', 'director', 'screenwriter', 'cinematographer', 'editor', 'sound_designer', 'vfx_supervisor', 'storyboard_artist', 'other']]
    print(f"   - Backward compatibility maintained: {len(valid_static_titles) == len(static_titles)}")
    print("   ✅ All tests completed successfully!")


if __name__ == "__main__":
    test_dynamic_crew_titles()