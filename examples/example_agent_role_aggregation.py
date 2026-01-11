"""示例：演示主agent和子agent的消息聚合机制"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.streaming.protocol import (
    AgentRole,
    StreamEventEmitter,
    StreamEvent,
    StreamEventType,
)


def print_event(event: StreamEvent):
    """打印事件信息（模拟UI显示）"""
    event_type_icons = {
        StreamEventType.AGENT_START: "🚀",
        StreamEventType.AGENT_THINKING: "💭",
        StreamEventType.AGENT_CONTENT: "💬",
        StreamEventType.AGENT_COMPLETE: "✅",
        StreamEventType.PLAN_CREATED: "📋",
        StreamEventType.PLAN_TASK_START: "▶️",
        StreamEventType.PLAN_TASK_COMPLETE: "✔️",
    }
    
    icon = event_type_icons.get(event.event_type, "•")
    role_icon = event.agent_role.icon_char
    
    # 显示聚合后的角色名称
    agent_display = f"{role_icon} {event.agent_name}"
    
    # 如果有原始角色信息，在括号中显示
    original_name = event.metadata.get("original_name")
    if original_name and original_name != event.agent_name:
        agent_display += f" ({original_name})"
    
    print(f"{icon} [{agent_display}] {event.event_type.value}")
    
    if event.content:
        print(f"   内容: {event.content[:80]}...")
    
    if event.structured_content:
        print(f"   结构化内容: {event.structured_content.content_type.value}")
    
    print(f"   消息ID: {event.message_id[:8]}...")
    print()


def demo_main_agent_flow():
    """演示主agent的工作流程"""
    print("=" * 70)
    print("演示1: 主Agent工作流程")
    print("=" * 70)
    print()
    
    emitter = StreamEventEmitter()
    emitter.add_callback(print_event)
    
    # 1. 问题理解阶段
    emitter.emit_agent_start("QuestionUnderstanding", AgentRole.QUESTION_UNDERSTANDING)
    emitter.emit_agent_thinking("QuestionUnderstanding", "分析用户请求...")
    emitter.emit_agent_content("QuestionUnderstanding", "任务类型: full_production，需要多agent协作")
    
    # 2. 计划制定阶段
    emitter.emit_agent_start("Planner", AgentRole.PLANNER)
    emitter.emit_agent_thinking("Planner", "制定执行计划...")
    
    plan = {
        "description": "太空探险短片制作计划",
        "phase": "full_production",
        "tasks": [
            {"task_id": 1, "agent_name": "Screenwriter", "skill_name": "script_outline"},
            {"task_id": 2, "agent_name": "Director", "skill_name": "storyboard"},
        ],
        "success_criteria": "完成剧本和分镜"
    }
    emitter.emit_plan_created(plan, "Planner")
    
    # 3. 计划评审
    emitter.emit_agent_start("Reviewer", AgentRole.REVIEWER)
    emitter.emit_agent_content("Reviewer", "评审计划: 所有任务定义清晰，依赖关系合理")
    emitter.emit_agent_complete("Reviewer")
    
    print("\n注意：以上所有主agent角色的消息都共享同一个message_id\n")


def demo_sub_agent_execution():
    """演示子agent的任务执行"""
    print("=" * 70)
    print("演示2: 子Agent任务执行")
    print("=" * 70)
    print()
    
    emitter = StreamEventEmitter()
    emitter.add_callback(print_event)
    
    # 子agent 1: Screenwriter
    emitter.emit_agent_start("Screenwriter", AgentRole.SCREENWRITER)
    emitter.emit_agent_thinking("Screenwriter", "构思剧本大纲...")
    emitter.emit_agent_content("Screenwriter", "完成剧本大纲：太空探险主题，三幕结构")
    emitter.emit_agent_complete("Screenwriter", "剧本大纲创作完成，质量评分: 0.85")
    
    print()
    
    # 子agent 2: Director
    emitter.emit_agent_start("Director", AgentRole.DIRECTOR)
    emitter.emit_agent_thinking("Director", "设计分镜头...")
    emitter.emit_agent_content("Director", "完成分镜设计：15个主要场景，重点突出太空景观")
    emitter.emit_agent_complete("Director", "分镜设计完成，质量评分: 0.90")
    
    print()
    
    # 子agent 3: Actor
    emitter.emit_agent_start("Actor", AgentRole.ACTOR)
    emitter.emit_agent_thinking("Actor", "准备角色表演...")
    emitter.emit_agent_content("Actor", "完成角色塑造：宇航员形象鲜明，情感表达到位")
    emitter.emit_agent_complete("Actor", "角色表演完成，质量评分: 0.88")
    
    print("\n注意：每个子agent都有独立的message_id\n")


def demo_mixed_workflow():
    """演示完整的混合工作流"""
    print("=" * 70)
    print("演示3: 完整的混合工作流")
    print("=" * 70)
    print()
    
    emitter = StreamEventEmitter()
    emitter.add_callback(print_event)
    
    # 阶段1: 主agent分析和计划
    print("--- 阶段1: 主agent协调 ---\n")
    emitter.emit_agent_start("QuestionUnderstanding", AgentRole.QUESTION_UNDERSTANDING)
    emitter.emit_agent_content("QuestionUnderstanding", "理解任务需求")
    
    emitter.emit_agent_start("Planner", AgentRole.PLANNER)
    plan = {
        "description": "短片制作计划",
        "phase": "production",
        "tasks": [{"task_id": 1, "agent_name": "Director"}],
    }
    emitter.emit_plan_created(plan, "Planner")
    
    # 阶段2: 子agent执行任务
    print("\n--- 阶段2: 子agent执行 ---\n")
    emitter.emit_task_start(1, "Director", "scene_direction", "plan-123")
    emitter.emit_agent_start("Director", AgentRole.DIRECTOR)
    emitter.emit_agent_content("Director", "导演场景")
    emitter.emit_task_complete(1, "Director", "scene_direction", "success", "场景导演完成", 0.92)
    
    # 阶段3: 主agent综合结果
    print("\n--- 阶段3: 主agent综合 ---\n")
    emitter.emit_agent_start("Synthesizer", AgentRole.SYNTHESIZER)
    emitter.emit_agent_content("Synthesizer", "综合所有任务结果，生成最终报告")
    emitter.emit_agent_complete("Synthesizer")
    
    print("\n观察到的消息分组：")
    print("- 主agent消息（阶段1和3）共享一个message_id")
    print("- 子agent消息（阶段2）有独立的message_id")
    print()


def demo_role_classification():
    """演示角色分类功能"""
    print("=" * 70)
    print("演示4: 角色分类检查")
    print("=" * 70)
    print()
    
    print("主Agent角色:")
    main_roles = [
        AgentRole.COORDINATOR,
        AgentRole.PLANNER,
        AgentRole.QUESTION_UNDERSTANDING,
        AgentRole.EXECUTOR,
    ]
    for role in main_roles:
        is_main = AgentRole.is_main_agent_role(role)
        print(f"  {role.icon_char} {role.display_name:25} → 主Agent: {is_main}")
    
    print("\n子Agent角色:")
    sub_roles = [
        AgentRole.DIRECTOR,
        AgentRole.SCREENWRITER,
        AgentRole.ACTOR,
        AgentRole.EDITOR,
    ]
    for role in sub_roles:
        is_sub = AgentRole.is_sub_agent_role(role)
        print(f"  {role.icon_char} {role.display_name:25} → 子Agent: {is_sub}")
    
    print()


if __name__ == "__main__":
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║           Agent消息聚合机制演示                                        ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print("\n")
    
    demo_role_classification()
    input("按回车继续演示1...")
    print("\n")
    
    demo_main_agent_flow()
    input("按回车继续演示2...")
    print("\n")
    
    demo_sub_agent_execution()
    input("按回车继续演示3...")
    print("\n")
    
    demo_mixed_workflow()
    
    print("\n")
    print("=" * 70)
    print("演示结束")
    print("=" * 70)
    print("\n关键要点：")
    print("1. 主agent的所有角色（coordinator, planner等）消息聚合到'MainAgent'")
    print("2. 子agent（director, actor等）各自维护独立的消息流")
    print("3. 原始角色信息保存在metadata中，便于调试")
    print("4. 这样的设计使UI显示更清晰，减少信息噪音")
    print()
