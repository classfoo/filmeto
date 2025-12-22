"""
Test script for ServerManager functionality

Demonstrates the server management system including:
- Creating and managing servers
- Routing tasks to servers
- Configuring routing rules
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server.server import ServerManager, ServerConfig, RoutingRule
from server.api.types import FilmetoTask, ToolType


async def test_server_manager():
    """Test ServerManager functionality"""
    
    print("=" * 80)
    print("ServerManager Test")
    print("=" * 80)
    
    # Get workspace path
    workspace_path = os.path.join(os.path.dirname(__file__), "..", "workspace", "demo")
    
    # Create server manager
    print("\n1. Creating ServerManager...")
    manager = ServerManager(workspace_path)
    
    # List available server types
    print("\n2. Available server types (from plugins):")
    for server_type in manager.list_available_server_types():
        print(f"   - {server_type}")
    
    # List servers
    print("\n3. Current servers:")
    servers = manager.list_servers()
    for server in servers:
        status = "✅ Enabled" if server.is_enabled else "❌ Disabled"
        print(f"   - {server.name} ({server.server_type}): {status}")
        print(f"     Plugin: {server.config.plugin_name}")
        print(f"     Description: {server.config.description}")
    
    # List routing rules
    print("\n4. Routing rules:")
    rules = manager.get_routing_rules()
    for rule in rules:
        print(f"   - {rule.name} (priority={rule.priority})")
        print(f"     Target: {rule.server_name}")
        print(f"     Fallbacks: {', '.join(rule.fallback_servers) if rule.fallback_servers else 'None'}")
        print(f"     Conditions: {rule.conditions}")
    
    # Test adding a new server
    print("\n5. Adding a new custom server...")
    try:
        new_config = ServerConfig(
            name="custom_comfyui",
            server_type="comfyui",
            plugin_name="comfy_ui_demo",
            description="Custom ComfyUI server for testing",
            enabled=True,
            endpoint="http://localhost:8188",
            parameters={
                "max_workers": 2,
                "timeout": 120
            }
        )
        
        new_server = manager.add_server(new_config)
        print(f"   ✅ Added server: {new_server.name}")
        
    except ValueError as e:
        print(f"   ℹ️  Server already exists: {e}")
    
    # Test routing
    print("\n6. Testing task routing...")
    
    # Create a test task
    test_task = FilmetoTask(
        tool_name=ToolType.TEXT2IMAGE,
        plugin_name="comfy_ui_demo",
        parameters={
            "prompt": "A beautiful sunset over mountains",
            "width": 512,
            "height": 512
        }
    )
    
    # Route task
    target_server = manager.route_task(test_task)
    if target_server:
        print(f"   📍 Task routed to: {target_server.name}")
    else:
        print("   ❌ No suitable server found")
    
    # Route with fallback
    print("\n7. Testing task routing with fallback...")
    fallback_servers = manager.route_task_with_fallback(test_task)
    print(f"   📋 Server chain:")
    for i, server in enumerate(fallback_servers, 1):
        print(f"      {i}. {server.name} ({server.server_type})")
    
    # Test adding a custom routing rule
    print("\n8. Adding custom routing rule...")
    custom_rule = RoutingRule(
        name="text2image_custom",
        priority=10,
        conditions={
            "tool_name": "text2image",
            "parameters": {}
        },
        server_name="local",
        fallback_servers=["filmeto", "custom_comfyui"],
        enabled=True
    )
    
    try:
        manager.add_routing_rule(custom_rule)
        print(f"   ✅ Added routing rule: {custom_rule.name}")
    except Exception as e:
        print(f"   ℹ️  Rule already exists or error: {e}")
    
    # Show updated rules
    print("\n9. Updated routing rules:")
    rules = manager.get_routing_rules()
    for rule in rules:
        print(f"   - {rule.name} (priority={rule.priority}) -> {rule.server_name}")
    
    # Test server counts for UI
    print("\n10. Server statistics (for UI):")
    all_servers = manager.list_servers()
    active_count = sum(1 for s in all_servers if s.is_enabled)
    inactive_count = sum(1 for s in all_servers if not s.is_enabled)
    print(f"   Total: {len(all_servers)}")
    print(f"   Active: {active_count}")
    print(f"   Inactive: {inactive_count}")
    
    # Cleanup
    print("\n11. Cleaning up...")
    await manager.cleanup()
    print("   ✅ Cleanup complete")
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_server_manager())


