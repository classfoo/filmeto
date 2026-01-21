"""
Prompt Service Module

Implements the PromptService class to manage prompt templates with internationalization support.
Prompts are stored as markdown files with YAML frontmatter metadata and can be loaded by name
and rendered with parameters.
"""
import os
import re
from typing import Dict, Optional, Any
from pathlib import Path
from string import Template

from utils.md_with_meta_utils import read_md_with_meta, get_metadata
from utils.i18n_utils import translation_manager


class PromptService:
    """
    Service class that manages prompt templates with internationalization support.

    Prompts are stored as markdown files in agent/prompt/system/{language}/ directory
    and can be loaded by name and rendered with parameters.
    """
    
    def __init__(self):
        """
        Initialize the PromptService.
        """
        self.system_prompts_path = os.path.join(os.path.dirname(__file__), "system")
        self._template_cache: Dict[str, str] = {}

    def get_prompt_template(self, name: str, language: Optional[str] = None) -> Optional[str]:
        """
        Get a prompt template by name and language.

        Args:
            name: Name of the prompt template (without .md extension)
            language: Language code (e.g., 'en_US', 'zh_CN'). If None, uses current language.

        Returns:
            Prompt template content if found, None otherwise
        """
        if language is None:
            language = translation_manager.get_current_language()

        # Construct path to the prompt file
        prompt_path = os.path.join(self.system_prompts_path, language, f"{name}.md")

        # If the language-specific file doesn't exist, fall back to en_US
        if not os.path.exists(prompt_path):
            fallback_path = os.path.join(self.system_prompts_path, "en_US", f"{name}.md")
            if os.path.exists(fallback_path):
                prompt_path = fallback_path
            else:
                return None

        # Check cache first
        cache_key = f"{name}_{language}"
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        try:
            # Use md_with_meta_utils to read the prompt file
            # We only need the content part, not the metadata
            _, content = read_md_with_meta(prompt_path)
            
            # Cache the template
            self._template_cache[cache_key] = content
            return content
        except Exception as e:
            print(f"Error loading prompt template {name}: {e}")
            return None

    def get_prompt_metadata(self, name: str, language: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a prompt template by name and language.

        Args:
            name: Name of the prompt template (without .md extension)
            language: Language code (e.g., 'en_US', 'zh_CN'). If None, uses current language.

        Returns:
            Metadata dictionary if found, None otherwise
        """
        if language is None:
            language = translation_manager.get_current_language()

        # Construct path to the prompt file
        prompt_path = os.path.join(self.system_prompts_path, language, f"{name}.md")

        # If the language-specific file doesn't exist, fall back to en_US
        if not os.path.exists(prompt_path):
            fallback_path = os.path.join(self.system_prompts_path, "en_US", f"{name}.md")
            if os.path.exists(fallback_path):
                prompt_path = fallback_path
            else:
                return None

        try:
            # Use md_with_meta_utils to get only the metadata
            return get_metadata(prompt_path)
        except Exception as e:
            print(f"Error loading prompt metadata {name}: {e}")
            return None

    def render_prompt(self, name: str, language: Optional[str] = None, **kwargs) -> Optional[str]:
        """
        Render a prompt template with the given parameters.

        Args:
            name: Name of the prompt template (without .md extension)
            language: Language code (e.g., 'en_US', 'zh_CN'). If None, uses current language.
            **kwargs: Parameters to substitute in the template

        Returns:
            Rendered prompt if successful, None otherwise
        """
        template_content = self.get_prompt_template(name, language)
        if template_content is None:
            return None

        try:
            # Use Python's Template for safe parameter substitution
            template = Template(template_content)
            rendered_prompt = template.substitute(**kwargs)
            return rendered_prompt
        except KeyError as e:
            print(f"Missing required parameter for prompt {name}: {e}")
            # Return the template with placeholders intact if some parameters are missing
            try:
                template = Template(template_content)
                rendered_prompt = template.safe_substitute(**kwargs)
                return rendered_prompt
            except Exception:
                return template_content
        except Exception as e:
            print(f"Error rendering prompt {name}: {e}")
            return template_content

    def clear_cache(self):
        """
        Clear the template cache.
        """
        self._template_cache.clear()

    def list_available_prompts(self, language: Optional[str] = None) -> list:
        """
        List all available prompt templates for a given language.

        Args:
            language: Language code (e.g., 'en_US', 'zh_CN'). If None, uses current language.

        Returns:
            List of available prompt names
        """
        if language is None:
            language = translation_manager.get_current_language()

        prompt_dir = os.path.join(self.system_prompts_path, language)
        if not os.path.exists(prompt_dir):
            return []

        prompts = []
        for file_path in Path(prompt_dir).glob("*.md"):
            prompts.append(file_path.stem)  # Get filename without extension

        return prompts


# Global instance of the prompt service
prompt_service = PromptService()