"""
Unit test for ToolContext
"""
import unittest
import sys
import os
import tempfile

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.tool.tool_context import ToolContext
from agent.tool.tool_service import ToolService
from agent.tool.base_tool import BaseTool, ToolMetadata, ToolParameter


class MockWorkspace:
    """Mock Workspace object for testing"""
    def __init__(self, workspace_path="/tmp/test_workspace", project_name="TestProject"):
        self.workspace_path = workspace_path
        self.project_name = project_name

    def get_project(self):
        """Mock get_project method"""
        return MockProject(self.project_name)


class MockProject:
    """Mock project object for testing"""
    def __init__(self, name="TestProject"):
        self.name = name


class DummyTool(BaseTool):
    """Dummy tool for testing"""
    def __init__(self):
        super().__init__(
            name="dummy_tool",
            description="Dummy tool for testing"
        )

    def metadata(self, lang: str = "en_US") -> ToolMetadata:
        return ToolMetadata(
            name=self.name,
            description="Dummy tool for testing",
            parameters=[],
            return_description="Returns a test message"
        )

    def execute(self, parameters, context=None):
        workspace = context.workspace if context else None
        project_name = context.project_name if context else None
        return f"Workspace: {workspace.workspace_path if workspace else None}, Project: {project_name}"


class TestToolContext(unittest.TestCase):
    """Test cases for ToolContext"""

    def test_tool_context_initialization(self):
        """Test ToolContext initialization"""
        workspace = MockWorkspace()
        context = ToolContext(
            workspace=workspace,
            project_name="TestProject"
        )

        self.assertEqual(context.workspace, workspace)
        self.assertEqual(context.project_name, "TestProject")
        self.assertEqual(context.workspace.workspace_path, "/tmp/test_workspace")

    def test_tool_context_setters(self):
        """Test ToolContext property setters"""
        context = ToolContext()
        new_workspace = MockWorkspace("/new/workspace", "NewProject")
        context.workspace = new_workspace
        context.project_name = "NewProject"

        self.assertEqual(context.workspace, new_workspace)
        self.assertEqual(context.workspace.workspace_path, "/new/workspace")
        self.assertEqual(context.project_name, "NewProject")

    def test_tool_context_get_set(self):
        """Test ToolContext get/set methods"""
        context = ToolContext()

        # Test get with default value
        self.assertIsNone(context.get("nonexistent_key"))
        self.assertEqual(context.get("nonexistent_key", "default"), "default")

        # Test set and get
        context.set("custom_key", "custom_value")
        self.assertEqual(context.get("custom_key"), "custom_value")

    def test_tool_context_update(self):
        """Test ToolContext update method"""
        context = ToolContext()
        context.update({
            "key1": "value1",
            "key2": "value2"
        })

        self.assertEqual(context.get("key1"), "value1")
        self.assertEqual(context.get("key2"), "value2")

    def test_tool_context_to_dict(self):
        """Test ToolContext to_dict method"""
        workspace = MockWorkspace("/tmp/workspace", "MyProject")
        context = ToolContext(
            workspace=workspace,
            project_name="MyProject"
        )
        context.set("custom_key", "custom_value")

        result = context.to_dict()
        self.assertEqual(result["workspace"], workspace)
        self.assertEqual(result["project_name"], "MyProject")
        self.assertEqual(result["custom_key"], "custom_value")

    def test_tool_context_from_dict(self):
        """Test ToolContext from_dict class method"""
        workspace = MockWorkspace("/tmp/workspace", "MyProject")
        data = {
            "workspace": workspace,
            "project_name": "MyProject",
            "custom_key": "custom_value"
        }

        context = ToolContext.from_dict(data)
        self.assertEqual(context.workspace, workspace)
        self.assertEqual(context.project_name, "MyProject")
        self.assertEqual(context.get("custom_key"), "custom_value")

    def test_tool_service_empty_constructor(self):
        """Test ToolService empty constructor"""
        service = ToolService()
        self.assertIsNotNone(service)
        self.assertIsInstance(service.tools, dict)

    def test_tool_service_execute_with_context(self):
        """Test ToolService execute_tool with context parameter"""
        service = ToolService()
        service.register_tool(DummyTool())

        workspace = MockWorkspace()
        context = ToolContext(workspace=workspace, project_name="TestProject")

        result = service.execute_tool("dummy_tool", {}, context)

        self.assertIn("Workspace:", result)
        self.assertIn("/tmp/test_workspace", result)
        self.assertIn("Project: TestProject", result)

    def test_tool_service_execute_without_context(self):
        """Test ToolService execute_tool without context"""
        service = ToolService()
        service.register_tool(DummyTool())

        result = service.execute_tool("dummy_tool", {}, None)

        self.assertIn("Workspace: None", result)
        self.assertIn("Project: None", result)


if __name__ == '__main__':
    unittest.main()
