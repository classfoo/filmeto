#!/usr/bin/env python3
"""
Check what crew member names are being used in the project
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


def check_crew_names():
    """Check what names are being used for crew members in the project"""
    print("Checking crew member names in project...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "test_workspace"
        workspace_path.mkdir()
        
        # Test with Chinese
        print("\n1. Testing with Chinese language...")
        translation_manager.switch_language("zh_CN")
        
        project_zh = Project(str(workspace_path), "test_project_zh", "Test Project ZH")
        crew_service = CrewService()
        crew_service.initialize_project_crew_members(project_zh)
        
        # Check what files were created
        project_crew_dir = Path(project_zh.project_path) / "agent" / "crew_members"
        print(f"   Files in Chinese project crew directory:")
        for file in project_crew_dir.glob("*.md"):
            print(f"     {file.name}")
            
            # Read the name from the file
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.startswith('---'):
                    end_idx = content.find('---', 3)
                    if end_idx != -1:
                        yaml_part = content[3:end_idx].strip()
                        import yaml
                        try:
                            metadata = yaml.safe_load(yaml_part)
                            name = metadata.get('name', 'unknown')
                            crew_title = metadata.get('crew_title', 'unknown')
                            description = metadata.get('description', 'no description')
                            print(f"       - name: {name}")
                            print(f"       - crew_title: {crew_title}")
                            print(f"       - description: {description[:50]}...")
                        except:
                            print(f"       - Could not parse YAML")
        
        crew_members_zh = crew_service.load_project_crew_members(project_zh)
        print(f"   Loaded {len(crew_members_zh)} crew members in Chinese project")
        for name, member in crew_members_zh.items():
            print(f"     {name}: {member.config.description[:50]}...")
        
        # Test with English
        print("\n2. Testing with English language...")
        translation_manager.switch_language("en_US")
        
        project_en = Project(str(workspace_path), "test_project_en", "Test Project EN")
        crew_service_en = CrewService()
        crew_service_en.initialize_project_crew_members(project_en)
        
        # Check what files were created
        project_crew_dir_en = Path(project_en.project_path) / "agent" / "crew_members"
        print(f"   Files in English project crew directory:")
        for file in project_crew_dir_en.glob("*.md"):
            print(f"     {file.name}")
            
            # Read the name from the file
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.startswith('---'):
                    end_idx = content.find('---', 3)
                    if end_idx != -1:
                        yaml_part = content[3:end_idx].strip()
                        import yaml
                        try:
                            metadata = yaml.safe_load(yaml_part)
                            name = metadata.get('name', 'unknown')
                            crew_title = metadata.get('crew_title', 'unknown')
                            description = metadata.get('description', 'no description')
                            print(f"       - name: {name}")
                            print(f"       - crew_title: {crew_title}")
                            print(f"       - description: {description[:50]}...")
                        except:
                            print(f"       - Could not parse YAML")
        
        crew_members_en = crew_service_en.load_project_crew_members(project_en)
        print(f"   Loaded {len(crew_members_en)} crew members in English project")
        for name, member in crew_members_en.items():
            print(f"     {name}: {member.config.description[:50]}...")


if __name__ == "__main__":
    check_crew_names()