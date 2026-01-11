"""Test agent role aggregation for main agent vs sub-agents."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.streaming.protocol import (
    AgentRole,
    StreamEventEmitter,
    StreamEvent,
    StreamEventType,
)


def test_main_agent_role_classification():
    """Test that main agent roles are correctly classified."""
    main_roles = [
        AgentRole.MAIN_AGENT,
        AgentRole.COORDINATOR,
        AgentRole.PLANNER,
        AgentRole.QUESTION_UNDERSTANDING,
        AgentRole.EXECUTOR,
        AgentRole.PLAN_REFINEMENT,
        AgentRole.RESPONSE,
        AgentRole.REVIEWER,
        AgentRole.SYNTHESIZER,
    ]
    
    for role in main_roles:
        assert AgentRole.is_main_agent_role(role), f"{role} should be a main agent role"
        assert not AgentRole.is_sub_agent_role(role), f"{role} should not be a sub-agent role"
    
    print("✓ Main agent role classification test passed")


def test_sub_agent_role_classification():
    """Test that sub-agent roles are correctly classified."""
    sub_roles = [
        AgentRole.PRODUCTION,
        AgentRole.DIRECTOR,
        AgentRole.SCREENWRITER,
        AgentRole.ACTOR,
        AgentRole.MAKEUP_ARTIST,
        AgentRole.SUPERVISOR,
        AgentRole.SOUND_MIXER,
        AgentRole.EDITOR,
    ]
    
    for role in sub_roles:
        assert AgentRole.is_sub_agent_role(role), f"{role} should be a sub-agent role"
        assert not AgentRole.is_main_agent_role(role), f"{role} should not be a main agent role"
    
    print("✓ Sub-agent role classification test passed")


def test_main_agent_message_aggregation():
    """Test that main agent roles share the same message ID."""
    emitter = StreamEventEmitter()
    
    events = []
    emitter.add_callback(lambda event: events.append(event))
    
    # Emit events from different main agent roles
    emitter.emit_agent_start("Coordinator", AgentRole.COORDINATOR)
    emitter.emit_agent_content("Coordinator", "Coordinator content")
    
    emitter.emit_agent_start("Planner", AgentRole.PLANNER)
    emitter.emit_agent_content("Planner", "Planner content")
    
    emitter.emit_agent_start("QuestionUnderstanding", AgentRole.QUESTION_UNDERSTANDING)
    emitter.emit_agent_content("QuestionUnderstanding", "Understanding content")
    
    # All main agent events should have the same message ID
    message_ids = [e.message_id for e in events]
    assert len(set(message_ids)) == 1, f"All main agent events should share one message ID, got {len(set(message_ids))}"
    
    # All should have MAIN_AGENT as agent_role
    for event in events:
        assert event.agent_role == AgentRole.MAIN_AGENT, f"Expected MAIN_AGENT role, got {event.agent_role}"
        assert event.agent_name == "MainAgent", f"Expected MainAgent name, got {event.agent_name}"
    
    # Check metadata contains original role
    assert events[0].metadata.get("original_role") == "coordinator"
    assert events[2].metadata.get("original_role") == "planner"
    assert events[4].metadata.get("original_role") == "question_understanding"
    
    print("✓ Main agent message aggregation test passed")


def test_sub_agent_separate_messages():
    """Test that sub-agents get separate message IDs."""
    emitter = StreamEventEmitter()
    
    events = []
    emitter.add_callback(lambda event: events.append(event))
    
    # Emit events from different sub-agents
    emitter.emit_agent_start("Director", AgentRole.DIRECTOR)
    emitter.emit_agent_content("Director", "Director content")
    
    emitter.emit_agent_start("Screenwriter", AgentRole.SCREENWRITER)
    emitter.emit_agent_content("Screenwriter", "Screenwriter content")
    
    emitter.emit_agent_start("Actor", AgentRole.ACTOR)
    emitter.emit_agent_content("Actor", "Actor content")
    
    # Each sub-agent should have different message IDs
    message_ids = [e.message_id for e in events if e.event_type == StreamEventType.AGENT_START]
    assert len(set(message_ids)) == 3, f"Each sub-agent should have unique message ID, got {len(set(message_ids))}"
    
    # Check that roles are preserved
    assert events[0].agent_role == AgentRole.DIRECTOR
    assert events[2].agent_role == AgentRole.SCREENWRITER
    assert events[4].agent_role == AgentRole.ACTOR
    
    # Check agent names are preserved
    assert events[0].agent_name == "Director"
    assert events[2].agent_name == "Screenwriter"
    assert events[4].agent_name == "Actor"
    
    print("✓ Sub-agent separate messages test passed")


def test_mixed_main_and_sub_agents():
    """Test main agents and sub-agents in the same session."""
    emitter = StreamEventEmitter()
    
    events = []
    emitter.add_callback(lambda event: events.append(event))
    
    # Main agent starts
    emitter.emit_agent_start("Coordinator", AgentRole.COORDINATOR)
    coordinator_message_id = events[-1].message_id
    
    emitter.emit_agent_content("Planner", "Planning...")
    planner_message_id = events[-1].message_id
    
    # Should share same ID
    assert coordinator_message_id == planner_message_id
    
    # Sub-agents start
    emitter.emit_agent_start("Director", AgentRole.DIRECTOR)
    director_message_id = events[-1].message_id
    
    emitter.emit_agent_start("Actor", AgentRole.ACTOR)
    actor_message_id = events[-1].message_id
    
    # Sub-agents should have different IDs
    assert director_message_id != actor_message_id
    
    # Main agent ID should be different from sub-agent IDs
    assert coordinator_message_id != director_message_id
    assert coordinator_message_id != actor_message_id
    
    print("✓ Mixed main and sub-agents test passed")


def test_agent_name_to_role_mapping():
    """Test agent name to role conversion."""
    mappings = {
        "Coordinator": AgentRole.COORDINATOR,
        "Planner": AgentRole.PLANNER,
        "QuestionUnderstanding": AgentRole.QUESTION_UNDERSTANDING,
        "Executor": AgentRole.EXECUTOR,
        "Director": AgentRole.DIRECTOR,
        "Screenwriter": AgentRole.SCREENWRITER,
        "Actor": AgentRole.ACTOR,
        "Production": AgentRole.PRODUCTION,
        "Reviewer": AgentRole.REVIEWER,
        "Synthesizer": AgentRole.SYNTHESIZER,
    }
    
    for name, expected_role in mappings.items():
        role = AgentRole.from_agent_name(name)
        assert role == expected_role, f"Expected {expected_role} for {name}, got {role}"
    
    print("✓ Agent name to role mapping test passed")


if __name__ == "__main__":
    print("Testing agent role aggregation...")
    print()
    
    test_main_agent_role_classification()
    test_sub_agent_role_classification()
    test_main_agent_message_aggregation()
    test_sub_agent_separate_messages()
    test_mixed_main_and_sub_agents()
    test_agent_name_to_role_mapping()
    
    print()
    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print()
    print("Summary:")
    print("- Main agent roles (coordinator, planner, etc.) are aggregated into a single 'MainAgent' message")
    print("- Sub-agent roles (director, actor, etc.) maintain separate messages")
    print("- Original role information is preserved in metadata")
