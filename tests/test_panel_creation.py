#!/usr/bin/env python
"""Test script to simulate the actual panel creation process."""

import time
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simulate_panel_creation():
    """Simulate the panel creation process like in workspace_top_right_bar."""
    print("Simulating panel creation process...")
    
    # Simulate the import timing like in _deferred_create_panel
    import_start = time.time()
    
    # Import panel class dynamically (this is what happens in _deferred_create_panel)
    import importlib
    module_path = 'app.ui.panels.agent.agent_panel'  # This matches what's in the registry
    class_name = 'AgentPanel'
    
    import_start_time = time.time()
    module = importlib.import_module(module_path)
    import_time = (time.time() - import_start_time) * 1000
    
    panel_class = getattr(module, class_name)
    
    # This is the end of the "import" phase that was showing up in the logs
    total_import_time = (time.time() - import_start) * 1000
    
    print(f"Module import completed in {import_time:.2f}ms")
    print(f"Total import phase: {total_import_time:.2f}ms")
    
    # Now test the instantiation (the "Init" phase)
    init_start = time.time()
    
    # We can't fully instantiate without workspace, but we can check the class
    print(f"Panel class retrieved: {panel_class.__name__}")
    
    init_time = (time.time() - init_start) * 1000
    
    print(f"Instantiation phase: {init_time:.2f}ms")
    print(f"Combined total: {(total_import_time + init_time):.2f}ms")
    
    return total_import_time, init_time

if __name__ == "__main__":
    simulate_panel_creation()