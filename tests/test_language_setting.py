"""
Test script to verify language setting functionality
"""
import asyncio
import tempfile
import os
from pathlib import Path

from agent.llm.llm_service import LlmService
from app.data.project import Project
from app.data.workspace import Workspace
from utils.i18n_utils import translation_manager


def test_language_prompt_injection():
    """Test that language prompts are properly injected based on language setting"""
    print("Testing language prompt injection...")
    
    # Create an LLM service instance
    llm_service = LlmService()
    
    # Test different languages
    test_cases = [
        ('zh_CN', '请使用中文回答。'),
        ('en_US', 'Please respond in English.'),
        ('ja_JP', '日本語で返答してください。'),
        ('fr_FR', 'Veuillez répondre en français.'),
        ('non_existent', '')  # Test for non-existent language
    ]
    
    for lang_code, expected_prompt in test_cases:
        print(f"\nTesting language: {lang_code}")
        
        # Temporarily set the language in the translation manager
        original_lang = translation_manager.get_current_language()
        translation_manager._current_language = lang_code
        
        # Test message injection
        test_messages = [{"role": "user", "content": "Hello, how are you?"}]
        result_messages = llm_service._inject_language_prompt(test_messages)
        
        print(f"Original messages: {test_messages}")
        print(f"Result messages: {result_messages}")
        
        # Check if the language prompt was injected
        if expected_prompt:
            # Should have a system message with the language prompt
            system_messages = [msg for msg in result_messages if msg['role'] == 'system']
            if system_messages:
                system_content = system_messages[0]['content']
                if expected_prompt in system_content:
                    print(f"✅ Correctly injected language prompt for {lang_code}")
                else:
                    print(f"❌ Language prompt not found in system message for {lang_code}")
                    print(f"   Expected: {expected_prompt}")
                    print(f"   Got: {system_content}")
            else:
                print(f"❌ No system message found for {lang_code}")
        else:
            # For non-existent language, should not inject anything
            if len(result_messages) == 1 and result_messages[0]['role'] == 'user':
                print(f"✅ Correctly handled non-existent language: {lang_code}")
            else:
                print(f"❌ Unexpected behavior for non-existent language: {lang_code}")
        
        # Restore original language
        translation_manager._current_language = original_lang


def test_language_prompt_with_existing_system_message():
    """Test that language prompts are appended to existing system messages"""
    print("\nTesting language prompt injection with existing system message...")
    
    # Create an LLM service instance
    llm_service = LlmService()
    
    # Temporarily set the language in the translation manager
    original_lang = translation_manager.get_current_language()
    translation_manager._current_language = 'en_US'
    
    # Test with existing system message
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
    result_messages = llm_service._inject_language_prompt(test_messages)
    
    print(f"Original messages: {test_messages}")
    print(f"Result messages: {result_messages}")
    
    # Check if the language prompt was appended to the existing system message
    system_message = result_messages[0]
    if system_message['role'] == 'system':
        content = system_message['content']
        if 'Please respond in English.' in content and 'You are a helpful assistant.' in content:
            print("✅ Correctly appended language prompt to existing system message")
        else:
            print("❌ Language prompt not properly appended to existing system message")
            print(f"   Content: {content}")
    else:
        print("❌ System message was not preserved")
    
    # Restore original language
    translation_manager._current_language = original_lang


def test_project_language_setting():
    """Test that language setting is saved to project"""
    print("\nTesting project language setting...")
    
    # Create a temporary project
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create workspace
        workspace = Workspace(workspace_path=temp_dir, project_name="test_workspace")
        
        # Create project directory structure
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        
        # Create basic project structure
        (project_path / "project.yml").write_text("{}")
        (project_path / "timeline").mkdir()
        (project_path / "prompts").mkdir()
        (project_path / "resources").mkdir()
        (project_path / "characters").mkdir()
        (project_path / "agent").mkdir()
        (project_path / "agent" / "conversations").mkdir()
        (project_path / "agent" / "crew_members").mkdir()
        
        # Create project
        project = Project(workspace, str(project_path), "test_project")
        
        # Update project language setting
        project.update_config('language', 'zh_CN')
        
        # Check if the setting was saved
        config = project.get_config()
        saved_language = config.get('language')
        
        if saved_language == 'zh_CN':
            print("✅ Language setting correctly saved to project")
        else:
            print(f"❌ Language setting not saved correctly. Got: {saved_language}")
        
        # Test updating to another language
        project.update_config('language', 'en_US')
        config = project.get_config()
        saved_language = config.get('language')
        
        if saved_language == 'en_US':
            print("✅ Language setting correctly updated in project")
        else:
            print(f"❌ Language setting not updated correctly. Got: {saved_language}")


if __name__ == "__main__":
    print("Running language setting functionality tests...\n")
    
    test_language_prompt_injection()
    test_language_prompt_with_existing_system_message()
    test_project_language_setting()
    
    print("\nLanguage setting tests completed.")