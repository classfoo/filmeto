#!/usr/bin/env python
"""Test script to verify message card layout fixes."""

import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QMainWindow
from PySide6.QtCore import QTimer

from app.ui.chat.agent_chat_message_card import AgentMessageCard, UserMessageCard
from agent.chat.agent_chat_message import AgentMessage, StructureContent, ContentType


def create_test_agent_message(text_content: str) -> AgentMessage:
    """Create a test agent message."""
    agent_msg = AgentMessage(
        message_id="test_msg_1",
        sender_id="test_agent",
        sender_name="Test Agent",
        content=text_content,
        timestamp=0
    )
    return agent_msg


def main():
    app = QApplication(sys.argv)

    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Message Card Layout Test")
    window.setGeometry(100, 100, 800, 600)

    # Create central widget with scroll area
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)

    # Add some test messages
    long_text = "This is a long message that should wrap properly within the message card. " * 10
    short_text = "Short message."

    # Add user message
    user_card = UserMessageCard(content=short_text)
    layout.addWidget(user_card)

    # Add agent message with short content
    agent_msg_short = create_test_agent_message(short_text)
    agent_card_short = AgentMessageCard(agent_message=agent_msg_short)
    layout.addWidget(agent_card_short)

    # Add agent message with long content
    agent_msg_long = create_test_agent_message(long_text)
    agent_card_long = AgentMessageCard(agent_message=agent_msg_long)
    layout.addWidget(agent_card_long)

    # Add agent message with code content
    agent_msg_code = create_test_agent_message("Here's some code:")
    
    # Add code structure content
    code_content = StructureContent(
        content_type=ContentType.CODE_BLOCK,
        data="def hello():\n    print('Hello, world!')",
        title="Sample Code",
        description="A simple function"
    )
    agent_msg_code.structured_content.append(code_content)
    
    agent_card_code = AgentMessageCard(agent_message=agent_msg_code)
    layout.addWidget(agent_card_code)

    # Add some padding at the bottom
    layout.addStretch()

    # Set the central widget
    window.setCentralWidget(central_widget)

    # Show the window
    window.show()

    # Exit after 5 seconds for automated testing
    QTimer.singleShot(5000, app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()