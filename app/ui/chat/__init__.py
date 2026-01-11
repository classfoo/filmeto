"""Chat UI components for agent panel."""

# Lazy loading - do not import at package level
# Import directly from submodules when needed:
#   from app.ui.chat.chat_history_widget import ChatHistoryWidget
#   from app.ui.chat.agent_message_card import AgentMessageCard, UserMessageCard

__all__ = [
    'ChatHistoryWidget',
    'AgentMessageCard',
    'UserMessageCard',
    'AgentAvatarWidget',
    'ThinkingIndicator',
    'TaskStatusWidget',
    'PlanDisplayWidget',
    'MediaDisplayWidget',
    'ReferenceDisplayWidget',
]
