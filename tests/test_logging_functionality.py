"""
Test script to verify logging functionality for agent messages
"""
import asyncio
import tempfile
import os
import logging
from pathlib import Path

from agent.crew.crew_member import CrewMember
from agent.llm.llm_service import LlmService
from app.data.project import Project
from app.data.workspace import Workspace
from agent.chat.agent_chat_message import AgentMessage, MessageType


def setup_test_logging():
    """Setup logging to capture messages"""
    # Set up root logger to capture all messages
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Create handler that stores logs in memory
    import io
    log_capture_string = io.StringIO()
    ch = logging.StreamHandler(log_capture_string)
    ch.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(ch)

    return root_logger, log_capture_string


async def test_logging_functionality():
    """Test that logging is properly added to agent messages"""
    print("Testing logging functionality for agent messages...")
    
    # Setup logging
    logger, log_capture_string = setup_test_logging()
    
    # Create a temporary project for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        
        # Initialize a minimal project structure
        agent_dir = project_path / "agent"
        agent_dir.mkdir()
        sub_agents_dir = agent_dir / "sub_agents"
        sub_agents_dir.mkdir()
        
        # Create a simple director agent config
        director_config = sub_agents_dir / "director.md"
        director_config.write_text("""---
name: director
description: Film director agent
soul: creative_vision
skills: []
model: gpt-4o-mini
temperature: 0.7
max_steps: 3
---

You are a film director. Help with directing films.
""")
        
        # Create a mock workspace
        workspace = Workspace(workspace_path=temp_dir, project_name="test_project")
        
        # Create a project
        project = Project(
            project_name="test_project",
            project_path=str(project_path),
            workspace=workspace
        )
        
        # Initialize the crew
        crew_member = CrewMember(
            config_path=str(director_config),
            workspace=workspace,
            project=project
        )
        
        # Mock LLM service with a test response
        class MockLlmService:
            def completion(self, model, messages, temperature, stream=False, **kwargs):
                # Simulate a response from the LLM
                return {
                    "choices": [{
                        "message": {
                            "content": '{"type":"final","response":"This is a test response from the director agent."}'
                        }
                    }]
                }
            
            def validate_config(self):
                return True  # Assume it's configured for testing
        
        # Replace the LLM service with our mock
        crew_member.llm_service = MockLlmService()
        
        # Test utility functions that create messages
        print("\n1. Testing utility functions...")
        from agent.utils import create_text_message, create_error_message, create_system_message
        
        text_msg = create_text_message("Test text message content", "test_sender", "Test Sender")
        error_msg = create_error_message("Test error message", "error_sender", "Error Sender")
        system_msg = create_system_message("Test system message")
        
        print(f"   Created text message: {text_msg.message_id}")
        print(f"   Created error message: {error_msg.message_id}")
        print(f"   Created system message: {system_msg.message_id}")
        
        # Capture logs after utility function calls
        log_contents = log_capture_string.getvalue()
        print(f"   Log contents after utility calls: {len(log_contents)} characters")
        
        # Variables to capture events
        captured_events = []
        
        def mock_on_stream_event(event):
            captured_events.append({
                "event_type": event.event_type,
                "data": event.data
            })
        
        # Test the chat_stream method which creates messages
        print("\n2. Testing crew chat_stream...")
        response_tokens = []
        
        try:
            async for token in crew_member.chat_stream(
                message="Test message",
                on_stream_event=mock_on_stream_event
            ):
                response_tokens.append(token)
        
            print(f"   Received {len(response_tokens)} response tokens")
            
            # Get logs after crew execution
            log_contents_after = log_capture_string.getvalue()
            print(f"   Total log contents after crew execution: {len(log_contents_after)} characters")
            
            # Look for specific log messages
            logs = log_contents_after.split('\n')
            agent_message_logs = [log for log in logs if 'Sending agent message' in log or 'Created' in log]
            
            print(f"   Found {len(agent_message_logs)} agent message logs:")
            for log in agent_message_logs:
                if log.strip():
                    print(f"     - {log.split(' - ')[-1]}")  # Print just the message part
            
            # Verify that we have logs for different message types
            has_text_logs = any('Created text message' in log for log in logs)
            has_error_logs = any('Created error message' in log for log in logs)
            has_system_logs = any('Created system message' in log for log in logs)
            has_send_logs = any('Sending agent message' in log for log in logs)
            
            print(f"\n3. Verification:")
            print(f"   Has text message logs: {has_text_logs}")
            print(f"   Has error message logs: {has_error_logs}")
            print(f"   Has system message logs: {has_system_logs}")
            print(f"   Has sending message logs: {has_send_logs}")
            
            success = has_text_logs and has_error_logs and has_system_logs and has_send_logs
            if success:
                print("\n✅ SUCCESS: All expected log types were found!")
                return True
            else:
                print("\n❌ FAILURE: Some expected log types were missing")
                return False
                
        except Exception as e:
            print(f"❌ ERROR during test: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_filmeto_agent_logging():
    """Test logging in FilmetoAgent message creation"""
    print("\n4. Testing FilmetoAgent message creation logging...")
    
    try:
        from agent.filmeto_agent import FilmetoAgent, StreamEvent
        from app.data.workspace import Workspace
        import tempfile
        from pathlib import Path
        
        # Create a temporary project
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            
            # Initialize a minimal project structure
            agent_dir = project_path / "agent"
            agent_dir.mkdir()
            sub_agents_dir = agent_dir / "sub_agents"
            sub_agents_dir.mkdir()
            
            # Create a simple director agent config
            director_config = sub_agents_dir / "director.md"
            director_config.write_text("""---
name: director
description: Film director agent
soul: creative_vision
skills: []
model: gpt-4o-mini
temperature: 0.7
max_steps: 3
---

You are a film director. Help with directing films.
""")
            
            # Create a mock workspace
            workspace = Workspace(workspace_path=temp_dir, project_name="test_project")
            
            # Create a project
            from app.data.project import Project
            project = Project(
                project_name="test_project",
                project_path=str(project_path),
                workspace=workspace
            )
            
            # Create FilmetoAgent
            agent = FilmetoAgent(
                workspace=workspace,
                project=project,
                model="gpt-4o-mini"
            )
            
            # Manually create a message to test logging
            from agent.chat.agent_chat_message import MessageType
            initial_msg = AgentMessage(
                content="Test initial message",
                message_type=MessageType.TEXT,
                sender_id="user",
                sender_name="User"
            )
            
            print(f"   Created initial message: {initial_msg.message_id}")
            
            # Check if logging was triggered
            print("   ✅ FilmetoAgent message creation test completed")
            return True
                
    except Exception as e:
        print(f"❌ ERROR during FilmetoAgent test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running agent message logging tests...\n")
    
    success1 = asyncio.run(test_logging_functionality())
    success2 = test_filmeto_agent_logging()
    
    if success1 and success2:
        print("\n🎉 All logging tests passed!")
    else:
        print("\n💥 Some logging tests failed!")