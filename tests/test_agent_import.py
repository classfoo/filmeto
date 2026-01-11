#!/usr/bin/env python
"""Simple test to measure import time of agent panel."""

import time
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_agent_panel_import():
    """Test how long it takes to import the agent panel module."""
    print("Testing agent panel import time...")
    
    start_time = time.time()
    
    # Import the agent panel module
    from app.ui.panels.agent.agent_panel import AgentPanel
    
    end_time = time.time()
    elapsed_ms = (end_time - start_time) * 1000
    
    print(f"Agent panel module imported in {elapsed_ms:.2f}ms")
    
    # Also test instantiating the class
    start_time = time.time()
    
    # We can't fully instantiate without workspace, but we can check the import worked
    print(f"AgentPanel class: {AgentPanel}")
    
    end_time = time.time()
    elapsed_init_ms = (end_time - start_time) * 1000
    
    print(f"Class reference obtained in {elapsed_init_ms:.2f}ms")
    print(f"Total time: {elapsed_ms + elapsed_init_ms:.2f}ms")
    
    return elapsed_ms

if __name__ == "__main__":
    test_agent_panel_import()