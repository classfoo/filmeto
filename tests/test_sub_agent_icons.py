"""
Test script to verify that crew icons are displayed correctly
"""
import tempfile
from pathlib import Path
from agent.crew.crew_service import CrewService
from app.data.project import Project
from app.data.workspace import Workspace


def test_sub_agent_icons():
    """Test that crew icons are correctly loaded from configuration"""
    print("Testing crew icon configurations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create workspace
        workspace = Workspace(workspace_path=temp_dir, project_name="test_project")
        
        # Create project directory structure
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
        (project_path / "agent" / "sub_agents").mkdir()
        
        # Create project instance
        project = Project(workspace, str(project_path), "test_project")
        
        # Initialize crew service
        sub_agent_service = CrewService()
        
        # Load crew metadata
        metadata = sub_agent_service.get_project_sub_agent_metadata(project)
        
        print(f"Loaded metadata for {len(metadata)} sub_agents:")
        
        # Define expected icons for each crew
        expected_icons = {
            "director": "🎬",
            "cinematographer": "📷",
            "editor": "✂️",
            "producer": "💼",
            "screenwriter": "✍️",
            "sound_designer": "🎵",
            "storyboard_artist": "🎨",
            "vfx_supervisor": "✨"
        }
        
        all_correct = True
        for agent_name, agent_metadata in metadata.items():
            icon = agent_metadata.get('icon', 'NOT_FOUND')
            expected_icon = expected_icons.get(agent_name, 'UNDEFINED')
            
            status = "✅" if icon == expected_icon else "❌"
            print(f"  {status} {agent_name}: {icon} (expected: {expected_icon})")
            
            if icon != expected_icon:
                all_correct = False
        
        # Check if all expected agents are present
        for agent_name, expected_icon in expected_icons.items():
            if agent_name not in metadata:
                print(f"  ❌ Missing agent: {agent_name}")
                all_correct = False
        
        if all_correct:
            print("\n🎉 All crew icon configurations are correct!")
            return True
        else:
            print("\n❌ Some crew icon configurations are incorrect!")
            return False


if __name__ == "__main__":
    success = test_sub_agent_icons()
    if success:
        print("\n✅ Icon configuration test passed!")
    else:
        print("\n❌ Icon configuration test failed!")