"""
Test Service Plugin System

Simple test script to validate the service plugin architecture.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.plugins.service_registry import ServiceRegistry


def test_service_discovery():
    """Test service plugin discovery"""
    print("=" * 60)
    print("Testing Service Plugin Discovery")
    print("=" * 60)
    
    registry = ServiceRegistry()
    registry.discover_services()
    
    services = registry.get_all_services()
    
    print(f"\n✅ Discovered {len(services)} service(s):")
    for service_info in services:
        print(f"\n  📦 {service_info.name} ({service_info.service_id})")
        print(f"     Version: {service_info.version}")
        print(f"     Icon: {service_info.icon}")
        print(f"     Enabled: {service_info.enabled}")
        print(f"     Description: {service_info.description}")
        print(f"     Capabilities: {len(service_info.capabilities)}")
        
        for cap in service_info.capabilities:
            print(f"       - {cap.display_name} ({cap.capability_id})")
            print(f"         Requires prompt: {cap.requires_prompt}")
            print(f"         Requires input media: {cap.requires_input_media}")


def test_service_configuration():
    """Test service configuration loading"""
    print("\n" + "=" * 60)
    print("Testing Service Configuration")
    print("=" * 60)
    
    registry = ServiceRegistry()
    registry.discover_services()
    
    services = registry.get_all_services()
    config_manager = registry.get_config_manager()
    
    for service_info in services:
        print(f"\n  🔧 {service_info.name} Configuration:")
        
        config = config_manager.get_config(service_info.service_id)
        if config:
            for group_name, group_config in config.items():
                print(f"     [{group_name}]")
                for field_name, value in group_config.items():
                    # Mask password fields
                    if field_name in ['api_key', 'password']:
                        value = "***" if value else "(empty)"
                    print(f"       {field_name}: {value}")
        else:
            print("     No configuration loaded")


def test_capability_search():
    """Test finding services by capability"""
    print("\n" + "=" * 60)
    print("Testing Capability-Based Service Search")
    print("=" * 60)
    
    registry = ServiceRegistry()
    registry.discover_services()
    
    capabilities_to_search = ["text2image", "image_edit", "image2video", "image_analysis"]
    
    for capability_id in capabilities_to_search:
        services = registry.get_services_by_capability(capability_id)
        print(f"\n  🔍 Services supporting '{capability_id}':")
        
        if services:
            for service_info in services:
                print(f"     ✓ {service_info.name}")
        else:
            print(f"     (none)")


def test_config_schema():
    """Test configuration schema retrieval"""
    print("\n" + "=" * 60)
    print("Testing Configuration Schema")
    print("=" * 60)
    
    registry = ServiceRegistry()
    registry.discover_services()
    
    services = registry.get_all_services()
    
    for service_info in services[:1]:  # Test first service only
        print(f"\n  📋 {service_info.name} Configuration Schema:")
        
        schema = service_info.service_class.get_config_schema()
        print(f"     Schema Version: {schema.version}")
        print(f"     Configuration Groups: {len(schema.groups)}")
        
        for group in schema.groups:
            print(f"\n     Group: {group.label} ({group.name})")
            print(f"     Fields: {len(group.fields)}")
            
            for field in group.fields:
                req = " *" if field.required else ""
                print(f"       - {field.label}{req} ({field.name})")
                print(f"         Type: {field.type}")
                print(f"         Default: {field.default if field.type != 'password' else '***'}")
                if field.validation:
                    print(f"         Validation: {field.validation}")


def main():
    """Run all tests"""
    print("\n" + "🧪 Service Plugin System Tests")
    print("\n")
    
    try:
        test_service_discovery()
        test_service_configuration()
        test_capability_search()
        test_config_schema()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
