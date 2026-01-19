---
name: write_screenplay_outline
description: A skill to generate screenplay outlines and create scenes in the project
parameters:
  - name: concept
    type: string
    required: true
    description: The basic concept or idea for the screenplay
  - name: genre
    type: string
    required: false
    default: General
    description: The genre of the screenplay (e.g., Drama, Comedy, Action, Horror)
  - name: num_scenes
    type: integer
    required: false
    default: 10
    description: Number of scenes to generate in the outline
---

# Screenplay Outline Writing Skill

This skill allows the agent to generate comprehensive screenplay outlines and create individual scenes in the project's screenplay manager. It can break down a story concept into structured scenes with proper metadata following Hollywood standards.

## Capabilities

- Generate a complete screenplay outline from a concept or idea
- Create individual scenes with proper metadata (location, time of day, characters, etc.)
- Structure scenes following Hollywood screenplay format
- Organize scenes chronologically with proper scene numbers
- Assign characters to appropriate scenes
- Set scene-specific metadata like duration and story beats

## Usage

The skill can be invoked when users want to develop a screenplay from scratch or expand an existing concept. It will generate a structured outline and create the corresponding scenes in the project's screenplay manager.

## Example Call

```json
{
  "type": "skill",
  "skill": "write_screenplay_outline",
  "args": {
    "concept": "A detective in 1920s Chicago investigates a series of mysterious disappearances in the jazz district",
    "genre": "Film Noir",
    "num_scenes": 12
  }
}
```

## Output

Returns a JSON object containing:
- `success`: Boolean indicating if the operation succeeded
- `total_scenes`: Number of scenes generated
- `created_scenes`: List of scene IDs that were created
- `message`: Human-readable status message