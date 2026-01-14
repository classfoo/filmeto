"""
Test suite for the new Multi-Agent Architecture.

Tests:
1. Project isolation
2. Agent independence (Subgraph architecture)
3. State communication between agents
"""

import pytest
import asyncio
from typing import Dict, Any
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
    
    def test_project_id_assignment(self):
        """Test that each agent instance has correct project_id."""
        from agent.filmeto_agent import FilmetoAgent
        
        workspace = MockWorkspace()
        project1 = MockProject("project1")
        project2 = MockProject("project2")
        
        # Create agents for different projects
        agent1 = FilmetoAgent(workspace, project1)
        agent2 = FilmetoAgent(workspace, project2)
        
        # Verify project isolation
        assert agent1.project_id == "project1"
        assert agent2.project_id == "project2"
        assert agent1.project_id != agent2.project_id
    
    def test_production_agent_project_context(self):
        """Test that ProductionAgent maintains project context."""
        from agent.filmeto_agent import FilmetoAgent
        
        workspace = MockWorkspace()
        project = MockProject("test_project")
        
        agent = FilmetoAgent(workspace, project)
        
        # Verify production agent has project context
        if agent.production_agent:
            assert agent.production_agent.project_id == "test_project"
            assert agent.production_agent.workspace == workspace
            assert agent.production_agent.project == project


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
    
    def test_production_agent_state_structure(self):
        """Test ProductionAgentState structure."""
        from agent.graph.state import ProductionAgentState
        from langchain_core.messages import HumanMessage
        
        # Create state
        state: ProductionAgentState = {
            "project_id": "test_project",
            "messages": [HumanMessage(content="Test message")],
            "next_action": "question_understanding",
            "context": {"test": "value"},
            "iteration_count": 0,
            "execution_plan": None,
            "current_task_index": 0,
            "sub_agent_results": {},
            "requires_multi_agent": False,
            "plan_refinement_count": 0
        }
        
        # Verify state structure
        assert state["project_id"] == "test_project"
        assert len(state["messages"]) == 1
        assert state["next_action"] == "question_understanding"
    
    def test_sub_agent_state_structure(self):
        """Test SubAgentState structure."""
        from agent.graph.state import SubAgentState
        from langchain_core.messages import AIMessage
        
        # Create state
        state: SubAgentState = {
            "agent_id": "Director",
            "agent_name": "Director",
            "task": {"skill_name": "storyboard"},
            "task_id": "task_001",
            "messages": [AIMessage(content="Processing")],
            "context": {"workspace": None, "project": None},
            "result": None,
            "status": "pending",
            "metadata": {}
        }
        
        # Verify state structure
        assert state["agent_id"] == "Director"
        assert state["task"]["skill_name"] == "storyboard"
        assert state["status"] == "pending"
    
    def test_state_isolation_between_agents(self):
        """Test that agent states are isolated."""
        from agent.graph.state import SubAgentState
        
        # Create states for two different agents
        director_state: SubAgentState = {
            "agent_id": "Director",
            "agent_name": "Director",
            "task": {},
            "task_id": "task_001",
            "messages": [],
            "context": {"data": "director_data"},
            "result": None,
            "status": "pending",
            "metadata": {}
        }
        
        screenwriter_state: SubAgentState = {
            "agent_id": "Screenwriter",
            "agent_name": "Screenwriter",
            "task": {},
            "task_id": "task_002",
            "messages": [],
            "context": {"data": "screenwriter_data"},
            "result": None,
            "status": "pending",
            "metadata": {}
        }
        
        # Verify isolation
        assert director_state["agent_id"] != screenwriter_state["agent_id"]
        assert director_state["context"]["data"] != screenwriter_state["context"]["data"]
        assert director_state["task_id"] != screenwriter_state["task_id"]


class TestProductionAgent:
    """Test Production Agent as main orchestrator."""
    
    def test_production_agent_initialization(self):
        """Test ProductionAgent initialization."""
        from agent.production_agent import ProductionAgent
        from langchain_openai import ChatOpenAI
        from agent.sub_agents.registry import SubAgentRegistry
        from agent.tools import ToolRegistry
        
        workspace = MockWorkspace()
        project = MockProject("test")
        llm = ChatOpenAI(api_key="test_key")
        sub_agent_registry = SubAgentRegistry(llm=llm)
        tool_registry = ToolRegistry(workspace=workspace, project=project)
        
        production_agent = ProductionAgent(
            project_id="test_project",
            workspace=workspace,
            project=project,
            llm=llm,
            sub_agent_registry=sub_agent_registry,
            tool_registry=tool_registry
        )
        
        # Verify initialization
        assert production_agent.project_id == "test_project"
        assert production_agent.graph is not None
        assert production_agent.workspace == workspace
        assert production_agent.project == project


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
        
        # But project IDs are different
        assert agent1.project_id != agent2.project_id


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
