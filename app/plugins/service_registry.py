"""
Service Registry

Manages service plugin discovery, registration, and lifecycle.
"""

import os
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type
from dataclasses import dataclass

from app.spi.service import BaseService, ServiceCapability
from app.plugins.plugin_config_manager import PluginConfigManager


@dataclass
class ServiceInfo:
    """Metadata about a registered service plugin"""
    service_id: str
    name: str
    icon: str
    service_class: Type[BaseService]
    capabilities: List[ServiceCapability]
    config_path: str
    module_path: str
    enabled: bool = True
    version: str = "1.0.0"
    description: str = ""


class ServiceRegistry:
    """
    Manages service plugin discovery, registration, and lifecycle.
    
    Provides centralized access to all available service plugins.
    """

    def __init__(self, workspace=None):
        """
        Initialize the service registry.
        
        Args:
            workspace: Optional workspace reference for context
        """
        self.workspace = workspace
        self._registry: Dict[str, ServiceInfo] = {}
        self._instances: Dict[str, BaseService] = {}
        self._config_manager = PluginConfigManager()

    def discover_services(self):
        """
        Scan and register available service plugins.
        
        Searches the app/plugins/services/ directory for service implementations.
        """
        # Get services directory
        current_dir = Path(__file__).parent  # app/plugins/
        services_dir = current_dir / "services"

        if not services_dir.exists():
            print(f"⚠️ Services directory not found: {services_dir}")
            print(f"Creating services directory...")
            services_dir.mkdir(parents=True, exist_ok=True)
            return

        print(f"🔍 Discovering service plugins in: {services_dir}")

        # Scan each subdirectory in services/
        for service_dir in services_dir.iterdir():
            if not service_dir.is_dir() or service_dir.name.startswith('_'):
                continue

            # Try to import the service module
            service_module_path = f"app.plugins.services.{service_dir.name}.{service_dir.name}_service"

            try:
                module = importlib.import_module(service_module_path)

                # Find BaseService subclasses in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseService) and obj != BaseService:
                        # Register the service
                        service_info = self._create_service_info(obj, service_module_path)
                        if service_info:
                            self._registry[service_info.service_id] = service_info
                            
                            # Register config schema
                            config_schema = obj.get_config_schema()
                            self._config_manager.register_schema(service_info.service_id, config_schema)
                            
                            # Load configuration
                            self._config_manager.load_config(service_info.service_id, service_info.config_path)
                            
                            print(f"✅ Registered service: {service_info.service_id} ({service_info.name})")
                        break

            except ModuleNotFoundError:
                print(f"⚠️ Service module not found: {service_module_path}")
            except Exception as e:
                print(f"❌ Failed to load service from {service_module_path}: {e}")

    def get_service_by_id(self, service_id: str) -> Optional[BaseService]:
        """
        Retrieve service instance by identifier.
        
        Args:
            service_id: Unique identifier for the service
            
        Returns:
            Service instance or None if not found
        """
        if service_id not in self._registry:
            print(f"⚠️ Service not found: {service_id}")
            return None

        # Return cached instance if exists
        if service_id in self._instances:
            return self._instances[service_id]

        # Create new instance
        service_info = self._registry[service_id]
        try:
            instance = service_info.service_class()
            self._instances[service_id] = instance
            return instance
        except Exception as e:
            print(f"❌ Failed to instantiate service {service_id}: {e}")
            return None

    def get_all_services(self) -> List[ServiceInfo]:
        """
        Return list of all registered services.
        
        Returns:
            List of ServiceInfo objects
        """
        return list(self._registry.values())

    def get_services_by_capability(self, capability_id: str) -> List[ServiceInfo]:
        """
        Find services supporting specific capability.
        
        Args:
            capability_id: The capability to search for (e.g., "text2image")
            
        Returns:
            List of ServiceInfo objects that support the capability
        """
        matching_services = []

        for service_info in self._registry.values():
            if not service_info.enabled:
                continue

            for capability in service_info.capabilities:
                if capability.capability_id == capability_id:
                    matching_services.append(service_info)
                    break

        return matching_services

    def reload_service(self, service_id: str) -> bool:
        """
        Reload service configuration and reinitialize.
        
        Args:
            service_id: Unique identifier for the service
            
        Returns:
            True if successful, False otherwise
        """
        if service_id not in self._registry:
            print(f"⚠️ Service not found: {service_id}")
            return False

        try:
            service_info = self._registry[service_id]
            
            # Reload configuration
            self._config_manager.load_config(service_id, service_info.config_path)
            
            # Remove cached instance to force recreation
            if service_id in self._instances:
                del self._instances[service_id]
            
            print(f"✅ Reloaded service: {service_id}")
            return True

        except Exception as e:
            print(f"❌ Failed to reload service {service_id}: {e}")
            return False

    def enable_service(self, service_id: str) -> bool:
        """
        Activate a disabled service.
        
        Args:
            service_id: Unique identifier for the service
            
        Returns:
            True if successful, False otherwise
        """
        if service_id not in self._registry:
            print(f"⚠️ Service not found: {service_id}")
            return False

        self._registry[service_id].enabled = True
        print(f"✅ Enabled service: {service_id}")
        return True

    def disable_service(self, service_id: str) -> bool:
        """
        Deactivate a service.
        
        Args:
            service_id: Unique identifier for the service
            
        Returns:
            True if successful, False otherwise
        """
        if service_id not in self._registry:
            print(f"⚠️ Service not found: {service_id}")
            return False

        self._registry[service_id].enabled = False
        
        # Remove cached instance
        if service_id in self._instances:
            del self._instances[service_id]
        
        print(f"✅ Disabled service: {service_id}")
        return True

    def get_config_manager(self) -> PluginConfigManager:
        """
        Get the configuration manager instance.
        
        Returns:
            PluginConfigManager instance
        """
        return self._config_manager

    def get_service_info(self, service_id: str) -> Optional[ServiceInfo]:
        """
        Get service metadata by ID.
        
        Args:
            service_id: Unique identifier for the service
            
        Returns:
            ServiceInfo object or None if not found
        """
        return self._registry.get(service_id)

    def _create_service_info(self, service_class: Type[BaseService], module_path: str) -> Optional[ServiceInfo]:
        """Create ServiceInfo from service class"""
        try:
            service_id = service_class.get_service_name()
            name = service_class.get_service_display_name()
            icon = service_class.get_service_icon()
            capabilities = service_class.get_capabilities()
            config_path = service_class.get_config_path()
            version = service_class.get_service_version()
            description = service_class.get_service_description()

            return ServiceInfo(
                service_id=service_id,
                name=name,
                icon=icon,
                service_class=service_class,
                capabilities=capabilities,
                config_path=config_path,
                module_path=module_path,
                enabled=True,
                version=version,
                description=description
            )

        except Exception as e:
            print(f"❌ Failed to create service info: {e}")
            return None
