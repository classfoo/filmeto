"""
Debug script to test the generated execution script
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.skill.skill_executor import SkillExecutor, SkillContext
from agent.skill.skill_service import Skill, SkillParameter


class MockProject:
    """Mock project object for testing"""
    def __init__(self):
        self.project_name = "TestProject"
        self.project_path = "/tmp/test_project"


class MockWorkspace:
    """Mock workspace object for testing"""
    def __init__(self):
        self.workspace_path = "/tmp/test_workspace"


def debug_script_generation():
    """Debug the script generation process"""
    executor = SkillExecutor()
    
    # Create a mock skill with a simple script
    mock_skill = Skill(
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
    test_script_content = '''def execute(context, input_text="World"):
    """Simple test function that returns a greeting."""
    return {
        "success": True,
        "output": f"Hello, {input_text}!",
        "message": f"Greeted {input_text} successfully"
    }
'''
    
    # Write the test script to a temporary file
    test_script_path = "/tmp/debug_test_skill_script.py"
    with open(test_script_path, 'w', encoding='utf-8') as f:
        f.write(test_script_content)
    
    # Add the script path to the mock skill
    mock_skill.scripts = [test_script_path]
    
    # Create a context for the skill
    context = SkillContext(
        workspace=MockWorkspace(),
        project=MockProject()
    )
    
    # Manually generate the execution script to debug
    with open(test_script_path, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    print("Original script content:")
    print(repr(script_content))
    print("\nOriginal script content (readable):")
    print(script_content)
    
    # Generate execution script manually (matching the new implementation)
    workspace_repr = f'"{getattr(context.workspace, "workspace_path", "")}"' if context.workspace else 'None'
    project_repr = f'"{getattr(context.project, "project_path", "")}"' if context.project else 'None'

    execution_script = f'''
# Prepare the skill execution context
# Note: We'll pass basic context values, but complex objects need special handling
context_dict = {{
    "workspace_path": {workspace_repr},
    "project_path": {project_repr},
    "screenplay_manager": {repr(getattr(context, 'screenplay_manager', None))},
    "llm_service": {repr(getattr(context, 'llm_service', None))},
    "additional_context": {repr(getattr(context, 'additional_context', {}))}
}}

# Prepare arguments
skill_args = {repr({"input_text": "ToolService"})}

# Execute the skill script with the context
script_content = {repr(script_content)}
exec(script_content)

# Call the main function of the skill with context and args
# This assumes the skill script has an 'execute' function
if 'execute' in locals():
    result = execute(context_dict, **skill_args)
elif 'execute_in_context' in locals():
    result = execute_in_context(context_dict, **skill_args)
else:
    # Try to find a function matching the skill name
    skill_fn_name = "test_skill"
    if skill_fn_name in locals():
        result = locals()[skill_fn_name](**skill_args)
    else:
        # If no standard function found, return an error
        result = {{
            "success": False,
            "error": "no_entry_point",
            "message": f"No execute function found in skill 'test-skill'. "
                      f"Expected 'execute(context, **kwargs)' or 'test_skill(...)' function."
        }}
'''
    
    print("\nGenerated execution script:")
    print(repr(execution_script))
    print("\nGenerated execution script (readable):")
    print(execution_script)
    
    # Try to parse the execution script to check for syntax errors
    try:
        import ast
        ast.parse(execution_script)
        print("\n✓ Generated script has valid syntax")
    except SyntaxError as e:
        print(f"\n✗ Generated script has syntax error: {e}")
    
    # Clean up
    if os.path.exists(test_script_path):
        os.remove(test_script_path)


if __name__ == "__main__":
    debug_script_generation()