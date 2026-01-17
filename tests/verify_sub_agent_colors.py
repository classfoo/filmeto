"""
Quick verification script to confirm all crew colors are working
"""
import tempfile
from pathlib import Path
from agent.crew.crew_service import CrewService
from app.data.project import Project
from app.data.workspace import Workspace


def verify_all_colors():
    """Verify that all crew colors are correctly configured"""
    print("Verifying all crew color configurations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create workspace and project
        workspace = Workspace(workspace_path=temp_dir, project_name="test_project")
        
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        
        # Create basic project structure
        (project_path / "project.yml").write_text("{}")
        (project_path / "timeline").mkdir()
        (project_path / "prompts").mkdir()
        (project_path / "resources").mkdir()
        (project_path / "characters").mkdir()
        (project_path / "agent").mkdir()
        (project_path / "agent" / "conversations").mkdir()
        (project_path / "agent" / "crew_members").mkdir()
        
        project = Project(workspace, str(project_path), "test_project")
        
        # Initialize crew_members
        crew_member_service = CrewService()
        crew_member_service.initialize_project_crew_members(project)
        
        # Get metadata
        metadata = crew_member_service.get_project_crew_member_metadata(project)
        
        print(f"\nFound {len(metadata)} crew_members with color configurations:")
        
        # Print each agent and its color
        for agent_name, agent_data in metadata.items():
            color = agent_data.get('color', 'NO_COLOR_DEFINED')
            print(f"  - {agent_name}: {color}")
        
        # Verify that all expected agents have colors
        expected_agents = [
            "director", "cinematographer", "editor", "producer", 
            "screenwriter", "sound_designer", "storyboard_artist", "vfx_supervisor"
        ]
        
        all_have_colors = True
        for agent in expected_agents:
            if agent not in metadata or 'color' not in metadata[agent]:
                print(f"  ❌ Missing color for {agent}")
                all_have_colors = False
            else:
                print(f"  ✅ {agent} has color: {metadata[agent]['color']}")
        
        if all_have_colors and len(metadata) >= len(expected_agents):
            print(f"\n🎉 Success! All {len(expected_agents)} crew_members have color configurations.")
            print("Colors are properly loaded from the configuration files and will be displayed in the UI.")
            return True
        else:
            print(f"\n❌ Issue detected: Expected {len(expected_agents)} agents, found {len(metadata)}")
            return False


if __name__ == "__main__":
    success = verify_all_colors()
    if success:
        print("\n✅ Verification completed successfully!")
    else:
        print("\n❌ Verification failed!")