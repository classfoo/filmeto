import os
import time
import logging
import importlib
import inspect
from pathlib import Path
from typing import Dict, Type, Optional
from dataclasses import dataclass

from app.spi.tool import BaseTool
from app.plugins.service_registry import ServiceRegistry
from utils.i18n_utils import tr

logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """Information about a registered tool"""
    tool_id: str  # e.g. "text2img"
    name: str  # Display name
    icon: str  # Unicode icon character
    tool_class: Type[BaseTool]  # Tool class
    module_path: str  # Module path for lazy loading


class Plugins:

    def __init__(self, bot, defer_discovery: bool = False):
        self.bot = bot
        self.tools = []
        self.models = []
        self._tool_registry: Dict[str, ToolInfo] = {}
        self._service_registry = ServiceRegistry(workspace=getattr(bot, 'workspace', None))
        self._discovery_done = False
        self._defer_discovery = defer_discovery
        
        if not defer_discovery:
            self._discover_tools()
            self._discover_services()
            self._discovery_done = True
    
    def ensure_discovery(self):
        """Ensure plugins are discovered (for deferred discovery)"""
        if not self._discovery_done:
            discovery_start = time.time()
            logger.info(f"⏱️  [Plugins] Starting deferred plugin discovery...")
            
            tools_start = time.time()
            self._discover_tools()
            tools_time = (time.time() - tools_start) * 1000
            tools_count = len(self._tool_registry)
            logger.info(f"⏱️  [Plugins] Tools discovery completed in {tools_time:.2f}ms (found {tools_count} tools)")
            
            services_start = time.time()
            self._discover_services()
            services_time = (time.time() - services_start) * 1000
            logger.info(f"⏱️  [Plugins] Services discovery completed in {services_time:.2f}ms")
            
            self._discovery_done = True
            total_time = (time.time() - discovery_start) * 1000
            logger.info(f"⏱️  [Plugins] Deferred plugin discovery completed in {total_time:.2f}ms")

    def _discover_tools(self):
        """Discover and register tools from plugins/tools directory"""
        # Get tools directory
        current_dir = Path(__file__).parent  # app/plugins/
        tools_dir = current_dir / "tools"

        if not tools_dir.exists():
            print(f"Tools directory not found: {tools_dir}")
            return

        # Scan each subdirectory in tools/
        for tool_dir in tools_dir.iterdir():
            if not tool_dir.is_dir() or tool_dir.name.startswith('_'):
                continue

            # Try to import the tool module
            tool_module_path = f"app.plugins.tools.{tool_dir.name}.{tool_dir.name}"

            try:
                module = importlib.import_module(tool_module_path)

                # Find BaseTool subclasses in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseTool) and obj != BaseTool:
                        # Register the tool
                        tool_id = tool_dir.name
                        tool_info = self._create_tool_info(tool_id, obj, tool_module_path)
                        if tool_info:
                            self._tool_registry[tool_id] = tool_info
                            print(f"Registered tool: {tool_id} ({tool_info.name})")
                        break

            except Exception as e:
                print(f"Failed to load tool from {tool_module_path}: {e}")

    def _create_tool_info(self, tool_id: str, tool_class: Type[BaseTool], module_path: str) -> Optional[ToolInfo]:
        """Create ToolInfo from tool class by getting class method properties"""
        try:
            # Get tool properties from the class methods
            name = tool_class.get_tool_display_name()
            icon = tool_class.get_tool_icon()
            
            return ToolInfo(
                tool_id=tool_id,
                name=name,
                icon=icon,
                tool_class=tool_class,
                module_path=module_path
            )
        except Exception as e:
            print(f"Failed to create tool info for {tool_id}: {e}")
            return None

    def get_tool_registry(self) -> Dict[str, ToolInfo]:
        """Get all registered tools"""
        return self._tool_registry.copy()

    def get_service_registry(self) -> ServiceRegistry:
        """Get the service registry"""
        return self._service_registry

    def _discover_services(self):
        """Discover and register service plugins"""
        print("🔍 Discovering service plugins...")
        self._service_registry.discover_services()