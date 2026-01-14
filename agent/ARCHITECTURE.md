# FilmetoAgent 架构优化说明

## 概述

本次架构优化实现了以下核心目标：
1. **项目级别隔离**：对话链路、状态和上下文完全绑定到项目，不同项目间完全隔离
2. **Subgraph架构**：每个Agent（主Agent和子Agent）都是独立的LangGraph实例
3. **Production Agent作为主入口**：统一的主Agent管理所有工作流节点
4. **独立状态管理**：主Agent和子Agent各有独立状态，通过明确接口通信

## 架构图

```
FilmetoAgent (项目级实例)
  ├── project_id: "project_name"           # 项目唯一标识
  ├── conversation_manager                  # 项目级对话管理器
  └── production_agent: ProductionAgent     # 主入口 (LangGraph实例)
        ├── question_understanding (node)   # 问题理解
        ├── coordinator (node)              # 简单任务协调
        ├── planner (node)                  # 复杂任务规划
        ├── sub_agent_executor (node)       # 子Agent执行器
        │     ├── DirectorAgent (Subgraph)    # 导演Agent - 独立图
        │     ├── ScreenwriterAgent (Subgraph)# 编剧Agent - 独立图
        │     ├── ActorAgent (Subgraph)       # 演员Agent - 独立图
        │     ├── EditorAgent (Subgraph)      # 剪辑Agent - 独立图
        │     └── ... (其他子Agent Subgraphs)
        ├── review_plan (node)              # 计划审查
        ├── refine_plan (node)              # 计划优化
        ├── synthesize_results (node)       # 结果综合
        └── respond (node)                  # 生成响应
```

## 核心组件

### 1. FilmetoAgent（项目级封装）

**位置**: `agent/filmeto_agent.py`

**职责**:
- 项目级别的Agent封装
- 管理项目特定的对话历史
- 提供流式对话接口
- 协调Production Agent执行

**关键特性**:
```python
class FilmetoAgent:
    project_id: str                          # 项目标识
    project: Project                         # 项目实例
    conversation_manager: ConversationManager # 项目级对话管理
    production_agent: ProductionAgent         # 主Agent实例
```

### 2. ProductionAgent（主Agent）

**位置**: `agent/production_agent.py`

**职责**:
- 作为主入口的完整LangGraph实例
- 协调所有工作流节点
- 管理子Agent的调用
- 处理计划、执行、审查、优化的完整流程

**关键特性**:
```python
class ProductionAgent:
    project_id: str                    # 项目上下文
    graph: CompiledGraph               # 主工作流图
    sub_agent_registry: SubAgentRegistry  # 子Agent注册表
    
    async def execute(messages) -> Dict  # 执行工作流
    async def stream(messages)           # 流式执行
```

### 3. BaseSubAgent（子Agent基类）

**位置**: `agent/sub_agents/base.py`

**职责**:
- 所有子Agent的基类
- 每个子Agent都是独立的LangGraph Subgraph
- 提供标准的执行和评估流程
- 支持技能（Skill）的组织和执行

**关键特性**:
```python
class BaseSubAgent:
    name: str                       # Agent名称
    graph: CompiledGraph           # 独立的Subgraph
    skills: Dict[str, BaseSkill]   # 技能集合
    
    async def execute_task(task, context) -> SkillResult
    def _build_subgraph() -> StateGraph  # 构建独立图
```

**Subgraph结构**:
```
每个子Agent的Subgraph:
  ├── execute_skill (node)     # 执行技能
  └── evaluate_result (node)   # 评估结果
```

### 4. 状态管理

**位置**: `agent/graph/state.py`

#### AgentState (基础状态)
```python
class AgentState(dict):
    messages: List[BaseMessage]      # 消息历史
    next_action: str                 # 下一步动作
    context: Dict[str, Any]          # 上下文信息
    iteration_count: int             # 迭代计数
```

#### ProductionAgentState (主Agent状态)
```python
class ProductionAgentState(AgentState):
    project_id: str                  # 项目标识（隔离关键）
    execution_plan: Optional[Dict]   # 执行计划
    current_task_index: int          # 当前任务索引
    sub_agent_results: Dict          # 子Agent结果
    requires_multi_agent: bool       # 是否需要多Agent
    plan_refinement_count: int       # 计划优化次数
```

#### SubAgentState (子Agent状态)
```python
class SubAgentState(dict):
    agent_id: str                    # Agent标识
    agent_name: str                  # Agent名称
    task: Dict[str, Any]             # 任务描述
    task_id: str                     # 任务ID
    messages: List[BaseMessage]      # Agent内部消息
    context: Dict[str, Any]          # 执行上下文
    result: Optional[Dict]           # 执行结果
    status: str                      # 状态：pending/in_progress/completed/failed
    metadata: Dict[str, Any]         # 元数据
```

## 项目隔离机制

### 1. 项目级实例化
每个项目创建独立的`FilmetoAgent`实例：
```python
# 项目1
agent1 = FilmetoAgent(workspace, project1)
agent1.project_id == "project1"  # 独立标识

# 项目2
agent2 = FilmetoAgent(workspace, project2)
agent2.project_id == "project2"  # 独立标识
```

### 2. 对话隔离
- 每个项目有独立的`ConversationManager`
- 对话历史存储在项目目录下：`{project_path}/agent/conversations/`
- 不同项目的对话完全隔离

### 3. 状态隔离
- `ProductionAgentState`包含`project_id`字段
- 所有状态操作都在项目上下文内进行
- LangGraph的checkpointer使用`thread_id`（conversation_id）确保隔离

### 4. 上下文隔离
```python
# 每个Agent实例维护项目特定上下文
context = {
    "workspace": workspace,
    "project": project,          # 项目特定
    "shared_state": {}           # 项目内共享
}
```

## Multi-Agent协作流程

### 1. 简单任务流程
```
用户请求
  ↓
question_understanding (分析请求)
  ↓
coordinator (协调执行)
  ↓ [可能调用工具]
use_tools
  ↓
respond (生成响应)
```

### 2. 复杂任务流程（Multi-Agent）
```
用户请求
  ↓
question_understanding (确定需要多Agent)
  ↓
planner (创建执行计划)
  ↓
execute_sub_agent_plan (并行执行子Agent)
  ├── DirectorAgent.graph.invoke()    # 独立Subgraph
  ├── ScreenwriterAgent.graph.invoke() # 独立Subgraph
  └── ...
  ↓
review_plan (审查结果)
  ↓ [需要优化]
refine_plan → execute_sub_agent_plan
  ↓ [通过审查]
synthesize_results (综合结果)
  ↓
respond (生成响应)
```

### 3. 子Agent执行流程
每个子Agent内部的Subgraph：
```
SubAgentState (初始)
  ↓
execute_skill (执行技能)
  - 从state获取task和parameters
  - 调用对应的Skill
  - 更新state.result
  ↓
evaluate_result (评估结果)
  - 检查执行状态
  - 更新quality_score
  - 设置最终status
  ↓
END (返回最终state)
```

## 状态通信机制

### 主Agent → 子Agent
```python
# 创建子Agent初始状态
sub_agent_state = {
    "agent_id": "Director",
    "task": {"skill_name": "storyboard", "parameters": {...}},
    "context": {
        "workspace": workspace,
        "project": project,
        "shared_state": main_agent_state["context"]["shared_state"]
    },
    # ...
}

# 调用子Agent的Subgraph
result = await director_agent.graph.ainvoke(sub_agent_state)
```

### 子Agent → 主Agent
```python
# 子Agent执行完成后，结果存储在其state中
sub_result = {
    "status": "completed",
    "output": {...},
    "quality_score": 0.85
}

# 主Agent收集结果
main_state["sub_agent_results"][task_id] = sub_result
```

### 子Agent间共享
```python
# 通过shared_state共享数据
context.set_shared_data("Director_storyboard", storyboard_data)

# 其他Agent可以访问
shared_data = context.get_shared_data("Director_storyboard")
```

## 可观察性

### 1. Agent独立性
- 每个子Agent是独立的Subgraph，可以单独测试
- 每个Agent有自己的状态和消息历史
- 支持独立的日志和监控

### 2. 执行追踪
```python
# 主Agent流式输出
async for event in production_agent.stream(messages):
    # event包含节点名称和输出
    node_name, node_output = event
    # 可追踪每个节点的执行
```

### 3. 状态检查点
- LangGraph的checkpointer自动保存状态
- 可以恢复任意checkpoint继续执行
- 支持时间旅行调试

## 关键代码文件

### 核心文件
- `agent/filmeto_agent.py` - FilmetoAgent主类
- `agent/production_agent.py` - ProductionAgent（新增）
- `agent/graph/state.py` - 状态定义
- `agent/sub_agents/base.py` - 子Agent基类

### 节点文件
- `agent/nodes/question_understanding.py`
- `agent/nodes/planner.py`
- `agent/nodes/coordinator.py`
- `agent/nodes/executor.py`
- `agent/nodes/response.py`
- `agent/nodes/sub_agent_executor.py`

### 子Agent文件
- `agent/sub_agents/director.py`
- `agent/sub_agents/screenwriter.py`
- `agent/sub_agents/actor.py`
- `agent/sub_agents/editor.py`
- `agent/sub_agents/sound_mixer.py`
- `agent/sub_agents/makeup_artist.py`
- `agent/sub_agents/supervisor.py`

### 注册和管理
- `agent/sub_agents/registry.py` - 子Agent注册表（已移除Production）
- `agent/tools.py` - 工具注册

## 测试

测试文件：`tests/test_new_architecture.py`

测试覆盖：
- ✅ 项目隔离验证
- ✅ 子Agent独立性验证
- ✅ 状态结构验证
- ✅ 状态隔离验证
- ✅ ProductionAgent初始化
- ✅ 对话隔离验证

运行测试：
```bash
pytest tests/test_new_architecture.py -v
```

## 优势总结

### 1. 项目隔离
- ✅ 不同项目的对话完全独立
- ✅ 状态不会跨项目污染
- ✅ 支持多项目并发执行

### 2. Agent独立性
- ✅ 每个Agent是独立的Subgraph，易于维护
- ✅ 可以独立测试每个Agent
- ✅ 易于扩展新的Agent

### 3. 可维护性
- ✅ 清晰的职责划分
- ✅ 标准化的接口
- ✅ 易于理解的架构

### 4. 可观察性
- ✅ 每个Agent的执行可追踪
- ✅ 状态变化可记录
- ✅ 支持调试和监控

### 5. 灵活性
- ✅ 主Agent流程可定制
- ✅ 子Agent工作流可独立修改
- ✅ 易于添加新的节点和Agent

## 迁移指南

从旧架构迁移到新架构：

### API兼容性
`FilmetoAgent`的外部API保持不变：
- ✅ `chat_stream()` - 流式对话
- ✅ `chat()` - 非流式对话
- ✅ `create_conversation()` - 创建对话
- ✅ `get_conversation_history()` - 获取历史
- ✅ `update_context()` - 更新上下文

### 内部变化
- `self.graph` → `self.production_agent.graph`
- 移除了`_build_multi_agent_graph()`
- 移除了`_setup_stream_emitters()`
- Production Agent不再作为子Agent注册

### 使用方式不变
```python
# 创建Agent（API不变）
agent = FilmetoAgent(workspace, project)

# 流式对话（API不变）
async for token in agent.chat_stream("创建一个故事"):
    print(token, end="")

# 非流式对话（API不变）
response = await agent.chat("创建一个故事")
```

## 未来扩展

### 1. Agent类型扩展
- 可以轻松添加新的专业Agent
- 每个Agent都是独立的Subgraph

### 2. 工作流定制
- 可以为不同项目类型定制ProductionAgent的工作流
- 支持动态节点组合

### 3. 分布式执行
- 子Agent的Subgraph架构天然支持分布式执行
- 可以将不同Agent部署到不同节点

### 4. 高级监控
- 基于独立Subgraph的监控系统
- 实时性能分析
- 执行路径可视化

---

**架构优化完成日期**: 2026-01-11
**测试状态**: ✅ 所有测试通过 (9/9)
