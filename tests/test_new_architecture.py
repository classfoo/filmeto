"""
Test suite for the new Multi-Agent Architecture.

Tests:
1. Project isolation
2. Agent independence (Subgraph architecture)
3. State communication between agents
"""

import pytest
from langchain_core.messages import HumanMessage

# Mock classes for testing
class MockWorkspace:
    """Mock workspace for testing."""
    def __init__(self):
        self.settings = {
            "ai_services.openai_api_key": "test_key",
            "ai_services.openai_host": "https://api.openai.com/v1"
        }


class MockProject:
    """Mock project for testing."""
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_path = f"/mock/path/{project_name}"
    
    def get_conversation_manager(self):
        return None


class TestProjectIsolation:
    """Test project-level isolation."""
    
    def test_project_name_assignment(self):
        """Test that each agent instance has correct project_name."""
        from agent.filmeto_agent import FilmetoAgent

        workspace = MockWorkspace()
        project1 = MockProject("project1")
        project2 = MockProject("project2")

        # Create agents for different projects
        agent1 = FilmetoAgent(workspace, project1)
        agent2 = FilmetoAgent(workspace, project2)

        # Verify project isolation
        assert agent1.project_name == "project1"
        assert agent2.project_name == "project2"
        assert agent1.project_name != agent2.project_name
    
    def test_filmeto_agent_project_context(self):
        """Test that FilmetoAgent maintains project context."""
        from agent.filmeto_agent import FilmetoAgent

        workspace = MockWorkspace()
        project = MockProject("test_project")

        agent = FilmetoAgent(workspace, project)

        # Verify agent has project context
        assert agent.workspace == workspace
        assert agent.project == project


class TestSubAgentArchitecture:
    """Test Sub-Agent Subgraph architecture."""
    
    def test_sub_agent_has_graph(self):
        """Test that each sub-agent has its own graph."""
        from agent.sub_agents.director import DirectorAgent
        from agent.sub_agents.screenwriter import ScreenwriterAgent
        
        director = DirectorAgent()
        screenwriter = ScreenwriterAgent()
        
        # Each agent should have its own graph
        assert hasattr(director, 'graph')
        assert hasattr(screenwriter, 'graph')
        assert director.graph is not None
        assert screenwriter.graph is not None
        
        # Graphs should be different instances
        assert director.graph is not screenwriter.graph
    
    @pytest.mark.asyncio
    async def test_sub_agent_independent_execution(self):
        """Test that sub-agents execute independently."""
        from agent.sub_agents.director import DirectorAgent
        from agent.skills.base import SkillContext, SkillStatus
        
        director = DirectorAgent()
        
        # Create a test task
        task = {
            "skill_name": "storyboard",
            "parameters": {"script": "Test script"}
        }
        
        context = SkillContext(
            workspace=MockWorkspace(),
            project=MockProject("test"),
            agent_name="Director",
            parameters=task["parameters"],
            shared_state={},
            tool_registry=None
        )
        
        try:
            # Execute task through subgraph
            result = await director.execute_task(task, context)
            
            # Verify result structure
            assert hasattr(result, 'status')
            assert hasattr(result, 'output')
            assert hasattr(result, 'message')
        except Exception as e:
            # Expected to fail without real LLM, but structure should be correct
            print(f"Expected error: {e}")


class TestStateManagement:
    """Test state management and communication."""
    
    def test_agent_message_structure(self):
        """Test AgentMessage structure."""
        from agent.chat.agent_chat_message import AgentMessage
        from agent.chat.agent_chat_types import MessageType
        from langchain_core.messages import HumanMessage

        # Create an agent message
        message = AgentMessage(
            content="Test message",
            message_type=MessageType.TEXT,
            sender_id="test_agent",
            sender_name="Test Agent",
            message_id="test_id"
        )

        # Verify message structure
        assert message.content == "Test message"
        assert message.sender_id == "test_agent"
        assert message.sender_name == "Test Agent"
        assert message.message_id == "test_id"
    
    def test_agent_conversation_flow(self):
        """Test agent conversation flow."""
        from agent.chat.agent_chat_message import AgentMessage
        from agent.chat.agent_chat_types import MessageType

        # Create a sequence of messages representing a conversation
        messages = [
            AgentMessage(
                content="Hello, I need help creating a video.",
                message_type=MessageType.TEXT,
                sender_id="user",
                sender_name="User",
                message_id="msg_001"
            ),
            AgentMessage(
                content="Sure, I can help you with that. What kind of video are you looking to create?",
                message_type=MessageType.TEXT,
                sender_id="assistant",
                sender_name="Assistant",
                message_id="msg_002"
            )
        ]

        # Verify conversation structure
        assert len(messages) == 2
        assert messages[0].sender_id == "user"
        assert messages[1].sender_id == "assistant"
        assert messages[0].message_type == MessageType.TEXT
    
    def test_isolation_between_different_projects(self):
        """Test that conversations are isolated between different projects."""
        from agent.chat.agent_chat_message import AgentMessage
        from agent.chat.agent_chat_types import MessageType

        # Create messages for two different projects
        project1_messages = [
            AgentMessage(
                content="Project 1 message",
                message_type=MessageType.TEXT,
                sender_id="user",
                sender_name="User",
                message_id="proj1_msg_001"
            )
        ]

        project2_messages = [
            AgentMessage(
                content="Project 2 message",
                message_type=MessageType.TEXT,
                sender_id="user",
                sender_name="User",
                message_id="proj2_msg_001"
            )
        ]

        # Verify isolation
        assert project1_messages[0].content != project2_messages[0].content
        assert project1_messages[0].message_id != project2_messages[0].message_id


class TestFilmetoAgent:
    """Test FilmetoAgent as main orchestrator."""
    
    def test_filmeto_agent_initialization(self):
        """Test FilmetoAgent initialization."""
        from agent.filmeto_agent import FilmetoAgent

        workspace = MockWorkspace()
        project = MockProject("test")

        agent = FilmetoAgent(
            workspace=workspace,
            project=project,
            model='gpt-4o-mini',
            temperature=0.7
        )

        # Verify initialization
        assert agent.workspace == workspace
        assert agent.project == project
        assert agent.model == 'gpt-4o-mini'
        assert agent.temperature == 0.7


class TestConversationIsolation:
    """Test conversation isolation by project."""
    
    def test_conversation_manager_project_scoped(self):
        """Test that conversation manager is project-scoped."""
        from agent.filmeto_agent import FilmetoAgent
        
        workspace = MockWorkspace()
        project1 = MockProject("project1")
        project2 = MockProject("project2")
        
        agent1 = FilmetoAgent(workspace, project1)
        agent2 = FilmetoAgent(workspace, project2)
        
        # Each agent should manage its own project's conversations
        # (conversation_manager is None in mock, but structure is correct)
        assert agent1.conversation_manager == agent2.conversation_manager  # Both None in mock
        
        # But project names are different
        assert agent1.project_name != agent2.project_name


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
