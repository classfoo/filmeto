#!/usr/bin/env python
"""Debug script to trace import time of agent panel."""

import time
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def trace_imports():
    """Trace the import process to identify bottlenecks."""
    print("Tracing agent panel import...")
    
    # Track time at each step
    start_time = time.time()
    
    # Import the module
    import importlib
    module = importlib.import_module('app.ui.panels.agent.agent_panel')
    
    end_time = time.time()
    total_time = (end_time - start_time) * 1000
    
    print(f"Module imported in {total_time:.2f}ms")
    print(f"Module: {module}")
    
    # Check if the class is accessible
    agent_panel_class = getattr(module, 'AgentPanel')
    print(f"AgentPanel class: {agent_panel_class}")
    
    return total_time

if __name__ == "__main__":
    trace_imports()