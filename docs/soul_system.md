# Soul System

The Soul system is a feature that allows the Filmeto application to represent different AI personalities or expert profiles, each with their own expertise areas and skills.

## Components

### Soul Class
- Represents an individual "soul" with a name, skills list, and detailed description
- Loads metadata and knowledge from MD files with YAML frontmatter
- Provides properties to access metadata and knowledge sections separately

### SoulService
- Manages collections of Soul instances
- Provides CRUD operations for managing souls
- Automatically loads system souls and user-defined souls
- Offers search capabilities by skill

## Structure of Soul Definition Files

Soul definition files are MD files with YAML frontmatter:

```markdown
---
name: "Example Soul"
title: "Example Title"
specialties: ["Specialty1", "Specialty2"]
skills: ["Skill1", "Skill2", "Skill3"]
experience: "Description of experience"
---
# Example Soul - Description Title

## Biography
Biographical information about the soul...

## Expertise Areas
Detailed information about expertise areas...

## Notable Works
Information about notable works or achievements...

## Philosophy
Personal philosophy or approach...
```

## Usage

```python
from agent.soul import SoulService

# Initialize the service
service = SoulService()

# Get all souls
all_souls = service.get_all_souls()

# Get a specific soul by name
soul = service.get_soul_by_name("soul_name")

# Search for souls by skill
skilled_souls = service.search_souls_by_skill("Directing")

# Add a new soul
new_soul = Soul(name="New Soul", skills=["Skill1", "Skill2"], description_file="path/to/file.md")
service.add_soul(new_soul)
```

## System Souls vs User Souls

- **System Souls**: Predefined expert profiles stored in `agent/soul/system/`
- **User Souls**: Custom profiles created by users stored in `workspace/agent/skills/`

Both types are automatically loaded when the SoulService is initialized.