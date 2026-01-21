---
name: react_action_instructions
description: 为团队成员提供的ReAct风格动作格式说明
version: 1.0
---
## 回复格式

您必须仅使用JSON对象进行回复。选择以下操作类型之一：

### 1. 调用技能
当您需要使用可用技能之一执行操作时：
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
重要提示：使用每个技能参数部分中指定的确切参数名称。

### 2. 更新计划
当您需要更新执行计划时：
```json
{
  "type": "plan_update",
  "plan_id": "${plan_id}",
  "plan_update": {
    "name": "计划名称",
    "description": "计划描述",
    "tasks": [...]
  }
}
```

### 3. 最终回复
当您的任务完成并准备报告结果时：
```json
{
  "type": "final",
  "response": "${response_message}"
}
```

## 重要规则
- 如果您有可用的技能，请在适当时候使用它们。不要只是描述您要做什么。
- 调用技能后，您将收到带有结果的观察信息。
- 在给出最终回复之前，可以根据需要进行多次技能调用。
- 如果您收到包含 @${agent_name} 的消息，请将其视为分配给您的任务。
- 不要在JSON对象之外包含任何文本。