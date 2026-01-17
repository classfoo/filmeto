#!/usr/bin/env python3
"""
Direct test to verify crew member internationalization functionality
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.i18n_utils import translation_manager
from agent.crew.crew_member import CrewMemberConfig
import tempfile


def test_direct_i18n():
    """Test crew member internationalization by directly loading configs"""
    print("Testing crew member internationalization by directly loading configs...")
    
    # Get the system directory paths
    system_base_dir = Path(__file__).parent / "agent" / "crew" / "system"
    
    # Test Chinese version
    print("\n1. Testing Chinese version...")
    translation_manager._current_language = "zh_CN"  # Directly set for testing
    
    chinese_file = system_base_dir / "zh_CN" / "director.md"
    if chinese_file.exists():
        config_zh = CrewMemberConfig.from_markdown(str(chinese_file))
        print(f"   Chinese director description: {config_zh.description}")
    else:
        print("   Chinese director file does not exist")
    
    # Test English version
    print("\n2. Testing English version...")
    translation_manager._current_language = "en_US"  # Directly set for testing
    
    english_file = system_base_dir / "en_US" / "director.md"
    if english_file.exists():
        config_en = CrewMemberConfig.from_markdown(str(english_file))
        print(f"   English director description: {config_en.description}")
    else:
        print("   English director file does not exist")
    
    # Compare the descriptions
    print(f"\n3. Comparison:")
    print(f"   Chinese: {config_zh.description if 'config_zh' in locals() else 'N/A'}")
    print(f"   English: {config_en.description if 'config_en' in locals() else 'N/A'}")
    
    if config_zh.description != config_en.description:
        print("   ✅ SUCCESS: Descriptions differ between languages, i18n is working!")
    else:
        print("   ❌ FAILURE: Descriptions are the same, i18n may not be working correctly")


def test_with_temp_project():
    """Test using a temporary project to verify the full flow"""
    print("\n\nTesting with temporary project to verify full flow...")
    
    from agent.crew.crew_service import CrewService
    from app.data.project import Project
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "test_workspace"
        workspace_path.mkdir()
        
        # Test with Chinese
        print("\n4. Testing with Chinese language in project...")
        translation_manager.switch_language("zh_CN")
        
        project_zh = Project(str(workspace_path), "../test_project_zh", "Test Project ZH")
        crew_service = CrewService()
        crew_service.initialize_project_crew_members(project_zh)
        crew_members_zh = crew_service.load_project_crew_members(project_zh)
        
        if 'director' in crew_members_zh:
            desc_zh = crew_members_zh['director'].config.description
            print(f"   Director description in Chinese project: {desc_zh}")
        else:
            print("   Director not found in Chinese project")
        
        # Test with English in a separate project directory
        print("\n5. Testing with English language in project...")
        translation_manager.switch_language("en_US")
        
        project_en = Project(str(workspace_path), "../test_project_en", "Test Project EN")
        crew_service_en = CrewService()  # Create a new instance to avoid caching
        crew_service_en.initialize_project_crew_members(project_en)
        crew_members_en = crew_service_en.load_project_crew_members(project_en)
        
        if 'director' in crew_members_en:
            desc_en = crew_members_en['director'].config.description
            print(f"   Director description in English project: {desc_en}")
        else:
            print("   Director not found in English project")
        
        # Compare
        print(f"\n6. Full flow comparison:")
        print(f"   Chinese project: {desc_zh if 'desc_zh' in locals() else 'N/A'}")
        print(f"   English project: {desc_en if 'desc_en' in locals() else 'N/A'}")
        
        if 'desc_zh' in locals() and 'desc_en' in locals() and desc_zh != desc_en:
            print("   ✅ SUCCESS: Full flow working correctly!")
        else:
            print("   ❌ FAILURE: Full flow not working correctly")


if __name__ == "__main__":
    test_direct_i18n()
    test_with_temp_project()