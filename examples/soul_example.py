"""
Example usage of the Soul system in Filmeto.

This script demonstrates how to use the SoulService to manage different
AI personalities or expert profiles for film production.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.soul import SoulService


def main():
    # Initialize the SoulService
    # This will automatically load both system souls and user-defined souls
    service = SoulService()
    
    print("=== Filmeto Soul System Demo ===\n")
    
    # List all available souls
    print("Available expert souls:")
    for soul in service.get_all_souls():
        print(f"  - {soul.name}")
        print(f"    Skills: {', '.join(soul.skills[:3])}")  # Show first 3 skills
        if len(soul.skills) > 3:
            print(f"    ... and {len(soul.skills) - 3} more")
        print()
    
    # Find experts with specific skills
    print("Experts skilled in 'Visual storytelling':")
    visual_storytelling_experts = service.search_souls_by_skill("Visual storytelling")
    for expert in visual_storytelling_experts:
        print(f"  - {expert.name}")
    print()
    
    # Get detailed information about a specific soul
    kurosawa = service.get_soul_by_name("kurosawa_soul")
    if kurosawa:
        print(f"Details for {kurosawa.name}:")
        print(f"  Title: {kurosawa.metadata.get('title', 'N/A')}")
        print(f"  Specialties: {', '.join(kurosawa.metadata.get('specialties', []))}")
        print(f"  Experience: {kurosawa.metadata.get('experience', 'N/A')}")
        print()


if __name__ == "__main__":
    main()