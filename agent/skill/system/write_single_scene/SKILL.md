---
name: write_single_scene
description: A skill to write and update individual scenes in the screenplay
parameters:
  - name: scene_id
    type: string
    required: true
    description: Unique identifier for the scene (e.g., scene_001)
  - name: title
    type: string
    required: true
    description: Title or heading for the scene
  - name: content
    type: string
    required: true
    description: The screenplay content in Hollywood format (scene headings, action, dialogue)
  - name: scene_number
    type: string
    required: false
    description: Scene number in the screenplay sequence
  - name: location
    type: string
    required: false
    description: Location of the scene (e.g., COFFEE SHOP, CITY STREET)
  - name: time_of_day
    type: string
    required: false
    description: Time of day (DAY, NIGHT, DAWN, DUSK)
  - name: genre
    type: string
    required: false
    description: Genre classification
  - name: logline
    type: string
    required: false
    description: Brief summary of the scene
  - name: characters
    type: array
    required: false
    description: List of character names appearing in the scene
  - name: story_beat
    type: string
    required: false
    description: Story beat or plot point for the scene
  - name: duration_minutes
    type: integer
    required: false
    description: Estimated duration in minutes
  - name: status
    type: string
    required: false
    description: Status of the scene (draft, revised, final)
---

# Single Scene Writing Skill

This skill allows the agent to write and update individual scenes in the project's screenplay. It can create new scenes or modify existing ones with proper formatting and metadata following Hollywood standards.

## Capabilities

- Write new individual scenes with proper screenplay formatting
- Update existing scenes with new content or metadata
- Apply Hollywood-standard screenplay formatting (scene headings, action, character names, dialogue)
- Modify scene metadata (location, time of day, characters, story beat, etc.)
- Preserve existing scene information while updating specific elements
- Follow industry-standard screenplay structure and format

## Usage

The skill can be invoked when users want to create or update specific scenes in the screenplay. It accepts scene details and uses the project's screenplay manager to store the updated scene.

## Example Call

```json
{
  "type": "skill",
  "skill": "write_single_scene",
  "args": {
    "scene_id": "scene_001",
    "title": "Opening Scene - The Jazz Club",
    "content": "# INT. JAZZ CLUB - NIGHT\n\nSmoke curls through the dim light as a SAXOPHONE wails. JACK MONROE, 40s, weathered face, sits at the bar nursing a whiskey.\n\n**JACK**\n*(to the bartender)*\nAnother one. Make it a double.\n\nThe door swings open. LILA CHEN, 30s, elegant in a red dress, scans the room.",
    "scene_number": "1",
    "location": "JAZZ CLUB",
    "time_of_day": "NIGHT",
    "characters": ["JACK MONROE", "LILA CHEN"],
    "story_beat": "character_introduction",
    "duration_minutes": 3
  }
}
```

## Output

Returns a JSON object containing:
- `success`: Boolean indicating if the operation succeeded
- `action`: "created" or "updated"
- `scene_id`: The ID of the scene
- `message`: Human-readable status message