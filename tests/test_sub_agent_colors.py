"""
Test script to verify that crew color configurations are applied correctly
"""
import tempfile
from pathlib import Path
from agent.crew.crew_service import CrewService
from app.data.project import Project
from app.data.workspace import Workspace


def test_sub_agent_colors():
    """Test that crew colors are correctly loaded from configuration"""
    print("Testing crew color configurations...")
    
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
        
        # Define expected colors for each crew
        expected_colors = {
            "director": "#4a90e2",
            "cinematographer": "#ff6347",
            "editor": "#ffa500",
            "producer": "#7b68ee",
            "screenwriter": "#32cd32",
            "sound_designer": "#9370db",
            "storyboard_artist": "#ff69b4",
            "vfx_supervisor": "#00ced1"
        }
        
        all_correct = True
        for agent_name, agent_metadata in metadata.items():
            color = agent_metadata.get('color', 'NOT_FOUND')
            expected_color = expected_colors.get(agent_name, 'UNDEFINED')
            
            status = "✅" if color == expected_color else "❌"
            print(f"  {status} {agent_name}: {color} (expected: {expected_color})")
            
            if color != expected_color:
                all_correct = False
        
        # Check if all expected agents are present
        for agent_name, expected_color in expected_colors.items():
            if agent_name not in metadata:
                print(f"  ❌ Missing agent: {agent_name}")
                all_correct = False
        
        if all_correct:
            print("\n🎉 All crew color configurations are correct!")
            return True
        else:
            print("\n❌ Some crew color configurations are incorrect!")
            return False


if __name__ == "__main__":
    success = test_sub_agent_colors()
    if success:
        print("\n✅ Test passed!")
    else:
        print("\n❌ Test failed!")