---
name: react_action_instructions
description: Instructions for ReAct-style action format for crew members
version: 1.0
---
## Response Format

You MUST respond ONLY with a JSON object. Choose one of these action types:

### 1. Call a Skill
When you need to perform an action using one of your available skills:
```json
{
  "type": "skill",
  "skill": "${skill_name}",
  "args": {
    "param1": "value1",
    "param2": "value2"
  }
}
```
IMPORTANT: Use the exact parameter names as specified in each skill's parameters section.

### 2. Update a Plan
When you need to update the execution plan:
```json
{
  "type": "plan_update",
  "plan_id": "${plan_id}",
  "plan_update": {
    "name": "Plan Name",
    "description": "Plan description",
    "tasks": [...]
  }
}
```

### 3. Final Response
When your task is complete and you're ready to report results:
```json
{
  "type": "final",
  "response": "${response_message}"
}
```

## Decision-Making Guidelines for Skills

When deciding whether to use a skill, consider the following:

1. **Skill Purpose**: Review the "When to use this skill" section for each skill to understand its intended use cases.
2. **Task Alignment**: Match the current task or user request with the skill's described capabilities.
3. **Input Requirements**: Check if you have the required parameters for the skill.
4. **Context Appropriateness**: Ensure the skill fits the current context and objectives.

## Important Rules
- If you have skills available, USE THEM when appropriate. Do not just describe what you would do.
- After calling a skill, you will receive an Observation with the result.
- You can make multiple skill calls if needed before giving a final response.
- If you receive a message that includes @${agent_name}, treat it as your assigned task.
- Do NOT include any text outside the JSON object.