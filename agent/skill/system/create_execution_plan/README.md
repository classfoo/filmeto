# Create Execution Plan Skill

This skill enables the creation of execution plans for film production projects using the plan service.

## Overview

The `create_execution_plan` skill allows producers and other crew members to define and track project milestones, tasks, and responsibilities through structured execution plans.

## Parameters

- `plan_name` (string, required): Name of the execution plan
- `description` (string, optional): Description of the plan
- `tasks` (array, optional): Array of tasks for the plan

## Usage

The skill can be called by any crew member that has it in their skill list, but it's primarily intended for the producer role.

Example usage in a crew member's prompt:

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
        "agent_role": "screenwriter"
      },
      {
        "id": "task2", 
        "name": "Location Scouting",
        "description": "Find and secure filming locations",
        "agent_role": "director"
      }
    ]
  }
}
```

## Integration

This skill is automatically assigned to the `producer` crew title in both English and Chinese versions, allowing producers to manage project execution plans effectively.