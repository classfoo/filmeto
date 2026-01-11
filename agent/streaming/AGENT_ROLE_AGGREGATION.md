# Agent消息聚合机制重构说明

## 概述

本次重构实现了主agent（Main Agent）和子agent（Sub-Agent）的消息分类和聚合，使得流式消息能够清晰地区分主agent的内部协调流程和子agent的专业任务执行。

## 核心设计

### 角色分类

#### 1. 主Agent角色（Main Agent Roles）
这些角色负责任务理解、计划制定、任务调度等协调工作，它们的消息会被聚合到统一的"MainAgent"消息流中：

- `MAIN_AGENT` - 虚拟角色，用于聚合显示
- `COORDINATOR` - 协调者，处理简单任务和工具调用
- `PLANNER` - 计划者，制定多agent执行计划
- `QUESTION_UNDERSTANDING` - 问题理解，分析用户意图
- `EXECUTOR` - 执行者，执行工具调用
- `PLAN_REFINEMENT` - 计划优化，根据反馈调整计划
- `RESPONSE` - 响应生成，生成最终回复
- `REVIEWER` - 评审者，评估执行结果
- `SYNTHESIZER` - 综合者，汇总子agent结果

#### 2. 子Agent角色（Sub-Agent Roles）
这些是影视制作团队中的专业角色，每个子agent维护独立的消息流：

- `PRODUCTION` - 制片人
- `DIRECTOR` - 导演
- `SCREENWRITER` - 编剧
- `ACTOR` - 演员
- `MAKEUP_ARTIST` - 化妆师
- `SUPERVISOR` - 场记
- `SOUND_MIXER` - 音响师
- `EDITOR` - 剪辑师

### 消息聚合策略

#### 主Agent消息聚合
所有主agent角色的消息共享同一个`message_id`，在UI中显示为统一的"MainAgent"消息：

```python
# 主agent的不同角色发送消息
emitter.emit_agent_start("Coordinator", AgentRole.COORDINATOR)
emitter.emit_agent_content("Coordinator", "正在分析任务...")

emitter.emit_agent_start("Planner", AgentRole.PLANNER)
emitter.emit_agent_content("Planner", "制定执行计划...")

# 这些消息都会聚合到同一个message_id下，显示为"MainAgent"
# 原始角色信息保存在metadata中
```

#### 子Agent独立消息
每个子agent维护独立的`message_id`，在UI中分别显示：

```python
# 子agent各自维护独立消息
emitter.emit_agent_start("Director", AgentRole.DIRECTOR)
emitter.emit_agent_content("Director", "设计场景构图...")

emitter.emit_agent_start("Screenwriter", AgentRole.SCREENWRITER)
emitter.emit_agent_content("Screenwriter", "撰写剧本...")

# Director和Screenwriter各有独立的message_id
```

## 实现细节

### AgentRole枚举增强

```python
@classmethod
def is_main_agent_role(cls, role: 'AgentRole') -> bool:
    """检查角色是否属于主agent"""
    main_agent_roles = {
        cls.MAIN_AGENT,
        cls.COORDINATOR,
        cls.PLANNER,
        cls.QUESTION_UNDERSTANDING,
        cls.EXECUTOR,
        cls.PLAN_REFINEMENT,
        cls.RESPONSE,
    }
    return role in main_agent_roles

@classmethod
def is_sub_agent_role(cls, role: 'AgentRole') -> bool:
    """检查角色是否属于子agent"""
    sub_agent_roles = {
        cls.PRODUCTION,
        cls.DIRECTOR,
        cls.SCREENWRITER,
        cls.ACTOR,
        cls.MAKEUP_ARTIST,
        cls.SUPERVISOR,
        cls.SOUND_MIXER,
        cls.EDITOR,
    }
    return role in sub_agent_roles
```

### StreamEventEmitter增强

```python
class StreamEventEmitter:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self._callbacks: List[Callable[[StreamEvent], None]] = []
        self._message_ids: Dict[str, str] = {}  # 子agent的message_id映射
        self._main_agent_message_id: Optional[str] = None  # 主agent聚合的message_id
    
    def _get_main_agent_message_id(self) -> str:
        """获取或创建主agent的聚合message_id"""
        if self._main_agent_message_id is None:
            self._main_agent_message_id = str(uuid.uuid4())
        return self._main_agent_message_id
```

### 消息发送逻辑

所有`emit_agent_*`方法都会检查角色类型并应用相应的聚合策略：

```python
def emit_agent_start(self, agent_name: str, agent_role: AgentRole = None):
    if agent_role is None:
        agent_role = AgentRole.from_agent_name(agent_name)
    
    # 主agent角色使用聚合message_id
    if AgentRole.is_main_agent_role(agent_role):
        message_id = self._get_main_agent_message_id()
        display_role = AgentRole.MAIN_AGENT
        display_name = "MainAgent"
    else:
        message_id = self._new_message_id(agent_name)
        display_role = agent_role
        display_name = agent_name
    
    event = StreamEvent(
        event_type=StreamEventType.AGENT_START,
        agent_role=display_role,
        agent_name=display_name,
        message_id=message_id,
        metadata={"original_role": agent_role.value, "original_name": agent_name}
    )
    self.emit(event)
    return event
```

## 使用效果

### 用户视角（UI显示）

```
┌─ User ─────────────────────────────────────┐
│ 创建一个关于太空探险的短片                    │
└────────────────────────────────────────────┘

┌─ MainAgent ────────────────────────────────┐
│ [问题理解] 任务类型: full_production        │
│ [计划制定] 创建执行计划，包含4个任务...       │
│ [计划详情] 阶段: 全流程制作                  │
└────────────────────────────────────────────┘

┌─ Screenwriter ─────────────────────────────┐
│ ✅ 任务1 - script_outline: 完成剧本大纲     │
│ 质量评分: 0.85                              │
└────────────────────────────────────────────┘

┌─ Director ─────────────────────────────────┐
│ ✅ 任务2 - storyboard: 完成分镜设计         │
│ 质量评分: 0.90                              │
└────────────────────────────────────────────┘

┌─ MainAgent ────────────────────────────────┐
│ [结果评审] 所有任务执行成功                  │
│ [结果综合] 制作团队完成所有任务，质量良好     │
└────────────────────────────────────────────┘
```

### 开发者视角（事件流）

```python
# 主agent事件（共享message_id: "msg-abc123"）
StreamEvent(
    event_type=AGENT_START,
    agent_role=MAIN_AGENT,
    agent_name="MainAgent",
    message_id="msg-abc123",
    metadata={"original_role": "question_understanding", "original_name": "QuestionUnderstanding"}
)

StreamEvent(
    event_type=AGENT_CONTENT,
    agent_role=MAIN_AGENT,
    agent_name="MainAgent",
    message_id="msg-abc123",  # 相同的message_id
    metadata={"original_role": "planner", "original_name": "Planner"}
)

# 子agent事件（独立message_id）
StreamEvent(
    event_type=AGENT_START,
    agent_role=DIRECTOR,
    agent_name="Director",
    message_id="msg-def456",  # 独立的message_id
)

StreamEvent(
    event_type=AGENT_START,
    agent_role=SCREENWRITER,
    agent_name="Screenwriter",
    message_id="msg-ghi789",  # 另一个独立的message_id
)
```

## 优势

1. **清晰的职责分离**：主agent负责协调，子agent负责执行，UI显示一目了然
2. **减少信息噪音**：主agent的内部协调过程聚合显示，不会产生过多消息气泡
3. **保留完整信息**：通过metadata保存原始角色信息，便于调试和分析
4. **更好的用户体验**：用户看到的是"主agent在协调"和"各专业团队在工作"的清晰画面

## 兼容性

- 所有原有的API调用都保持兼容
- 通过metadata字段可以获取原始的角色和名称信息
- UI层可以根据需要选择显示聚合后的角色或原始角色

## 测试

运行测试文件验证功能：

```bash
python tests/test_agent_role_aggregation.py
```

测试覆盖：
- ✅ 主agent角色分类
- ✅ 子agent角色分类  
- ✅ 主agent消息聚合
- ✅ 子agent独立消息
- ✅ 混合场景下的消息隔离
- ✅ 角色名称映射

## 后续优化建议

1. 在UI层添加"展开主agent详情"功能，显示内部各个角色的具体工作
2. 为主agent消息添加进度指示器，显示当前处于哪个阶段
3. 添加消息过滤功能，允许用户只查看子agent的工作成果
4. 考虑添加消息压缩功能，将过长的主agent内部日志折叠显示
