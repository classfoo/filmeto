"""
Server Manager Module

Manages server instances and routing for task execution.
Servers represent different AIGC service providers (ComfyUI, Bailian, Local, etc.)
that can generate images, videos, audio, and other storyboard materials.
"""

import os
import yaml
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

from server.api.types import FilmetoTask, TaskProgress, TaskResult
from server.plugins.plugin_manager import PluginManager, PluginInfo


@dataclass
class ServerConfig:
    """
    Configuration for a server instance.
    
    Attributes:
        name: Server name (must be unique)
        server_type: Type of server (comfyui, bailian, local, filmeto, etc.)
        description: Human-readable description
        enabled: Whether the server is enabled
        plugin_name: Associated plugin name for task execution
        endpoint: Optional endpoint URL for remote services
        api_key: Optional API key for authentication
        parameters: Additional server-specific parameters
        metadata: Additional metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    name: str
    server_type: str
    plugin_name: str
    description: str = ""
    enabled: bool = True
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization"""
        return {
            "name": self.name,
            "server_type": self.server_type,
            "plugin_name": self.plugin_name,
            "description": self.description,
            "enabled": self.enabled,
            "endpoint": self.endpoint,
            "api_key": self.api_key,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        """Create from dictionary loaded from YAML"""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.now()
        
        return cls(
            name=data["name"],
            server_type=data["server_type"],
            plugin_name=data["plugin_name"],
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            endpoint=data.get("endpoint"),
            api_key=data.get("api_key"),
            parameters=data.get("parameters", {}),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
        )
    
    def save_to_file(self, file_path: str):
        """Save configuration to YAML file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, sort_keys=False)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'ServerConfig':
        """Load configuration from YAML file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


@dataclass
class RoutingRule:
    """
    Routing rule for task distribution.
    
    Attributes:
        name: Rule name
        priority: Priority (higher = execute first)
        conditions: Conditions for matching (tool_name, parameters, etc.)
        server_name: Target server name
        fallback_servers: List of fallback server names if primary fails
        enabled: Whether the rule is enabled
    """
    name: str
    server_name: str
    priority: int = 0
    conditions: Dict[str, Any] = field(default_factory=dict)
    fallback_servers: List[str] = field(default_factory=list)
    enabled: bool = True
    
    def matches(self, task: FilmetoTask) -> bool:
        """Check if this rule matches the given task"""
        if not self.enabled:
            return False
        
        # Check tool_name condition
        if "tool_name" in self.conditions:
            expected_tool = self.conditions["tool_name"]
            if isinstance(expected_tool, list):
                if task.tool_name.value not in expected_tool:
                    return False
            elif task.tool_name.value != expected_tool:
                return False
        
        # Check plugin_name condition
        if "plugin_name" in self.conditions:
            if task.plugin_name != self.conditions["plugin_name"]:
                return False
        
        # Check custom parameters
        if "parameters" in self.conditions:
            for key, value in self.conditions["parameters"].items():
                if task.parameters.get(key) != value:
                    return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "priority": self.priority,
            "conditions": self.conditions,
            "server_name": self.server_name,
            "fallback_servers": self.fallback_servers,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoutingRule':
        """Create from dictionary"""
        return cls(
            name=data["name"],
            server_name=data["server_name"],
            priority=data.get("priority", 0),
            conditions=data.get("conditions", {}),
            fallback_servers=data.get("fallback_servers", []),
            enabled=data.get("enabled", True),
        )


class Server:
    """
    Server instance that manages plugin execution.
    
    A server represents a connection to an AIGC service provider
    and provides methods to execute tasks through its associated plugin.
    """
    
    def __init__(self, config: ServerConfig, plugin_manager: PluginManager):
        """
        Initialize server instance.
        
        Args:
            config: Server configuration
            plugin_manager: Plugin manager for task execution
        """
        self.config = config
        self.plugin_manager = plugin_manager
        self._plugin_info: Optional[PluginInfo] = None
    
    @property
    def name(self) -> str:
        """Get server name"""
        return self.config.name
    
    @property
    def server_type(self) -> str:
        """Get server type"""
        return self.config.server_type
    
    @property
    def is_enabled(self) -> bool:
        """Check if server is enabled"""
        return self.config.enabled
    
    def get_plugin_info(self) -> Optional[PluginInfo]:
        """Get associated plugin information"""
        if self._plugin_info is None:
            self._plugin_info = self.plugin_manager.get_plugin_info(self.config.plugin_name)
        return self._plugin_info
    
    async def execute_task(
        self,
        task: FilmetoTask
    ) -> Union[TaskProgress, TaskResult]:
        """
        Execute a task through the server's plugin.
        
        Args:
            task: Task to execute
            
        Yields:
            TaskProgress: Progress updates
            TaskResult: Final result
        """
        if not self.is_enabled:
            raise Exception(f"Server '{self.name}' is disabled")
        
        # Get plugin
        plugin = await self.plugin_manager.get_plugin(self.config.plugin_name)
        
        # Inject server-specific parameters
        if self.config.parameters:
            task.metadata["server_config"] = self.config.parameters
        
        # Send task to plugin
        await plugin.send_task(task)
        
        # Receive and yield messages
        async for message in plugin.receive_messages():
            yield message
    
    def __repr__(self) -> str:
        return f"Server(name={self.name}, type={self.server_type}, enabled={self.is_enabled})"


class ServerManager:
    """
    Manages server instances and task routing.

    Provides CRUD operations for servers and routes tasks to appropriate
    servers based on routing rules.
    """
    _instance = None
    _initialized = False  # Flag to track if the instance has been initialized
    _workspace_path = None

    def __new__(cls, workspace_path: str, plugin_manager: Optional[PluginManager] = None):
        """
        Create or return the singleton instance of ServerManager.
        """
        if cls._instance is None:
            cls._instance = super(ServerManager, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        workspace_path: str,
        plugin_manager: Optional[PluginManager] = None
    ):
        """
        Initialize server manager (only once).

        Args:
            workspace_path: Path to workspace root
            plugin_manager: Plugin manager instance (creates new if None)
        """
        # Check if we need to reinitialize because workspace path has changed
        if self._initialized and str(self._workspace_path) != str(workspace_path):
            print(f"⚠️ ServerManager workspace path changed from {self._workspace_path} to {workspace_path}")
            # For singleton, we'll stick with the first workspace path
            # This might need to be handled differently based on requirements
            return

        # Only initialize once
        if self._initialized:
            return

        self.workspace_path = Path(workspace_path)
        self._workspace_path = self.workspace_path  # Store for comparison later
        self.servers_dir = self.workspace_path / "servers"
        self.router_config_path = self.servers_dir / "server_router.yaml"

        # Initialize plugin manager
        if plugin_manager is None:
            self.plugin_manager = PluginManager()
            self.plugin_manager.discover_plugins()
        else:
            self.plugin_manager = plugin_manager

        # Server instances
        self.servers: Dict[str, Server] = {}

        # Routing rules
        self.routing_rules: List[RoutingRule] = []

        # Initialize
        self._ensure_directories()
        self.cleanup_old_configs()  # Clean up old configurations first
        self._init_default_servers()
        self._load_servers()
        self._load_routing_rules()

        # Mark as initialized
        self._initialized = True

    @classmethod
    def get_instance(cls) -> Optional['ServerManager']:
        """
        Get the singleton instance of ServerManager.

        Returns:
            ServerManager instance if it exists, None otherwise
        """
        return cls._instance
    
    def _ensure_directories(self):
        """Ensure server directories exist"""
        self.servers_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_default_servers(self):
        """Initialize default servers (local and filmeto) if they don't exist"""
        # Default local server
        local_server_dir = self.servers_dir / "local"
        local_config_path = local_server_dir / "server.yaml"

        if not local_config_path.exists():
            local_config = ServerConfig(
                name="local",
                server_type="local",
                plugin_name="Local Server",  # Default local plugin
                description="Local AIGC service running on this machine",
                enabled=True,
                endpoint="http://localhost:8188",
            )
            local_config.save_to_file(str(local_config_path))
            print(f"✅ Created default server: local")

        # Default filmeto server
        filmeto_server_dir = self.servers_dir / "filmeto"
        filmeto_config_path = filmeto_server_dir / "server.yaml"

        if not filmeto_config_path.exists():
            filmeto_config = ServerConfig(
                name="filmeto",
                server_type="filmeto",
                plugin_name="Filmeto Server",  # Default filmeto plugin
                description="Filmeto built-in AIGC service",
                enabled=True,
            )
            filmeto_config.save_to_file(str(filmeto_config_path))
            print(f"✅ Created default server: filmeto")

        # Default routing rules
        if not self.router_config_path.exists():
            default_rules = {
                "routing_rules": [
                    {
                        "name": "default_local",
                        "priority": 0,
                        "conditions": {},
                        "server_name": "local",
                        "fallback_servers": ["filmeto"],
                        "enabled": True,
                    }
                ]
            }
            with open(self.router_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_rules, f, allow_unicode=True, sort_keys=False)
            print(f"✅ Created default routing rules")

    def cleanup_old_configs(self):
        """Clean up any old or invalid plugin configurations in the workspace"""
        if not self.servers_dir.exists():
            return

        # Get list of all plugin directories
        all_plugin_dirs = [d for d in self.servers_dir.iterdir() if d.is_dir()]

        for plugin_dir in all_plugin_dirs:
            # Skip default servers
            if plugin_dir.name in ["local", "filmeto"]:
                continue

            config_path = plugin_dir / "server.yaml"
            if config_path.exists():
                try:
                    # Try to load the config
                    config = ServerConfig.load_from_file(str(config_path))

                    # If we can load it, it should be valid
                    print(f"✅ Valid config found for: {config.name}")
                except Exception as e:
                    # If there's an error loading the config, delete the entire directory
                    import shutil
                    print(f"❌ Invalid config in {plugin_dir.name}: {e} - removing")
                    shutil.rmtree(plugin_dir)
                    print(f"🗑️ Removed invalid server config: {plugin_dir.name}")
    
    def _load_servers(self):
        """Load all server configurations"""
        if not self.servers_dir.exists():
            return
        
        for server_dir in self.servers_dir.iterdir():
            if not server_dir.is_dir():
                continue
            
            config_path = server_dir / "server.yaml"
            if not config_path.exists():
                continue
            
            try:
                config = ServerConfig.load_from_file(str(config_path))
                server = Server(config, self.plugin_manager)
                self.servers[config.name] = server
                print(f"✅ Loaded server: {config.name} ({config.server_type})")
            except Exception as e:
                print(f"❌ Failed to load server from {server_dir}: {e}")
    
    def _load_routing_rules(self):
        """Load routing rules from configuration"""
        if not self.router_config_path.exists():
            return
        
        try:
            with open(self.router_config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            rules_data = data.get("routing_rules", [])
            self.routing_rules = [RoutingRule.from_dict(rule) for rule in rules_data]
            
            # Sort by priority (higher first)
            self.routing_rules.sort(key=lambda r: r.priority, reverse=True)
            
            print(f"✅ Loaded {len(self.routing_rules)} routing rules")
        except Exception as e:
            print(f"❌ Failed to load routing rules: {e}")
    
    def _save_routing_rules(self):
        """Save routing rules to configuration"""
        rules_data = {
            "routing_rules": [rule.to_dict() for rule in self.routing_rules]
        }
        with open(self.router_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(rules_data, f, allow_unicode=True, sort_keys=False)
    
    # CRUD Operations
    
    def add_server(self, config: ServerConfig) -> Server:
        """
        Add a new server.
        
        Args:
            config: Server configuration
            
        Returns:
            Created server instance
            
        Raises:
            ValueError: If server name already exists
        """
        if config.name in self.servers:
            raise ValueError(f"Server '{config.name}' already exists")
        
        # Verify plugin exists
        plugin_info = self.plugin_manager.get_plugin_info(config.plugin_name)
        if plugin_info is None:
            raise ValueError(f"Plugin '{config.plugin_name}' not found")
        
        # Save configuration
        server_dir = self.servers_dir / config.name
        config_path = server_dir / "server.yaml"
        config.save_to_file(str(config_path))
        
        # Create server instance
        server = Server(config, self.plugin_manager)
        self.servers[config.name] = server
        
        print(f"✅ Added server: {config.name}")
        return server
    
    def get_server(self, name: str) -> Optional[Server]:
        """
        Get server by name.
        
        Args:
            name: Server name
            
        Returns:
            Server instance or None if not found
        """
        return self.servers.get(name)
    
    def list_servers(self) -> List[Server]:
        """
        List all servers.
        
        Returns:
            List of server instances
        """
        return list(self.servers.values())
    
    def update_server(self, name: str, config: ServerConfig) -> Server:
        """
        Update server configuration.
        
        Args:
            name: Server name
            config: New configuration
            
        Returns:
            Updated server instance
            
        Raises:
            ValueError: If server not found
        """
        if name not in self.servers:
            raise ValueError(f"Server '{name}' not found")
        
        # Update timestamp
        config.updated_at = datetime.now()
        
        # Save configuration
        server_dir = self.servers_dir / name
        config_path = server_dir / "server.yaml"
        config.save_to_file(str(config_path))
        
        # Update server instance
        server = Server(config, self.plugin_manager)
        self.servers[name] = server
        
        print(f"✅ Updated server: {name}")
        return server
    
    def delete_server(self, name: str):
        """
        Delete a server.
        
        Args:
            name: Server name
            
        Raises:
            ValueError: If server not found or is a default server
        """
        if name not in self.servers:
            raise ValueError(f"Server '{name}' not found")
        
        # Prevent deletion of default servers
        if name in ["local", "filmeto"]:
            raise ValueError(f"Cannot delete default server '{name}'")
        
        # Remove from memory
        del self.servers[name]
        
        # Delete directory
        server_dir = self.servers_dir / name
        if server_dir.exists():
            import shutil
            shutil.rmtree(server_dir)
        
        print(f"✅ Deleted server: {name}")
    
    # Routing Operations
    
    def add_routing_rule(self, rule: RoutingRule):
        """Add a routing rule"""
        self.routing_rules.append(rule)
        self.routing_rules.sort(key=lambda r: r.priority, reverse=True)
        self._save_routing_rules()
        print(f"✅ Added routing rule: {rule.name}")
    
    def remove_routing_rule(self, name: str):
        """Remove a routing rule by name"""
        self.routing_rules = [r for r in self.routing_rules if r.name != name]
        self._save_routing_rules()
        print(f"✅ Removed routing rule: {name}")
    
    def get_routing_rules(self) -> List[RoutingRule]:
        """Get all routing rules"""
        return self.routing_rules.copy()
    
    def route_task(self, task: FilmetoTask) -> Optional[Server]:
        """
        Route a task to appropriate server based on routing rules.
        
        Args:
            task: Task to route
            
        Returns:
            Server instance or None if no matching server
        """
        # Try each rule in priority order
        for rule in self.routing_rules:
            if rule.matches(task):
                server = self.get_server(rule.server_name)
                if server and server.is_enabled:
                    return server
        
        # No matching rule, try default server
        default_server = self.get_server("local")
        if default_server and default_server.is_enabled:
            return default_server
        
        return None
    
    def route_task_with_fallback(self, task: FilmetoTask) -> List[Server]:
        """
        Route a task and return list of servers including fallbacks.
        
        Args:
            task: Task to route
            
        Returns:
            List of servers (primary + fallbacks)
        """
        servers = []
        
        # Find matching rule
        for rule in self.routing_rules:
            if rule.matches(task):
                # Add primary server
                primary = self.get_server(rule.server_name)
                if primary and primary.is_enabled:
                    servers.append(primary)
                
                # Add fallback servers
                for fallback_name in rule.fallback_servers:
                    fallback = self.get_server(fallback_name)
                    if fallback and fallback.is_enabled:
                        servers.append(fallback)
                
                break
        
        # If no match, use default
        if not servers:
            default = self.get_server("local")
            if default and default.is_enabled:
                servers.append(default)
        
        return servers
    
    async def execute_task_with_routing(
        self,
        task: FilmetoTask,
        use_fallback: bool = True
    ):
        """
        Execute task with automatic routing and fallback.
        
        Args:
            task: Task to execute
            use_fallback: Whether to try fallback servers on failure
            
        Yields:
            TaskProgress: Progress updates
            TaskResult: Final result
        """
        if use_fallback:
            servers = self.route_task_with_fallback(task)
        else:
            primary = self.route_task(task)
            servers = [primary] if primary else []
        
        if not servers:
            yield TaskResult(
                task_id=task.task_id,
                status="error",
                error_message="No available server found for task"
            )
            return
        
        last_error = None
        
        # Try each server in order
        for server in servers:
            try:
                print(f"🎯 Routing task {task.task_id} to server: {server.name}")
                
                async for message in server.execute_task(task):
                    yield message
                    
                    # If we got a result, we're done
                    if isinstance(message, dict) and "result" in message:
                        return
                
                # Task completed successfully
                return
                
            except Exception as e:
                last_error = e
                print(f"❌ Server {server.name} failed: {e}")
                continue
        
        # All servers failed
        yield TaskResult(
            task_id=task.task_id,
            status="error",
            error_message=f"All servers failed. Last error: {str(last_error)}"
        )
    
    def list_available_server_types(self) -> List[str]:
        """
        List available server types based on available plugins.
        
        Returns:
            List of server type names
        """
        plugins = self.plugin_manager.list_plugins()
        return list(set(plugin.engine for plugin in plugins if plugin.engine))
    
    def list_available_plugins(self) -> List['PluginInfo']:
        """
        List all available plugins that can be used to create servers.

        Returns:
            List of PluginInfo objects
        """
        return self.plugin_manager.list_plugins()

    def get_plugin_directory(self, plugin_name: str) -> Optional[Path]:
        """
        Find the plugin directory based on plugin name.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Path to plugin directory or None if not found
        """
        # First try to match by plugin name as stored in plugin config
        for plugin_info in self.plugin_manager.list_plugins():
            if plugin_info.name.lower() == plugin_name.lower():
                return plugin_info.plugin_path

        # If not found, try to match by directory name (fallback)
        plugins_dir = self.plugin_manager.plugins_dir
        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir():
                # Check if this directory has a plugin.yaml with matching name
                config_file = plugin_dir / "plugin.yaml"
                if config_file.exists():
                    import yaml
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = yaml.safe_load(f)
                        if config.get('name', '').lower() == plugin_name.lower():
                            return plugin_dir
                    except:
                        continue

        return None

    def load_plugin_instance_for_ui(self, plugin_dir: Path):
        """
        Load and instantiate the plugin class from its main module for UI purposes.

        Args:
            plugin_dir: Path to the plugin directory

        Returns:
            Plugin instance or None if failed
        """
        import sys
        import importlib.util

        main_file = plugin_dir / "main.py"
        if not main_file.exists():
            return None

        # Create a unique module name to avoid conflicts
        plugin_name = plugin_dir.name
        module_name = f"plugin_{plugin_name.replace('-', '_')}_config_ui"

        # Check if module already exists in sys.modules
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            # Import the plugin module
            spec = importlib.util.spec_from_file_location(module_name, main_file)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

        plugin_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and
                hasattr(obj, 'init_ui') and
                hasattr(obj, 'get_plugin_info') and
                name != 'BaseServerPlugin'):
                plugin_class = obj
                break

        if not plugin_class:
            return None

        # Create plugin instance - this will be for UI only, not for actual task execution
        try:
            plugin_instance = plugin_class()
            return plugin_instance
        except Exception as e:
            print(f"Failed to instantiate plugin class {plugin_class.__name__}: {e}")
            return None

    def get_plugin_ui_widget(self, plugin_name: str, server_config_dict: Optional[Dict[str, Any]] = None):
        """
        Get custom UI widget from a plugin for configuration purposes.

        Args:
            plugin_name: Name of the plugin
            server_config_dict: Optional server configuration dict for editing existing server

        Returns:
            Custom UI widget or None if not available
        """
        try:
            # Get the plugin directory based on plugin name
            plugin_dir = self.get_plugin_directory(plugin_name)

            if not plugin_dir:
                return None

            # Import and instantiate the plugin class to get custom UI
            plugin_instance = self.load_plugin_instance_for_ui(plugin_dir)

            if not plugin_instance:
                return None

            # Call init_ui method with workspace path and server config
            # Note: workspace_path would normally be provided by the caller
            custom_widget = plugin_instance.init_ui(self.workspace_path, server_config_dict)

            return custom_widget

        except Exception as e:
            print(f"Failed to get custom UI from plugin: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def cleanup(self):
        """Cleanup resources"""
        await self.plugin_manager.stop_all_plugins()


if __name__ == "__main__":
    # Example usage
    import sys
    
    async def test_server_manager():
        # Get workspace path
        workspace_path = os.path.join(os.path.dirname(__file__), "..", "workspace", "demo")
        
        # Create server manager
        manager = ServerManager(workspace_path)
        
        # List servers
        print("\n📋 Available servers:")
        for server in manager.list_servers():
            print(f"  - {server.name} ({server.server_type}): enabled={server.is_enabled}")
        
        # List routing rules
        print("\n📋 Routing rules:")
        for rule in manager.get_routing_rules():
            print(f"  - {rule.name}: {rule.server_name} (priority={rule.priority})")
        
        # List available server types
        print("\n📋 Available server types (from plugins):")
        for server_type in manager.list_available_server_types():
            print(f"  - {server_type}")
        
        # Cleanup
        await manager.cleanup()
    
    # Run test
    asyncio.run(test_server_manager())
