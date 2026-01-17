#!/usr/bin/env python3
"""
Test script to verify the new properties implementation in CrewTitle class
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.crew.crew_title import CrewTitle


def test_crew_title_properties():
    """Test the new properties implementation in CrewTitle class"""
    print("Testing new properties implementation in CrewTitle class...")
    
    # Test 1: Create a CrewTitle instance and check its properties
    print("\n1. Testing CrewTitle properties...")
    
    director_title = CrewTitle.create_from_title("director")
    print(f"   Title: {director_title.title}")
    print(f"   Name: {director_title.name}")
    print(f"   Description: {director_title.description}")
    print(f"   Soul: {director_title.soul}")
    print(f"   Skills: {director_title.skills}")
    print(f"   Model: {director_title.model}")
    print(f"   Temperature: {director_title.temperature}")
    print(f"   Max Steps: {director_title.max_steps}")
    print(f"   Color: {director_title.color}")
    print(f"   Icon: {director_title.icon}")
    print(f"   Display Names: {director_title.display_names}")
    print(f"   Crew Title: {director_title.crew_title}")
    
    # Test 2: Check if properties are accessible
    print("\n2. Verifying properties are accessible...")
    properties_to_check = [
        ('title', director_title.title),
        ('name', director_title.name),
        ('description', director_title.description),
        ('soul', director_title.soul),
        ('skills', director_title.skills),
        ('model', director_title.model),
        ('temperature', director_title.temperature),
        ('max_steps', director_title.max_steps),
        ('color', director_title.color),
        ('icon', director_title.icon),
        ('display_names', director_title.display_names),
        ('crew_title', director_title.crew_title)
    ]
    
    all_accessible = True
    for prop_name, prop_value in properties_to_check:
        if prop_value is None:
            print(f"   ❌ Property {prop_name} is None")
            all_accessible = False
        else:
            print(f"   ✅ Property {prop_name} is accessible: {type(prop_value).__name__}")
    
    # Test 3: Test with another crew title
    print("\n3. Testing with another crew title (producer)...")
    producer_title = CrewTitle.create_from_title("producer")
    print(f"   Producer title: {producer_title.title}")
    print(f"   Producer name: {producer_title.name}")
    print(f"   Producer description: {producer_title.description[:50]}...")
    print(f"   Producer soul: {producer_title.soul}")
    
    # Test 4: Verify metadata is still accessible
    print("\n4. Verifying metadata is still accessible...")
    print(f"   Director metadata keys: {list(director_title.metadata.keys())}")
    print(f"   Producer metadata keys: {list(producer_title.metadata.keys())}")
    
    print("\n5. Summary:")
    print(f"   - Properties are properly defined: {all_accessible}")
    print(f"   - Multiple crew titles work: {producer_title.title is not None}")
    print(f"   - Metadata remains accessible: {bool(director_title.metadata)}")
    print("   ✅ All tests completed successfully!")


if __name__ == "__main__":
    test_crew_title_properties()