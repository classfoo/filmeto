"""Script to extract skills from sub_agents into separate files."""

import os
import re
from pathlib import Path


def extract_skills_from_file(agent_file_path):
    """Extract all skill classes from an agent file."""
    with open(agent_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find agent name
    agent_match = re.search(r'class (\w+Agent)\(', content)
    if not agent_match:
        return None, []
    
    agent_name = agent_match.group(1).replace('Agent', '').lower()
    
    # Find all skill classes
    skill_pattern = r'(class (\w+Skill)\(BaseSkill\):.*?)(?=\n\nclass |\Z)'
    skills = re.findall(skill_pattern, content, re.DOTALL)
    
    skill_data = []
    for skill_code, skill_name in skills:
        # Convert class name to filename (e.g., StoryboardSkill -> storyboard.py)
        filename = re.sub(r'(?<!^)(?=[A-Z])', '_', skill_name.replace('Skill', '')).lower() + '.py'
        skill_data.append((skill_name, filename, skill_code.strip()))
    
    return agent_name, skill_data


def create_skill_file(agent_name, skill_name, filename, skill_code, base_path):
    """Create a separate skill file."""
    skill_dir = base_path / agent_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    skill_file = skill_dir / filename
    
    # Create file content with proper imports
    file_content = f'"""{ skill_name.replace("Skill", " Skill") }."""\n\n'
    file_content += 'from agent.skills.base import BaseSkill, SkillContext, SkillResult, SkillStatus\n\n\n'
    file_content += skill_code + '\n'
    
    with open(skill_file, 'w', encoding='utf-8') as f:
        f.write(file_content)
    
    print(f"Created: {skill_file}")
    return skill_name, filename


def create_init_file(agent_name, skills_info, base_path):
    """Create __init__.py for agent skills."""
    skill_dir = base_path / agent_name
    init_file = skill_dir / '__init__.py'
    
    content = f'"""{agent_name.title()} Agent Skills."""\n\n'
    
    # Add imports
    for skill_name, filename in skills_info:
        module_name = filename.replace('.py', '')
        content += f'from agent.skills.{agent_name}.{module_name} import {skill_name}\n'
    
    # Add __all__
    content += '\n__all__ = [\n'
    for skill_name, _ in skills_info:
        content += f'    "{skill_name}",\n'
    content += ']\n'
    
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Created: {init_file}")


def update_agent_file(agent_file_path, agent_name, skills_info):
    """Update agent file to import from skills module."""
    with open(agent_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove old imports
    content = re.sub(
        r'from typing import.*?\n',
        lambda m: m.group(0).replace(', Dict, List, Optional', ''),
        content
    )
    
    # Remove BaseSkill imports
    content = re.sub(
        r'from agent\.skills\.base import BaseSkill, SkillContext, SkillResult, SkillStatus\n',
        '',
        content
    )
    
    # Add new imports after the base import
    import_line = f'from agent.sub_agents.base import FilmProductionAgent'
    skill_imports = 'from agent.skills.{} import (\n'.format(agent_name)
    for skill_name, _ in skills_info:
        skill_imports += f'    {skill_name},\n'
    skill_imports += ')'
    
    content = content.replace(
        import_line,
        import_line + '\n' + skill_imports
    )
    
    # Remove all skill class definitions
    for skill_name, _ in skills_info:
        pattern = rf'\n\nclass {skill_name}\(BaseSkill\):.*?(?=\n\nclass |\Z)'
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    with open(agent_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated: {agent_file_path}")


def main():
    """Main function to process all agent files."""
    base_path = Path('/Users/classfoo/ai/filmeto/agent')
    sub_agents_path = base_path / 'sub_agents'
    skills_base_path = base_path / 'skills'
    
    # Skip these files
    skip_files = ['__init__.py', 'base.py', 'registry.py']
    
    # Process each agent file
    for agent_file in sub_agents_path.glob('*.py'):
        if agent_file.name in skip_files:
            continue
        
        print(f"\nProcessing {agent_file.name}...")
        agent_name, skill_data = extract_skills_from_file(agent_file)
        
        if not agent_name or not skill_data:
            print(f"  Skipping {agent_file.name} - no skills found")
            continue
        
        # Create skill files
        skills_info = []
        for skill_name, filename, skill_code in skill_data:
            create_skill_file(agent_name, skill_name, filename, skill_code, skills_base_path)
            skills_info.append((skill_name, filename))
        
        # Create __init__.py
        create_init_file(agent_name, skills_info, skills_base_path)
        
        # Update agent file
        update_agent_file(agent_file, agent_name, skills_info)
    
    print("\n✅ All skills extracted successfully!")


if __name__ == '__main__':
    main()
