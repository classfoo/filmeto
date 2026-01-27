"""
Unit test for ToolService execute_script functionality with get_project_crew_members tool
"""
import unittest
import sys
import os
import tempfile

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.tool.tool_service import ToolService
from agent.tool.tool_context import ToolContext
from agent.tool.system import GetProjectCrewMembersTool


class MockProject:
    """Mock project object for testing"""
    def __init__(self):
        self.project_name = "TestProject"
        self.project_path = "/tmp/test_project"


class MockWorkspace:
    """Mock workspace object for testing"""
    def __init__(self):
        self.workspace_path = "/tmp/test_workspace"
        self.project_name = "TestProject"
        self._project = MockProject()

    def get_project(self):
        """Get the mock project"""
        return self._project


class TestToolServiceExecuteScript(unittest.TestCase):
    """Test cases for ToolService execute_script with get_project_crew_members tool"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.tool_service = ToolService()

        # Register the GetProjectCrewMembersTool
        self.get_crew_members_tool = GetProjectCrewMembersTool()
        self.tool_service.register_tool(self.get_crew_members_tool)

        # Set up context with mock project and workspace
        mock_workspace = MockWorkspace()
        self.context = ToolContext(workspace=mock_workspace, project_name="TestProject")

    def test_execute_script_with_get_project_crew_members(self):
        """Test that execute_script can call get_project_crew_members tool and return correct results"""
        # Script that calls the get_project_crew_members tool
        script_content = '''
# Call the get_project_crew_members tool
result = execute_tool("get_project_crew_members", {})
import json
print(json.dumps(result))
'''

        # Create a temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = f.name

        try:
            # Execute the script with context
            output = self.tool_service.execute_script(script_path, context=self.context)
            # Extract the last line which should be the JSON result
            if output:
                lines = output.strip().split('\n')
                # Find the last line that looks like JSON
                json_line = None
                for line in reversed(lines):
                    line = line.strip()
                    if line.startswith('[') or line.startswith('{'):
                        json_line = line
                        break
                if json_line:
                    import json
                    result = json.loads(json_line)
                else:
                    result = []
            else:
                result = []
        finally:
            # Clean up the temporary file
            os.remove(script_path)

        # Verify the result
        self.assertIsNotNone(result, "Result should not be None")
        self.assertIsInstance(result, list, "Result should be a list of crew members")

        # Verify that we got some crew members
        self.assertGreater(len(result), 0, "Should have at least one crew member")

        # Verify the structure of each crew member
        for member in result:
            self.assertIn('name', member, "Each crew member should have a 'name' field")
            self.assertIn('role', member, "Each crew member should have a 'role' field")
            self.assertIn('description', member, "Each crew member should have a 'description' field")
            self.assertIn('skills', member, "Each crew member should have a 'skills' field")
            self.assertIn('model', member, "Each crew member should have a 'model' field")
            self.assertIn('temperature', member, "Each crew member should have a 'temperature' field")
            self.assertIn('max_steps', member, "Each crew member should have a 'max_steps' field")
            self.assertIn('color', member, "Each crew member should have a 'color' field")
            self.assertIn('icon', member, "Each crew member should have an 'icon' field")

            # Verify that the name is a non-empty string
            self.assertIsInstance(member['name'], str, "Name should be a string")
            self.assertGreater(len(member['name']), 0, "Name should not be empty")

    def test_execute_script_with_parameters(self):
        """Test that execute_script works even when passing parameters to the tool"""
        script_content = '''
# Call the get_project_crew_members tool with empty parameters
result = execute_tool("get_project_crew_members", {})
import json
print(json.dumps(result))
'''

        # Create a temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = f.name

        try:
            output = self.tool_service.execute_script(script_path, context=self.context)
            # Extract the last line which should be the JSON result
            if output:
                lines = output.strip().split('\n')
                # Find the last line that looks like JSON
                json_line = None
                for line in reversed(lines):
                    line = line.strip()
                    if line.startswith('[') or line.startswith('{'):
                        json_line = line
                        break
                if json_line:
                    import json
                    result = json.loads(json_line)
                else:
                    result = []
            else:
                result = []
        finally:
            # Clean up the temporary file
            os.remove(script_path)

        # Verify the result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_execute_tool_directly(self):
        """Test that the tool can be called directly as well"""
        result = self.tool_service.execute_tool("get_project_crew_members", {}, context=self.context)

        # Verify the result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # Verify structure
        for member in result:
            self.assertIn('name', member)
            self.assertIn('role', member)
            self.assertIn('description', member)

    def test_script_syntax_error_handling(self):
        """Test that syntax errors in scripts are properly handled"""
        invalid_script_content = '''
result = execute_tool("get_project_crew_members", {}
'''  # Missing closing parenthesis

        # Create a temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(invalid_script_content)
            script_path = f.name

        try:
            with self.assertRaises(ValueError) as context:
                self.tool_service.execute_script(script_path, context=self.context)

            self.assertIn("Syntax error in script", str(context.exception))
        finally:
            # Clean up the temporary file
            os.remove(script_path)

    def test_nonexistent_tool_error_handling(self):
        """Test that calling a nonexistent tool raises an error"""
        script_content = '''
result = execute_tool("nonexistent_tool", {})
'''

        # Create a temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = f.name

        try:
            with self.assertRaises(RuntimeError) as context:
                self.tool_service.execute_script(script_path, context=self.context)

            self.assertIn("Tool 'nonexistent_tool' not found", str(context.exception))
        finally:
            # Clean up the temporary file
            os.remove(script_path)


if __name__ == '__main__':
    # Run the tests
    unittest.main()
