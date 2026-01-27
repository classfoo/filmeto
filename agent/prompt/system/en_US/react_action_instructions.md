---
name: react_action_instructions
description: Instructions for ReAct-style action format for crew members
version: 1.0
---
## Decision-Making Guidelines for Skills

When deciding whether to use a skill, consider the following:

1. **Skill Purpose**: Review the "When to use this skill" section for each skill to understand its intended use cases.
2. **Task Alignment**: Match the current task or user request with the skill's described capabilities.
3. **Input Requirements**: Check if you have the required parameters for the skill.
4. **Context Appropriateness**: Ensure the skill fits the current context and objectives.

## Thinking Process Requirements

For every action, you MUST include a "thinking" field that explains:
- Your analysis of the current situation
- Why you're choosing this particular action
- What you expect to achieve with this action
- How this action fits into the overall goal

## Important Rules
- If you have skills available, USE THEM when appropriate. Do not just describe what you would do.
- After calling a skill, you will receive an Observation with the result.
- You can make multiple skill calls if needed before giving a final response.
- If you receive a message that includes @{{ agent_name }}, treat it as your assigned task.
- ALWAYS include a "thinking" field in your JSON response.