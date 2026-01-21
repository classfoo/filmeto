---
name: create_execution_plan
description: Creates an execution plan for film production projects
parameters:
  - name: plan_name
    type: string
    required: true
    description: Name of the execution plan
  - name: description
    type: string
    required: false
    description: Description of the plan
  - name: tasks
    type: array
    required: false
    description: Array of tasks for the plan
---
# Execution Plan Creation Skill

This skill creates an execution plan for film production projects using the plan service. It allows producers and other crew members to define and track project milestones, tasks, and responsibilities.

## Capabilities

- Create structured execution plans with named tasks and dependencies
- Assign tasks to specific crew members using valid titles
- Define task parameters and dependencies between tasks
- Track project milestones and responsibilities

## Important Notes for Plan Creation

When creating a plan, you must provide tasks in the following JSON format:

Each task must include: id, name, description, title, needs, parameters.

The title MUST be one of the following valid crew member titles:
- producer
- director
- screenwriter
- cinematographer
- editor
- sound_designer
- vfx_supervisor
- storyboard_artist

Using any other title (such as 'system', 'user', 'assistant', etc.) will cause the task to fail.

Tasks can have dependencies defined in the 'needs' field, which should contain an array of other task IDs that must be completed before this task can begin.

## Usage

The skill can be invoked when users want to create a structured execution plan for a film production project. The plan will be created with the specified tasks assigned to appropriate crew members.

## Example Call

```json
{
  "type": "skill",
  "skill": "create_execution_plan",
  "args": {
    "plan_name": "Pre-production Schedule",
    "description": "Detailed schedule for pre-production activities",
    "tasks": [
      {
        "id": "task1",
        "name": "Script Finalization",
        "description": "Complete final revisions to the script",
        "title": "screenwriter",
        "needs": [],
        "parameters": {}
      },
      {
        "id": "task2",
        "name": "Location Scouting",
        "description": "Find and secure filming locations",
        "title": "director",
        "needs": ["task1"],
        "parameters": {}
      },
      {
        "id": "task3",
        "name": "Casting",
        "description": "Hold auditions and select cast members",
        "title": "director",
        "needs": ["task1"],
        "parameters": {}
      }
    ]
  }
}
```

## Output

Returns a JSON object containing:
- `success`: Boolean indicating if the operation succeeded
- `message`: Human-readable status message
- `plan_id`: Unique identifier for the created plan
- `plan_name`: Name of the created plan
- `project_name`: Name of the project the plan belongs to