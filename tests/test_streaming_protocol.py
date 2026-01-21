"""Tests for the streaming protocol and multi-agent conversation display.

This test suite covers:
- StreamEvent and StreamEventEmitter
- AgentStreamManager and AgentStreamSession
- DependencyGraph for parallel task execution
- Message aggregation and session management
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

# Import streaming components
from agent.streaming.protocol import (
    StreamEventType,
    StreamEvent,
    AgentRole,
    ContentType,
    StructuredContent,
    PlanContent,
    TaskContent,
    MediaContent,
    ReferenceContent,
    ThinkingContent,
    StreamEventEmitter,
)
from agent.streaming.manager import (
    AgentStreamManager,
    AgentStreamSession,
    AgentMessage,
    DependencyGraph,
)


class TestAgentRole:
    """Tests for AgentRole enum."""
    
    def test_from_agent_name(self):
        """Test converting agent names to roles."""
        assert AgentRole.from_agent_name("Director") == AgentRole.DIRECTOR
        assert AgentRole.from_agent_name("Screenwriter") == AgentRole.SCREENWRITER
        assert AgentRole.from_agent_name("Actor") == AgentRole.ACTOR
        assert AgentRole.from_agent_name("Editor") == AgentRole.EDITOR
        assert AgentRole.from_agent_name("Unknown") == AgentRole.SYSTEM
    
    def test_display_name(self):
        """Test display names for roles."""
        assert AgentRole.USER.display_name == "User"
        assert AgentRole.COORDINATOR.display_name == "Coordinator"
        assert AgentRole.DIRECTOR.display_name == "Director"
    
    def test_color(self):
        """Test color codes for roles."""
        assert AgentRole.USER.color == "#35373a"
        assert AgentRole.DIRECTOR.color == "#4ecdc4"
        assert AgentRole.PLANNER.color == "#7c4dff"


class TestStreamEvent:
    """Tests for StreamEvent dataclass."""
    
    def test_create_event(self):
        """Test creating a stream event."""
        event = StreamEvent(
            event_type=StreamEventType.AGENT_START,
            title=AgentRole.DIRECTOR,
            agent_name="Director",
            content="Starting direction"
        )
        
        assert event.event_type == StreamEventType.AGENT_START
        assert event.agent_role == AgentRole.DIRECTOR
        assert event.agent_name == "Director"
        assert event.content == "Starting direction"
        assert event.event_id is not None
        assert event.timestamp is not None
    
    def test_to_dict(self):
        """Test converting event to dictionary."""
        event = StreamEvent(
            event_type=StreamEventType.CONTENT_TOKEN,
            title=AgentRole.SCREENWRITER,
            agent_name="Screenwriter",
            content="Hello",
            progress=0.5
        )
        
        data = event.to_dict()
        
        assert data["event_type"] == "content_token"
        assert data["agent_role"] == "screenwriter"
        assert data["agent_name"] == "Screenwriter"
        assert data["content"] == "Hello"
        assert data["progress"] == 0.5
    
    def test_from_dict(self):
        """Test creating event from dictionary."""
        data = {
            "event_type": "agent_complete",
            "agent_role": "director",
            "agent_name": "Director",
            "content": "Done"
        }
        
        event = StreamEvent.from_dict(data)
        
        assert event.event_type == StreamEventType.AGENT_COMPLETE
        assert event.agent_role == AgentRole.DIRECTOR
        assert event.content == "Done"


class TestStructuredContent:
    """Tests for structured content types."""
    
    def test_plan_content(self):
        """Test PlanContent creation."""
        plan = PlanContent(
            description="Create a short film",
            phase="pre_production",
            tasks=[
                {"task_id": 1, "agent_name": "Screenwriter", "skill_name": "script_outline"}
            ],
            success_criteria="Complete all tasks"
        )
        
        assert plan.content_type == ContentType.PLAN
        assert plan.data["description"] == "Create a short film"
        assert plan.data["phase"] == "pre_production"
        assert len(plan.data["tasks"]) == 1
    
    def test_task_content(self):
        """Test TaskContent creation."""
        task = TaskContent(
            task_id="1",
            agent_name="Director",
            skill_name="scene_direction",
            status="running",
            message="Directing scene 1"
        )
        
        assert task.content_type == ContentType.TASK
        assert task.data["task_id"] == "1"
        assert task.data["status"] == "running"
    
    def test_media_content(self):
        """Test MediaContent creation."""
        media = MediaContent(
            media_type="video",
            url="/path/to/video.mp4",
            title="Scene 1",
            description="Opening scene"
        )
        
        assert media.content_type == ContentType.MEDIA
        assert media.data["media_type"] == "video"
        assert media.data["url"] == "/path/to/video.mp4"
    
    def test_reference_content(self):
        """Test ReferenceContent creation."""
        ref = ReferenceContent(
            ref_type="timeline_item",
            ref_id="item-123",
            name="Scene 1"
        )
        
        assert ref.content_type == ContentType.REFERENCE
        assert ref.data["ref_type"] == "timeline_item"
        assert ref.data["ref_id"] == "item-123"


class TestStreamEventEmitter:
    """Tests for StreamEventEmitter."""
    
    def test_emit_event(self):
        """Test emitting events with callbacks."""
        emitter = StreamEventEmitter()
        received_events = []
        
        emitter.add_callback(lambda e: received_events.append(e))
        
        event = StreamEvent(
            event_type=StreamEventType.AGENT_START,
            title=AgentRole.DIRECTOR,
            agent_name="Director"
        )
        emitter.emit(event)
        
        assert len(received_events) == 1
        assert received_events[0].event_type == StreamEventType.AGENT_START
        assert received_events[0].session_id == emitter.session_id
    
    def test_emit_session_start(self):
        """Test emitting session start event."""
        emitter = StreamEventEmitter()
        received_events = []
        emitter.add_callback(lambda e: received_events.append(e))
        
        emitter.emit_session_start({"key": "value"})
        
        assert len(received_events) == 1
        assert received_events[0].event_type == StreamEventType.SESSION_START
    
    def test_emit_agent_start(self):
        """Test emitting agent start event."""
        emitter = StreamEventEmitter()
        received_events = []
        emitter.add_callback(lambda e: received_events.append(e))
        
        event = emitter.emit_agent_start("Director", AgentRole.DIRECTOR)
        
        assert len(received_events) == 1
        assert received_events[0].event_type == StreamEventType.AGENT_START
        assert received_events[0].agent_name == "Director"
        assert received_events[0].message_id is not None
    
    def test_emit_content_token(self):
        """Test emitting content tokens."""
        emitter = StreamEventEmitter()
        received_events = []
        emitter.add_callback(lambda e: received_events.append(e))
        
        # Start agent first
        emitter.emit_agent_start("Director")
        
        # Emit tokens
        emitter.emit_content_token("Director", "H")
        emitter.emit_content_token("Director", "e")
        emitter.emit_content_token("Director", "l")
        emitter.emit_content_token("Director", "l")
        emitter.emit_content_token("Director", "o")
        
        # Check token events have same message_id
        token_events = [e for e in received_events if e.event_type == StreamEventType.CONTENT_TOKEN]
        assert len(token_events) == 5
        assert all(e.message_id == token_events[0].message_id for e in token_events)
    
    def test_emit_plan_created(self):
        """Test emitting plan created event."""
        emitter = StreamEventEmitter()
        received_events = []
        emitter.add_callback(lambda e: received_events.append(e))
        
        plan = {
            "description": "Create film",
            "phase": "pre_production",
            "tasks": [{"task_id": 1}]
        }
        
        event, plan_id = emitter.emit_plan_created(plan, "Planner")
        
        assert len(received_events) == 1
        assert received_events[0].event_type == StreamEventType.PLAN_CREATED
        assert received_events[0].plan_id == plan_id
        assert received_events[0].structured_content is not None
    
    def test_emit_task_complete(self):
        """Test emitting task complete event."""
        emitter = StreamEventEmitter()
        received_events = []
        emitter.add_callback(lambda e: received_events.append(e))
        
        event = emitter.emit_task_complete(
            task_id="1",
            agent_name="Director",
            skill_name="scene_direction",
            status="success",
            message="Scene directed successfully",
            quality_score=0.9
        )
        
        assert len(received_events) == 1
        assert received_events[0].event_type == StreamEventType.PLAN_TASK_COMPLETE
        assert received_events[0].structured_content is not None
    
    def test_remove_callback(self):
        """Test removing callbacks."""
        emitter = StreamEventEmitter()
        received_events = []
        
        callback = lambda e: received_events.append(e)
        emitter.add_callback(callback)
        
        emitter.emit_session_start()
        assert len(received_events) == 1
        
        emitter.remove_callback(callback)
        emitter.emit_session_end()
        assert len(received_events) == 1  # No new events


class TestDependencyGraph:
    """Tests for DependencyGraph."""
    
    def test_add_tasks(self):
        """Test adding tasks to the graph."""
        graph = DependencyGraph()
        
        graph.add_task("1", {"name": "Task 1"}, [])
        graph.add_task("2", {"name": "Task 2"}, ["1"])
        graph.add_task("3", {"name": "Task 3"}, ["1"])
        graph.add_task("4", {"name": "Task 4"}, ["2", "3"])
        
        assert graph.get_task("1")["name"] == "Task 1"
        assert graph.get_task("4")["name"] == "Task 4"
    
    def test_get_ready_tasks(self):
        """Test getting tasks ready to execute."""
        graph = DependencyGraph()
        
        graph.add_task("1", {"name": "Task 1"}, [])
        graph.add_task("2", {"name": "Task 2"}, ["1"])
        graph.add_task("3", {"name": "Task 3"}, ["1"])
        graph.add_task("4", {"name": "Task 4"}, ["2", "3"])
        
        # Initially only task 1 is ready
        ready = graph.get_ready_tasks()
        assert ready == ["1"]
        
        # After completing task 1, tasks 2 and 3 are ready
        graph.mark_complete("1")
        ready = graph.get_ready_tasks()
        assert set(ready) == {"2", "3"}
        
        # After completing task 2, task 3 is still ready, 4 is not
        graph.mark_complete("2")
        ready = graph.get_ready_tasks()
        assert ready == ["3"]
        
        # After completing task 3, task 4 is ready
        graph.mark_complete("3")
        ready = graph.get_ready_tasks()
        assert ready == ["4"]
    
    def test_parallel_groups(self):
        """Test getting parallel execution groups."""
        graph = DependencyGraph()
        
        graph.add_task("1", {}, [])
        graph.add_task("2", {}, ["1"])
        graph.add_task("3", {}, ["1"])
        graph.add_task("4", {}, ["2", "3"])
        
        groups = graph.get_parallel_groups()
        
        assert len(groups) == 3
        assert groups[0] == ["1"]
        assert set(groups[1]) == {"2", "3"}
        assert groups[2] == ["4"]
    
    def test_completion_status(self):
        """Test getting completion status."""
        graph = DependencyGraph()
        
        graph.add_task("1", {}, [])
        graph.add_task("2", {}, ["1"])
        graph.add_task("3", {}, ["1"])
        
        status = graph.get_completion_status()
        assert status["total"] == 3
        assert status["completed"] == 0
        assert status["is_complete"] is False
        
        graph.mark_complete("1")
        graph.mark_complete("2")
        graph.mark_failed("3")
        
        status = graph.get_completion_status()
        assert status["completed"] == 2
        assert status["failed"] == 1
        assert status["is_complete"] is True
    
    def test_add_tasks_from_plan(self):
        """Test adding tasks from execution plan."""
        graph = DependencyGraph()
        
        plan = {
            "tasks": [
                {"task_id": 1, "agent_name": "Screenwriter", "skill_name": "script_outline", "dependencies": []},
                {"task_id": 2, "agent_name": "Director", "skill_name": "storyboard", "dependencies": [1]},
                {"task_id": 3, "agent_name": "Director", "skill_name": "scene_composition", "dependencies": [1]},
                {"task_id": 4, "agent_name": "Editor", "skill_name": "video_editing", "dependencies": [2, 3]},
            ]
        }
        
        graph.add_tasks_from_plan(plan)
        
        groups = graph.get_parallel_groups()
        assert len(groups) == 3


class TestAgentStreamSession:
    """Tests for AgentStreamSession."""
    
    def test_create_session(self):
        """Test creating a session."""
        session = AgentStreamSession()
        
        assert session.session_id is not None
        assert session.is_active is True
        assert len(session.messages) == 0
    
    def test_get_or_create_message(self):
        """Test getting or creating messages."""
        session = AgentStreamSession()
        
        msg1 = session.get_or_create_message("msg-1", "Director", AgentRole.DIRECTOR)
        msg2 = session.get_or_create_message("msg-1", "Director", AgentRole.DIRECTOR)
        msg3 = session.get_or_create_message("msg-2", "Screenwriter", AgentRole.SCREENWRITER)
        
        # Same ID returns same message
        assert msg1 is msg2
        # Different ID returns different message
        assert msg1 is not msg3
        
        assert len(session.messages) == 2
    
    def test_message_order(self):
        """Test message ordering."""
        session = AgentStreamSession()
        
        session.get_or_create_message("msg-1", "Director", AgentRole.DIRECTOR)
        session.get_or_create_message("msg-2", "Screenwriter", AgentRole.SCREENWRITER)
        session.get_or_create_message("msg-3", "Editor", AgentRole.EDITOR)
        
        messages = session.get_all_messages()
        
        assert len(messages) == 3
        assert messages[0].message_id == "msg-1"
        assert messages[1].message_id == "msg-2"
        assert messages[2].message_id == "msg-3"
    
    def test_agent_messages(self):
        """Test getting messages by agent."""
        session = AgentStreamSession()
        
        session.get_or_create_message("msg-1", "Director", AgentRole.DIRECTOR)
        session.get_or_create_message("msg-2", "Director", AgentRole.DIRECTOR)
        session.get_or_create_message("msg-3", "Screenwriter", AgentRole.SCREENWRITER)
        
        director_msgs = session.get_agent_messages("Director")
        screenwriter_msgs = session.get_agent_messages("Screenwriter")
        
        assert len(director_msgs) == 2
        assert len(screenwriter_msgs) == 1
    
    def test_set_plan(self):
        """Test setting execution plan."""
        session = AgentStreamSession()
        
        plan = {"description": "Test plan", "tasks": []}
        session.set_plan(plan, "plan-123")
        
        assert session.current_plan == plan
        assert session.plan_id == "plan-123"
    
    def test_end_session(self):
        """Test ending a session."""
        session = AgentStreamSession()
        
        assert session.is_active is True
        assert session.end_time is None
        
        session.end_session()
        
        assert session.is_active is False
        assert session.end_time is not None


class TestAgentMessage:
    """Tests for AgentMessage."""
    
    def test_append_content(self):
        """Test appending content."""
        msg = AgentMessage(
            message_id="msg-1",
            agent_name="Director",
            title=AgentRole.DIRECTOR
        )
        
        msg.append_content("Hello")
        msg.append_content(" World")
        
        assert msg.content == "Hello World"
    
    def test_set_content(self):
        """Test setting content."""
        msg = AgentMessage(
            message_id="msg-1",
            agent_name="Director",
            title=AgentRole.DIRECTOR
        )
        
        msg.set_content("First")
        msg.set_content("Second")
        
        assert msg.content == "Second"
    
    def test_add_structured_content(self):
        """Test adding structured content."""
        msg = AgentMessage(
            message_id="msg-1",
            agent_name="Director",
            title=AgentRole.DIRECTOR
        )
        
        task = TaskContent(
            task_id="1",
            agent_name="Director",
            skill_name="scene_direction",
            status="success"
        )
        
        msg.add_structured_content(task)
        
        assert len(msg.structured_contents) == 1
        assert msg.structured_contents[0] == task


class TestAgentStreamManager:
    """Tests for AgentStreamManager."""
    
    def test_create_session(self):
        """Test creating a session."""
        manager = AgentStreamManager()
        
        session, emitter = manager.create_session()
        
        assert session is not None
        assert emitter is not None
        assert session.session_id == emitter.session_id
    
    def test_get_session(self):
        """Test getting a session."""
        manager = AgentStreamManager()
        
        session1, _ = manager.create_session()
        session2 = manager.get_session(session1.session_id)
        
        assert session1 is session2
    
    def test_ui_callbacks(self):
        """Test UI callbacks."""
        manager = AgentStreamManager()
        received_events = []
        
        def callback(event, session):
            received_events.append((event, session))
        
        manager.add_ui_callback(callback)
        
        session, emitter = manager.create_session()
        emitter.emit_session_start()
        
        assert len(received_events) == 1
        assert received_events[0][1] is session
    
    def test_event_handling(self):
        """Test that events update session state."""
        manager = AgentStreamManager()
        session, emitter = manager.create_session()
        
        # Emit some events
        emitter.emit_session_start()
        emitter.emit_agent_start("Director", AgentRole.DIRECTOR)
        emitter.emit_content_token("Director", "Hello")
        emitter.emit_agent_complete("Director", "Hello World")
        
        # Check session state
        messages = session.get_all_messages()
        assert len(messages) == 1
        assert messages[0].agent_name == "Director"
        assert messages[0].is_complete is True


class TestIntegration:
    """Integration tests for the streaming system."""
    
    def test_full_conversation_flow(self):
        """Test a complete multi-agent conversation flow."""
        manager = AgentStreamManager()
        session, emitter = manager.create_session()
        
        # Simulate a multi-agent conversation
        emitter.emit_session_start({"user_message": "Create a short film"})
        
        # Coordinator starts
        emitter.emit_agent_start("Coordinator", AgentRole.COORDINATOR)
        emitter.emit_agent_thinking("Coordinator", "Analyzing request...")
        emitter.emit_agent_content("Coordinator", "I'll help you create a short film.")
        emitter.emit_agent_complete("Coordinator")
        
        # Planner creates a plan
        emitter.emit_agent_start("Planner", AgentRole.PLANNER)
        plan = {
            "description": "Create a 1-minute short film",
            "phase": "full_production",
            "tasks": [
                {"task_id": 1, "agent_name": "Screenwriter", "skill_name": "script_outline"},
                {"task_id": 2, "agent_name": "Director", "skill_name": "storyboard", "dependencies": [1]},
            ]
        }
        event, plan_id = emitter.emit_plan_created(plan, "Planner")
        emitter.emit_agent_complete("Planner")
        
        # Screenwriter executes task
        emitter.emit_task_start("1", "Screenwriter", "script_outline", plan_id)
        emitter.emit_agent_content("Screenwriter", "Creating script outline...")
        emitter.emit_task_complete(
            "1", "Screenwriter", "script_outline",
            "success", "Script outline created", 0.9
        )
        
        # Director executes task
        emitter.emit_task_start("2", "Director", "storyboard", plan_id)
        emitter.emit_agent_content("Director", "Creating storyboard...")
        emitter.emit_task_complete(
            "2", "Director", "storyboard",
            "success", "Storyboard created", 0.85
        )
        
        # Session ends
        emitter.emit_session_end()
        
        # Verify session state
        assert session.is_active is False
        assert len(session.get_all_messages()) >= 4  # Coordinator, Planner, Screenwriter, Director
        assert session.current_plan is not None
        
        # Verify agent messages
        coordinator_msgs = session.get_agent_messages("Coordinator")
        assert len(coordinator_msgs) == 1
        assert coordinator_msgs[0].is_complete is True
        
        # Planner has 2 messages: one from emit_agent_start, one from emit_plan_created
        planner_msgs = session.get_agent_messages("Planner")
        assert len(planner_msgs) >= 1  # At least one message
        # Check that at least one planner message has the plan
        plan_msgs = [m for m in planner_msgs if m.plan_id is not None]
        assert len(plan_msgs) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
