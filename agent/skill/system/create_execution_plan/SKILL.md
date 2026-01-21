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
This skill creates an execution plan for film production projects using the plan service. It allows producers and other crew members to define and track project milestones, tasks, and responsibilities.