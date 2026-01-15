"""
Example usage of the SkillService in Filmeto Agent.
"""
import sys
import os
import tempfile

# Add the project root to the Python path
sys.path.insert(0, '/root/filmeto')

from agent.skill.skill_service import SkillService


def example_basic_usage():
    """Example showing basic usage of SkillService."""
    print("=== Example: Basic SkillService Usage ===")
    
    # Initialize SkillService without a workspace (will only load system skills)
    skill_service = SkillService()
    
    # Get all available skills
    skill_names = skill_service.get_skill_names()
    print(f"Available skills: {skill_names}")
    
    # Get a specific skill
    if skill_names:
        skill_name = skill_names[0]
        skill = skill_service.get_skill(skill_name)
        
        if skill:
            print(f"Skill name: {skill.name}")
            print(f"Description: {skill.description}")
            print(f"Knowledge length: {len(skill.knowledge) if skill.knowledge else 0} characters")
            print(f"Number of scripts: {len(skill.scripts) if skill.scripts else 0}")
    
    print()


def example_with_workspace():
    """Example showing SkillService with a workspace."""
    print("=== Example: SkillService with Workspace ===")

    # Create a temporary workspace to demonstrate custom skills
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a custom skills directory
        skills_dir = os.path.join(temp_dir, "skills")
        os.makedirs(skills_dir, exist_ok=True)

        # Create a custom skill directory
        custom_skill_dir = os.path.join(skills_dir, "my_custom_skill")
        os.makedirs(custom_skill_dir, exist_ok=True)

        # Create a SKILL.md file for the custom skill
        skill_md_content = """---
name: my_custom_skill
description: A custom skill for demonstration
---

# My Custom Skill

This is a custom skill that demonstrates how users can extend the agent's capabilities.
"""
        with open(os.path.join(custom_skill_dir, "SKILL.md"), 'w') as f:
            f.write(skill_md_content)

        # Create a mock workspace object (in a real scenario, you would have an actual Workspace object)
        class MockWorkspace:
            def __init__(self, workspace_path):
                self.workspace_path = workspace_path

        workspace_obj = MockWorkspace(temp_dir)

        # Initialize SkillService with the workspace object
        skill_service = SkillService(workspace=workspace_obj)

        # Now we should have both system and custom skills
        all_skills = skill_service.get_skill_names()
        print(f"All skills (system + custom): {all_skills}")

        # Get the custom skill
        custom_skill = skill_service.get_skill("my_custom_skill")
        if custom_skill:
            print(f"Custom skill loaded: {custom_skill.name}")
            print(f"Custom skill description: {custom_skill.description}")

    print()


def example_skill_execution():
    """Example showing how to execute skill scripts."""
    print("=== Example: Executing Skill Scripts ===")
    
    # Initialize SkillService
    skill_service = SkillService()
    
    # Get the weather skill as an example
    weather_skill = skill_service.get_skill("get_weather")
    if weather_skill and weather_skill.scripts:
        print(f"Weather skill has {len(weather_skill.scripts)} script(s)")
        
        # Show script names
        for script_path in weather_skill.scripts:
            script_name = os.path.basename(script_path)
            print(f"- Script: {script_name}")
        
        # Example of how to execute a script (would need proper arguments in real usage)
        print("To execute a script: skill_service.execute_skill_script(skill_name, script_name, *args)")
    else:
        print("No scripts found for weather skill")
    
    print()


if __name__ == "__main__":
    print("SkillService Example Usage\n")
    
    example_basic_usage()
    example_with_workspace()
    example_skill_execution()
    
    print("Examples completed!")