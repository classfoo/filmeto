# Prompt Package

The prompt package provides a centralized system for managing prompt templates with internationalization support.

## Overview

The prompt service allows for:
- Storing prompt templates as markdown files with YAML frontmatter metadata
- Internationalization support with language-specific templates
- Parameterized template rendering
- Caching for improved performance

## Directory Structure

```
agent/
└── prompt/
    ├── __init__.py
    ├── prompt_service.py
    └── system/
        ├── en_US/
        │   ├── react_base.md
        │   └── skill_react.md
        └── zh_CN/
            ├── react_base.md
            └── skill_react.md
```

## Usage

### Basic Usage

```python
from agent.prompt.prompt_service import prompt_service

# Get a prompt template
template = prompt_service.get_prompt_template("react_base", "en_US")

# Render a prompt with parameters
rendered_prompt = prompt_service.render_prompt(
    "react_base",
    title="crew member",
    agent_name="my_agent",
    role_description="Role description",
    soul_profile="Soul profile",
    skills_list=[...],
    context_info="Context information"
)

# Get metadata for a prompt
metadata = prompt_service.get_prompt_metadata("react_base", "en_US")
```

### Template Format

Prompt templates are stored as markdown files with YAML frontmatter:

```markdown
---
name: template_name
description: Description of the template
version: 1.0
---
Template content with ${parameter_placeholders}
```

## Features

- **Internationalization**: Templates are organized by language code (en_US, zh_CN, etc.)
- **Metadata Support**: YAML frontmatter allows defining metadata for each template
- **Parameter Substitution**: Templates support parameter substitution using `${parameter_name}` syntax
- **Fallback Mechanism**: Falls back to en_US templates if language-specific template doesn't exist
- **Caching**: Templates are cached to improve performance
- **Safe Substitution**: Uses Python's Template.safe_substitute to prevent errors with missing parameters
```