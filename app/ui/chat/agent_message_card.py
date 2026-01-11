"""Agent message card widget for multi-agent chat display.

This module provides a card widget for displaying individual agent messages
with support for streaming content, structured data, and visual differentiation.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QSizePolicy, QProgressBar, QScrollArea
)
from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QIcon, QFont, QPen

from app.ui.base_widget import BaseWidget
from agent.streaming.protocol import (
    AgentRole, ContentType, StructuredContent,
    PlanContent, TaskContent, MediaContent, ReferenceContent, ThinkingContent
)

if TYPE_CHECKING:
    from app.data.workspace import Workspace


class AgentAvatarWidget(QWidget):
    """Avatar widget for agent display."""
    
    def __init__(self, role: AgentRole, size: int = 32, parent=None):
        """Initialize avatar widget."""
        super().__init__(parent)
        self.role = role
        self.size = size
        self.setFixedSize(size, size)
        self._create_avatar()
    
    def _create_avatar(self):
        """Create the avatar pixmap."""
        pixmap = QPixmap(self.size, self.size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw circular background
        bg_color = QColor(self.role.color)
        path = QPainterPath()
        path.addEllipse(0, 0, self.size, self.size)
        painter.fillPath(path, bg_color)
        
        # Draw icon
        icon_char = self.role.icon_char
        if len(icon_char) == 1 and ord(icon_char) < 128:
            # Regular letter
            font = QFont()
            font.setPointSize(self.size // 2)
            font.setBold(True)
            painter.setFont(font)
        else:
            # Emoji or iconfont
            font = QFont()
            font.setPointSize(self.size // 2 - 2)
            painter.setFont(font)
        
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(0, 0, self.size, self.size, Qt.AlignCenter, icon_char)
        
        painter.end()
        
        # Set as background
        self.pixmap = pixmap
    
    def paintEvent(self, event):
        """Paint the avatar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, self.pixmap)


class ThinkingIndicator(QWidget):
    """Animated thinking indicator."""
    
    def __init__(self, parent=None):
        """Initialize thinking indicator."""
        super().__init__(parent)
        self.setFixedHeight(24)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Thinking dots
        self.dots_label = QLabel("⋯", self)
        self.dots_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 16px;
            }
        """)
        
        self.text_label = QLabel("Thinking...", self)
        self.text_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                font-style: italic;
            }
        """)
        
        layout.addWidget(self.dots_label)
        layout.addWidget(self.text_label)
        layout.addStretch()
    
    def set_text(self, text: str):
        """Set thinking text."""
        if text:
            display_text = text[:80] + "..." if len(text) > 80 else text
            self.text_label.setText(display_text)
        else:
            self.text_label.setText("Thinking...")


class TaskStatusWidget(QWidget):
    """Widget for displaying task execution status."""
    
    def __init__(self, task_content: TaskContent, parent=None):
        """Initialize task status widget."""
        super().__init__(parent)
        self.task_content = task_content
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        data = self.task_content.data
        status = data.get("status", "pending")
        skill_name = data.get("skill_name", "Unknown")
        message = data.get("message", "")
        quality_score = data.get("quality_score")
        
        # Status icon
        status_icons = {
            "pending": "⏳",
            "running": "🔄",
            "success": "✅",
            "failed": "❌",
        }
        icon_label = QLabel(status_icons.get(status, "•"), self)
        icon_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(icon_label)
        
        # Skill name
        skill_label = QLabel(skill_name, self)
        skill_label.setStyleSheet("""
            QLabel {
                color: #e1e1e1;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        layout.addWidget(skill_label)
        
        # Message
        if message:
            msg_label = QLabel(message[:100] + "..." if len(message) > 100 else message, self)
            msg_label.setStyleSheet("""
                QLabel {
                    color: #aaaaaa;
                    font-size: 11px;
                }
            """)
            layout.addWidget(msg_label)
        
        layout.addStretch()
        
        # Quality score
        if quality_score is not None:
            score_label = QLabel(f"{quality_score:.0%}", self)
            score_color = "#82e0aa" if quality_score >= 0.7 else "#f39c12" if quality_score >= 0.4 else "#e74c3c"
            score_label.setStyleSheet(f"""
                QLabel {{
                    color: {score_color};
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
            layout.addWidget(score_label)
        
        # Style based on status
        bg_colors = {
            "pending": "#3d3f4e",
            "running": "#2c3e50",
            "success": "#1e3d1e",
            "failed": "#3d1e1e",
        }
        bg_color = bg_colors.get(status, "#3d3f4e")
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 4px;
            }}
        """)


class PlanDisplayWidget(QWidget):
    """Widget for displaying execution plan."""
    
    def __init__(self, plan_content: PlanContent, parent=None):
        """Initialize plan display widget."""
        super().__init__(parent)
        self.plan_content = plan_content
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        data = self.plan_content.data
        description = data.get("description", "")
        phase = data.get("phase", "")
        tasks = data.get("tasks", [])
        
        # Header
        header = QLabel("📋 Execution Plan", self)
        header.setStyleSheet("""
            QLabel {
                color: #7c4dff;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        layout.addWidget(header)
        
        # Phase
        if phase:
            phase_label = QLabel(f"Phase: {phase.replace('_', ' ').title()}", self)
            phase_label.setStyleSheet("""
                QLabel {
                    color: #aaaaaa;
                    font-size: 11px;
                }
            """)
            layout.addWidget(phase_label)
        
        # Description
        if description:
            desc_label = QLabel(description[:200] + "..." if len(description) > 200 else description, self)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("""
                QLabel {
                    color: #e1e1e1;
                    font-size: 11px;
                }
            """)
            layout.addWidget(desc_label)
        
        # Tasks summary
        if tasks:
            tasks_label = QLabel(f"Tasks: {len(tasks)}", self)
            tasks_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 11px;
                }
            """)
            layout.addWidget(tasks_label)
            
            # Task list (abbreviated)
            for i, task in enumerate(tasks[:5]):
                agent = task.get("agent_name", "Unknown")
                skill = task.get("skill_name", "Unknown")
                task_label = QLabel(f"  {i+1}. {agent}: {skill}", self)
                task_label.setStyleSheet("""
                    QLabel {
                        color: #aaaaaa;
                        font-size: 10px;
                    }
                """)
                layout.addWidget(task_label)
            
            if len(tasks) > 5:
                more_label = QLabel(f"  ... and {len(tasks) - 5} more", self)
                more_label.setStyleSheet("""
                    QLabel {
                        color: #666666;
                        font-size: 10px;
                        font-style: italic;
                    }
                """)
                layout.addWidget(more_label)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #2a2d3e;
                border: 1px solid #7c4dff;
                border-radius: 6px;
            }
        """)


class MediaDisplayWidget(QWidget):
    """Widget for displaying media content."""
    
    def __init__(self, media_content: MediaContent, parent=None):
        """Initialize media display widget."""
        super().__init__(parent)
        self.media_content = media_content
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        data = self.media_content.data
        media_type = data.get("media_type", "image")
        title = data.get("title", "")
        description = data.get("description", "")
        
        # Media type icon
        icons = {"image": "🖼️", "video": "🎬", "audio": "🎵"}
        type_label = QLabel(f"{icons.get(media_type, '📁')} {media_type.title()}", self)
        type_label.setStyleSheet("""
            QLabel {
                color: #e1e1e1;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        layout.addWidget(type_label)
        
        # Title
        if title:
            title_label = QLabel(title, self)
            title_label.setStyleSheet("""
                QLabel {
                    color: #aaaaaa;
                    font-size: 11px;
                }
            """)
            layout.addWidget(title_label)
        
        # Description
        if description:
            desc_label = QLabel(description[:100], self)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 10px;
                }
            """)
            layout.addWidget(desc_label)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #505254;
                border-radius: 4px;
            }
        """)


class ReferenceDisplayWidget(QWidget):
    """Widget for displaying reference content."""
    
    def __init__(self, ref_content: ReferenceContent, parent=None):
        """Initialize reference display widget."""
        super().__init__(parent)
        self.ref_content = ref_content
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)
        
        data = self.ref_content.data
        ref_type = data.get("ref_type", "")
        name = data.get("name", "")
        
        # Reference type icon
        icons = {
            "timeline_item": "🎞️",
            "task": "📋",
            "character": "👤",
            "resource": "📦",
        }
        icon_label = QLabel(icons.get(ref_type, "🔗"), self)
        layout.addWidget(icon_label)
        
        # Name
        name_label = QLabel(name, self)
        name_label.setStyleSheet("""
            QLabel {
                color: #4a90d9;
                font-size: 11px;
                text-decoration: underline;
            }
        """)
        layout.addWidget(name_label)
        layout.addStretch()
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1a3a5a;
                border-radius: 3px;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)


class AgentMessageCard(QFrame):
    """Card widget for displaying an agent message in the chat.
    
    Features:
    - Visual differentiation by agent role
    - Streaming content support
    - Structured content display (plans, tasks, media, references)
    - Thinking indicator
    - Collapsible for long content
    """
    
    # Signals
    clicked = Signal(str)  # message_id
    reference_clicked = Signal(str, str)  # ref_type, ref_id
    
    def __init__(
        self,
        message_id: str,
        agent_name: str,
        agent_role: AgentRole,
        parent=None
    ):
        """Initialize agent message card."""
        super().__init__(parent)
        self.message_id = message_id
        self.agent_name = agent_name
        self.agent_role = agent_role
        
        self._content = ""
        self._is_thinking = False
        self._is_complete = False
        self._structured_contents: List[QWidget] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up UI."""
        self.setObjectName("agent_message_card")
        self.setFrameShape(QFrame.NoFrame)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # Header row (avatar + name)
        header_row = QWidget(self)
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        # Avatar
        self.avatar = AgentAvatarWidget(self.agent_role, size=28, parent=header_row)
        header_layout.addWidget(self.avatar)
        
        # Name and role
        name_widget = QWidget(header_row)
        name_layout = QVBoxLayout(name_widget)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(0)
        
        self.name_label = QLabel(self.agent_name or self.agent_role.display_name, name_widget)
        self.name_label.setStyleSheet(f"""
            QLabel {{
                color: {self.agent_role.color};
                font-size: 12px;
                font-weight: bold;
            }}
        """)
        name_layout.addWidget(self.name_label)
        
        if self.agent_name and self.agent_name != self.agent_role.display_name:
            role_label = QLabel(self.agent_role.display_name, name_widget)
            role_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 10px;
                }
            """)
            name_layout.addWidget(role_label)
        
        header_layout.addWidget(name_widget)
        header_layout.addStretch()
        
        main_layout.addWidget(header_row)
        
        # Thinking indicator
        self.thinking_indicator = ThinkingIndicator(self)
        self.thinking_indicator.setVisible(False)
        main_layout.addWidget(self.thinking_indicator)
        
        # Content label
        self.content_label = QLabel(self)
        self.content_label.setObjectName("message_content")
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self.content_label.setStyleSheet("""
            QLabel#message_content {
                color: #e1e1e1;
                font-size: 13px;
                padding: 4px 0px;
            }
        """)
        main_layout.addWidget(self.content_label)
        
        # Structured content container
        self.structured_container = QWidget(self)
        self.structured_layout = QVBoxLayout(self.structured_container)
        self.structured_layout.setContentsMargins(0, 4, 0, 0)
        self.structured_layout.setSpacing(6)
        main_layout.addWidget(self.structured_container)
        
        # Apply card styling
        self._apply_style()
    
    def _apply_style(self):
        """Apply card styling based on agent role."""
        border_color = self.agent_role.color
        self.setStyleSheet(f"""
            QFrame#agent_message_card {{
                background-color: #2b2d30;
                border-left: 3px solid {border_color};
                border-radius: 6px;
                margin: 2px 0px;
            }}
        """)
    
    def set_content(self, content: str):
        """Set the content (replace)."""
        self._content = content
        self.content_label.setText(content)
        self.content_label.setVisible(bool(content))
    
    def append_content(self, content: str):
        """Append content."""
        self._content += content
        self.content_label.setText(self._content)
        self.content_label.setVisible(True)
    
    def get_content(self) -> str:
        """Get current content."""
        return self._content
    
    def set_thinking(self, is_thinking: bool, thinking_text: str = ""):
        """Set thinking state."""
        self._is_thinking = is_thinking
        self.thinking_indicator.setVisible(is_thinking)
        if thinking_text:
            self.thinking_indicator.set_text(thinking_text)
    
    def set_complete(self, is_complete: bool):
        """Set completion state."""
        self._is_complete = is_complete
        if is_complete:
            self.thinking_indicator.setVisible(False)
    
    def set_error(self, error_message: str):
        """Set error state."""
        self._is_complete = True
        self.thinking_indicator.setVisible(False)
        
        # Show error in content
        self.set_content(f"❌ Error: {error_message}")
        self.content_label.setStyleSheet("""
            QLabel#message_content {
                color: #e74c3c;
                font-size: 13px;
                padding: 4px 0px;
            }
        """)
    
    def add_structured_content(self, structured: StructuredContent):
        """Add structured content widget."""
        widget = None
        
        if isinstance(structured, PlanContent):
            widget = PlanDisplayWidget(structured, self.structured_container)
        elif isinstance(structured, TaskContent):
            widget = TaskStatusWidget(structured, self.structured_container)
        elif isinstance(structured, MediaContent):
            widget = MediaDisplayWidget(structured, self.structured_container)
        elif isinstance(structured, ReferenceContent):
            widget = ReferenceDisplayWidget(structured, self.structured_container)
            # Connect click signal
            widget.mousePressEvent = lambda e: self.reference_clicked.emit(
                structured.data.get("ref_type", ""),
                structured.data.get("ref_id", "")
            )
        
        if widget:
            self.structured_layout.addWidget(widget)
            self._structured_contents.append(widget)
    
    def clear_structured_content(self):
        """Clear all structured content."""
        for widget in self._structured_contents:
            widget.setParent(None)
            widget.deleteLater()
        self._structured_contents.clear()


class UserMessageCard(QFrame):
    """Card widget for displaying user messages."""
    
    def __init__(self, content: str, parent=None):
        """Initialize user message card."""
        super().__init__(parent)
        self.setObjectName("user_message_card")
        self._setup_ui(content)
    
    def _setup_ui(self, content: str):
        """Set up UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Header row
        header_row = QWidget(self)
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        # Spacer to push to right
        header_layout.addStretch()
        
        # Name
        name_label = QLabel("You", header_row)
        name_label.setStyleSheet("""
            QLabel {
                color: #35373a;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(name_label)
        
        # Avatar
        avatar = AgentAvatarWidget(AgentRole.USER, size=28, parent=header_row)
        header_layout.addWidget(avatar)
        
        layout.addWidget(header_row)
        
        # Content
        content_label = QLabel(content, self)
        content_label.setObjectName("user_content")
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setStyleSheet("""
            QLabel#user_content {
                color: #e1e1e1;
                font-size: 13px;
                padding: 8px;
                background-color: #35373a;
                border-radius: 5px;
            }
        """)
        layout.addWidget(content_label)
        
        self.setStyleSheet("""
            QFrame#user_message_card {
                background-color: transparent;
                margin: 2px 0px;
            }
        """)
