"""
Unit test for SkillExecutor using ToolService execute_script functionality
"""
import unittest
import sys
import os
from unittest.mock import MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.skill.skill_executor import SkillExecutor, SkillContext
from agent.skill.skill_service import Skill
from agent.skill.skill_service import SkillParameter


class MockProject:
    """Mock project object for testing"""
    def __init__(self):
        self.project_name = "TestProject"
        self.project_path = "/tmp/test_project"


class MockWorkspace:
    """Mock workspace object for testing"""
    def __init__(self):
        self.workspace_path = "/tmp/test_workspace"


class TestSkillExecutorWithToolService(unittest.TestCase):
    """Test cases for SkillExecutor using ToolService execute_script"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.executor = SkillExecutor()
        
        # Create a mock skill with a simple script
        self.mock_skill = Skill(
            name="test-skill",
            description="A test skill",
            knowledge="This is a test skill for verification.",
            skill_path="/tmp/test_skill_path",
            parameters=[
                SkillParameter(
                    name="input_text",
                    param_type="string",
                    required=True,
                    description="Input text for the skill"
                )
            ],
            scripts=[]
        )
        
        # Create a simple test script content
        self.test_script_content = '''
import sys
import json
import argparse

def execute(context, input_text="World"):
    """Simple test function that returns a greeting."""
    return {
        "success": True,
        "output": f"Hello, {input_text}!",
        "message": f"Greeted {input_text} successfully"
    }

def main():
    """Main function for script execution."""
    # Parse command line arguments
    # Handle both named arguments and potential positional arguments
    args = sys.argv[1:]  # Skip script name

    input_text = "World"  # default value
    project_path = None

    i = 0
    while i < len(args):
        if args[i] == '--input-text' and i + 1 < len(args):
            input_text = args[i + 1]
            i += 2
        elif args[i] == '--project-path' and i + 1 < len(args):
            project_path = args[i + 1]
            i += 2
        else:
            # Skip unknown arguments
            i += 1

    # Create a minimal context
    context = {"project_path": project_path} if project_path else {}

    # Execute the function and print the result
    result = execute(context, input_text)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
'''
        
        # Write the test script to a temporary file
        self.test_script_path = "/tmp/test_skill_script.py"
        with open(self.test_script_path, 'w', encoding='utf-8') as f:
            f.write(self.test_script_content)
        
        # Add the script path to the mock skill
        self.mock_skill.scripts = [self.test_script_path]

    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.test_script_path):
            os.remove(self.test_script_path)

    def test_execute_skill_via_tool_service(self):
        """Test that SkillExecutor can execute a skill via ToolService"""
        # Create a context for the skill
        context = SkillContext(
            workspace=MockWorkspace(),
            project=MockProject()
        )

        # Execute the skill with arguments
        args = {"input_text": "ToolService"}
        result = self.executor.execute_skill(self.mock_skill, context, args)

        # Verify the result is a string
        self.assertIsInstance(result, str)
        self.assertIn("Hello, ToolService!", result)

    def test_execute_skill_with_empty_args(self):
        """Test executing a skill with empty arguments (should use defaults)"""
        context = SkillContext(
            workspace=MockWorkspace(),
            project=MockProject()
        )

        # Execute with no args (should use default "World")
        result = self.executor.execute_skill(self.mock_skill, context, {})

        # Verify the result uses the default value
        self.assertIsInstance(result, str)
        self.assertIn("Hello, World!", result)

    def test_tool_service_integration(self):
        """Test that ToolService is being used in the execution"""
        # Verify that the executor has a ToolService instance
        self.assertIsNotNone(self.executor.tool_service)

        # Mock the ToolService's execute_script method to verify it's called
        original_execute_script = self.executor.tool_service.execute_script
        self.executor.tool_service.execute_script = MagicMock(return_value="Mocked result")

        context = SkillContext(
            workspace=MockWorkspace(),
            project=MockProject()
        )

        result = self.executor.execute_skill(self.mock_skill, context, {"input_text": "Test"})

        # Verify that execute_script was called
        self.executor.tool_service.execute_script.assert_called_once()
        # Verify that the result is the mocked return value
        self.assertEqual(result, "Mocked result")

        # Restore the original method
        self.executor.tool_service.execute_script = original_execute_script

    def test_error_handling_when_script_has_invalid_syntax(self):
        """Test that the executor properly handles scripts with invalid syntax"""
        context = SkillContext(
            workspace=MockWorkspace(),
            project=MockProject()
        )

        # Create a script with invalid syntax to trigger ToolService failure
        invalid_script_content = '''
def execute(context, input_text="World"):
    # Invalid syntax to cause an error
    return {
        "success": True,
        "output": f"Hello, {input_text}!,
        "message": f"Greeted {input_text} successfully"
    '''

        invalid_script_path = "/tmp/invalid_test_skill_script.py"
        with open(invalid_script_path, 'w', encoding='utf-8') as f:
            f.write(invalid_script_content)

        original_scripts = self.mock_skill.scripts
        self.mock_skill.scripts = [invalid_script_path]

        try:
            # Execute the skill - should return an error string
            result = self.executor.execute_skill(self.mock_skill, context, {"input_text": "Test"})
            # Result should be a string indicating an error occurred
            self.assertIsInstance(result, str)
            self.assertIn("Error", result)
        finally:
            # Clean up
            if os.path.exists(invalid_script_path):
                os.remove(invalid_script_path)
            # Restore original scripts
            self.mock_skill.scripts = original_scripts


if __name__ == '__main__':
    # Run the tests
    unittest.main()