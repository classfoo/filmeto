#!/usr/bin/env python3
"""
Debug script to check crew member internationalization functionality
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
import shutil


def debug_crew_i18n():
    """Debug crew member internationalization functionality"""
    print("Debugging crew member internationalization...")
    
    # Check current language
    current_lang = translation_manager.get_current_language()
    print(f"Current language: {current_lang}")
    
    # Show the content of language-specific files
    system_dir = Path(__file__).parent / "agent" / "crew" / "system"
    
    print(f"\nContents of {system_dir / 'zh_CN' / 'director.md'}:")
    if (system_dir / "zh_CN" / "director.md").exists():
        with open(system_dir / "zh_CN" / "director.md", 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print("File does not exist")
    
    print(f"\nContents of {system_dir / 'en_US' / 'director.md'}:")
    if (system_dir / "en_US" / "director.md").exists():
        with open(system_dir / "en_US" / "director.md", 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print("File does not exist")
    
    # Create a temporary workspace for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "test_workspace"
        workspace_path.mkdir()
        
        # Create a test project
        project = Project(str(workspace_path), "test_project", "Test Project")
        
        # Initialize crew members
        crew_service = CrewService()
        crew_service.initialize_project_crew_members(project)
        
        # Check what files were created in the project
        project_crew_dir = Path(project.project_path) / "agent" / "crew_members"
        print(f"\nFiles in project crew directory {project_crew_dir}:")
        if project_crew_dir.exists():
            for file in project_crew_dir.glob("*.md"):
                print(f"  {file.name}")
                
                # Read and print the content
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"    Content preview: {content[:100]}...")
        else:
            print("  Directory does not exist")
        
        # Load crew members
        crew_members = crew_service.load_project_crew_members(project)
        print(f"\nLoaded {len(crew_members)} crew members")
        
        for name, member in crew_members.items():
            print(f"  {name}: description='{member.config.description}'")


if __name__ == "__main__":
    debug_crew_i18n()