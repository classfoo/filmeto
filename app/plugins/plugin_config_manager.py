"""
Plugin Configuration Manager

Manages loading, validation, and persistence of service plugin configurations.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from app.spi.service import ConfigSchema, ConfigGroup, ConfigField
from utils.yaml_utils import load_yaml, save_yaml

logger = logging.getLogger(__name__)


class PluginConfigManager:
    """
    Manages service plugin configurations.
    
    Handles loading, validation, and saving of plugin-specific YAML configuration files.
    """

    def __init__(self):
        """Initialize the configuration manager"""
        self._configs: Dict[str, Dict[str, Any]] = {}  # service_id -> config data
        self._schemas: Dict[str, ConfigSchema] = {}  # service_id -> config schema

    def register_schema(self, service_id: str, schema: ConfigSchema):
        """
        Register a configuration schema for a service.
        
        Args:
            service_id: Unique identifier for the service
            schema: Configuration schema definition
        """
        self._schemas[service_id] = schema
        logger.info(f"✅ Registered config schema for service: {service_id}")

    def load_config(self, service_id: str, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            service_id: Unique identifier for the service
            config_path: Path to the configuration YAML file
            
        Returns:
            Dictionary containing configuration data
        """
        try:
            # Ensure config file exists
            if not os.path.exists(config_path):
                logger.warning(f"⚠️ Config file not found: {config_path}")
                # Create from schema defaults
                config_data = self._create_default_config(service_id)
                self._save_config_file(config_path, config_data)
            else:
                config_data = load_yaml(config_path)

            # Parse and store configuration
            parsed_config = self._parse_config(service_id, config_data)
            self._configs[service_id] = parsed_config

            logger.info(f"✅ Loaded config for service: {service_id}")
            return parsed_config

        except Exception as e:
            logger.error(f"❌ Error loading config for {service_id}: {e}")
            # Return default config on error
            return self._create_default_config(service_id)

    def save_config(self, service_id: str, config_path: str, config_data: Dict[str, Any]) -> bool:
        """
        Save configuration to YAML file.
        
        Args:
            service_id: Unique identifier for the service
            config_path: Path to the configuration YAML file
            config_data: Configuration data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate configuration
            if not self.validate_config(service_id, config_data):
                logger.warning(f"⚠️ Config validation failed for {service_id}")
                return False

            # Build YAML structure from config data
            yaml_data = self._build_yaml_structure(service_id, config_data)

            # Save to file
            self._save_config_file(config_path, yaml_data)

            # Update cached config
            self._configs[service_id] = config_data

            logger.info(f"✅ Saved config for service: {service_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving config for {service_id}: {e}")
            return False

    def get_config(self, service_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current configuration for a service.
        
        Args:
            service_id: Unique identifier for the service
            
        Returns:
            Configuration dictionary or None if not loaded
        """
        return self._configs.get(service_id)

    def update_config(self, service_id: str, key: str, value: Any) -> bool:
        """
        Update a specific configuration value.
        
        Args:
            service_id: Unique identifier for the service
            key: Configuration key in format "group.field"
            value: New value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if service_id not in self._configs:
                logger.warning(f"⚠️ No config loaded for service: {service_id}")
                return False

            parts = key.split('.')
            if len(parts) != 2:
                logger.warning(f"⚠️ Invalid config key format: {key}")
                return False

            group_name, field_name = parts

            # Validate value against schema
            if not self._validate_field_value(service_id, group_name, field_name, value):
                logger.warning(f"⚠️ Validation failed for {key} = {value}")
                return False

            # Update config
            if group_name not in self._configs[service_id]:
                self._configs[service_id][group_name] = {}

            self._configs[service_id][group_name][field_name] = value
            return True

        except Exception as e:
            logger.error(f"❌ Error updating config {key}: {e}")
            return False

    def validate_config(self, service_id: str, config_data: Dict[str, Any]) -> bool:
        """
        Validate configuration against schema.
        
        Args:
            service_id: Unique identifier for the service
            config_data: Configuration data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if service_id not in self._schemas:
            logger.warning(f"⚠️ No schema registered for service: {service_id}")
            return False

        schema = self._schemas[service_id]

        try:
            # Validate all groups and fields
            for group in schema.groups:
                group_data = config_data.get(group.name, {})

                for field in group.fields:
                    # Check required fields
                    if field.required and field.name not in group_data:
                        logger.warning(f"⚠️ Required field missing: {group.name}.{field.name}")
                        return False

                    # Validate field value if present
                    if field.name in group_data:
                        value = group_data[field.name]
                        if not self._validate_field_value(service_id, group.name, field.name, value):
                            return False

            return True

        except Exception as e:
            logger.error(f"❌ Validation error for {service_id}: {e}")
            return False

    def reset_to_defaults(self, service_id: str) -> Dict[str, Any]:
        """
        Reset configuration to default values.
        
        Args:
            service_id: Unique identifier for the service
            
        Returns:
            Default configuration dictionary
        """
        default_config = self._create_default_config(service_id)
        self._configs[service_id] = default_config
        return default_config

    def _parse_config(self, service_id: str, yaml_data: Dict) -> Dict[str, Any]:
        """Parse YAML data into configuration structure"""
        config = {}

        groups_data = yaml_data.get('groups', [])
        for group_data in groups_data:
            group_name = group_data.get('name')
            if not group_name:
                continue

            config[group_name] = {}

            fields_data = group_data.get('fields', [])
            for field_data in fields_data:
                field_name = field_data.get('name')
                if field_name:
                    config[group_name][field_name] = field_data.get('default')

        return config

    def _create_default_config(self, service_id: str) -> Dict[str, Any]:
        """Create default configuration from schema"""
        if service_id not in self._schemas:
            return {}

        schema = self._schemas[service_id]
        config = {}

        for group in schema.groups:
            config[group.name] = {}
            for field in group.fields:
                config[group.name][field.name] = field.default

        return config

    def _build_yaml_structure(self, service_id: str, config_data: Dict[str, Any]) -> Dict:
        """Build YAML structure from configuration data"""
        if service_id not in self._schemas:
            return {}

        schema = self._schemas[service_id]
        groups_data = []

        for group in schema.groups:
            group_dict = {
                'name': group.name,
                'label': group.label,
                'fields': []
            }

            group_config = config_data.get(group.name, {})

            for field in group.fields:
                field_dict = {
                    'name': field.name,
                    'label': field.label,
                    'type': field.type,
                    'default': group_config.get(field.name, field.default),
                    'description': field.description
                }

                if field.required:
                    field_dict['required'] = field.required

                if field.validation:
                    field_dict['validation'] = field.validation

                if field.options:
                    field_dict['options'] = field.options

                group_dict['fields'].append(field_dict)

            groups_data.append(group_dict)

        return {
            'version': schema.version,
            'groups': groups_data
        }

    def _save_config_file(self, config_path: str, data: Dict):
        """Save configuration data to YAML file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # Save YAML
        save_yaml(config_path, data)

    def _validate_field_value(self, service_id: str, group_name: str, field_name: str, value: Any) -> bool:
        """Validate a field value against its schema"""
        if service_id not in self._schemas:
            return False

        schema = self._schemas[service_id]

        # Find the field definition
        field = None
        for group in schema.groups:
            if group.name == group_name:
                for f in group.fields:
                    if f.name == field_name:
                        field = f
                        break
                break

        if not field:
            logger.warning(f"⚠️ Field not found in schema: {group_name}.{field_name}")
            return False

        # Type-specific validation
        if field.type == 'text':
            if not isinstance(value, str):
                return False
            if field.validation:
                min_len = field.validation.get('min_length', 0)
                max_len = field.validation.get('max_length', float('inf'))
                if len(value) < min_len or len(value) > max_len:
                    return False

        elif field.type == 'number':
            if not isinstance(value, (int, float)):
                return False
            if field.validation:
                min_val = field.validation.get('min', float('-inf'))
                max_val = field.validation.get('max', float('inf'))
                if value < min_val or value > max_val:
                    return False

        elif field.type == 'boolean':
            if not isinstance(value, bool):
                return False

        elif field.type == 'select':
            if field.options:
                valid_values = [opt.get('value') for opt in field.options]
                if value not in valid_values:
                    return False

        elif field.type == 'password':
            if not isinstance(value, str):
                return False

        return True
