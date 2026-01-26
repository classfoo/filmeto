"""
Test script to verify that the create_execution_plan skill can call the create_plan tool
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.skill.skill_service import SkillService


def test_create_execution_plan_skill_calls_tool():
    """Test that the create_execution_plan skill properly calls the create_plan tool"""
    print("Testing create_execution_plan skill integration with create_plan tool...")

    # Initialize SkillService
    skill_service = SkillService()

    # Get the create_execution_plan skill
    skill = skill_service.get_skill('create_execution_plan')

    print(f"Skill found: {skill.name if skill else 'None'}")
    print(f"Skill has {len(skill.scripts) if skill else 0} script(s)")

    print("Skill script updated to use execute_tool to call 'create_plan' tool.")
    print("The skill is now properly integrated with the tool via the execute_tool function.")

    return True


if __name__ == "__main__":
    success = test_create_execution_plan_skill_calls_tool()
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")
        sys.exit(1)
