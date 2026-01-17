#!/usr/bin/env python3
"""
Test script to verify crew member internationalization functionality in both languages
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.i18n_utils import translation_manager
from agent.crew.crew_service import CrewService
from app.data.project import Project
import tempfile


def test_both_languages():
    """Test crew member internationalization in both Chinese and English"""
    print("Testing crew member internationalization in both languages...")
    
    # Create a temporary workspace for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "test_workspace"
        workspace_path.mkdir()
        
        # Create a test project
        project = Project(str(workspace_path), "../test_project", "Test Project")
        
        # Test with Chinese language first
        print("\n1. Testing with Chinese language...")
        translation_manager.switch_language("zh_CN")
        
        # Initialize and load crew members
        crew_service = CrewService()
        crew_service.initialize_project_crew_members(project)
        crew_members_zh = crew_service.load_project_crew_members(project, refresh=True)
        
        print(f"   Loaded {len(crew_members_zh)} crew members in Chinese")
        
        # Print a sample crew member's description in Chinese
        if 'director' in crew_members_zh:
            director_desc_zh = crew_members_zh['director'].config.description
            print(f"   Director description in Chinese: {director_desc_zh}")
        
        # Test with English language
        print("\n2. Testing with English language...")
        translation_manager.switch_language("en_US")
        
        # Force refresh to reload with new language
        crew_members_en = crew_service.load_project_crew_members(project, refresh=True)
        
        print(f"   Loaded {len(crew_members_en)} crew members in English")
        
        # Print a sample crew member's description in English
        if 'director' in crew_members_en:
            director_desc_en = crew_members_en['director'].config.description
            print(f"   Director description in English: {director_desc_en}")
        
        # Verify that the descriptions are different (indicating successful i18n)
        director_zh = crew_members_zh.get('director')
        director_en = crew_members_en.get('director')
        
        zh_desc = director_zh.config.description if director_zh else ""
        en_desc = director_en.config.description if director_en else ""
        
        print(f"\n3. Verification:")
        print(f"   Chinese description: {zh_desc}")
        print(f"   English description: {en_desc}")
        
        if zh_desc != en_desc and zh_desc and en_desc:
            print("   ✅ SUCCESS: Descriptions differ between languages, i18n is working!")
        else:
            print("   ❌ FAILURE: Descriptions are the same or empty, i18n may not be working correctly")
        
        # Test language switching again to ensure it works both ways
        print("\n4. Testing language switch back to Chinese...")
        translation_manager.switch_language("zh_CN")
        crew_members_zh2 = crew_service.load_project_crew_members(project, refresh=True)
        
        if 'director' in crew_members_zh2:
            director_desc2 = crew_members_zh2['director'].config.description
            print(f"   Director description after switching back to Chinese: {director_desc2}")
            
            if director_desc2 == zh_desc:
                print("   ✅ SUCCESS: Language switching works correctly!")
            else:
                print("   ❌ FAILURE: Language switching didn't restore the correct language")
        
        print("\n5. Summary:")
        print(f"   Current language: {translation_manager.get_current_language()}")
        print(f"   Available languages: {list(translation_manager.get_available_languages().keys())}")


if __name__ == "__main__":
    test_both_languages()