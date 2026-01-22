"""
Skill content widget for displaying skill execution status.

This module provides a widget for displaying skill execution with support for
different states: start, progress, and end.
"""
from typing import Any, Dict

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.ui.chat.message.base_structured_content_widget import BaseStructuredContentWidget
from agent.chat.agent_chat_message import StructureContent, ContentType


class SkillContentWidget(BaseStructuredContentWidget):
    """
    Widget for displaying skill execution status with different states.
    
    Supports start, progress, and end states for skill execution.
    """
    
    def __init__(self, structure_content: StructureContent, parent=None, available_width=None):
        """
        Initialize the skill content widget.

        Args:
            structure_content: The structure content to display
            parent: Parent widget
            available_width: Available width from parent container
        """
        super().__init__(structure_content, parent)
        # Store the available width
        self.available_width = available_width
        if self.available_width is not None:
            # Set the maximum width of the container frame to the available width
            self.container_frame.setFixedWidth(self.available_width)
    
    def _setup_ui(self):
        """Set up the UI components."""
        self.setObjectName("skill_content_widget")

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)

        # Container frame
        self.container_frame = QFrame()
        self.container_frame.setObjectName("skill_container_frame")
        self.container_frame.setStyleSheet("""
            QFrame#skill_container_frame {
                border: 1px solid #4a90e2;
                border-radius: 5px;
                background-color: #2d2d2d;
            }
        """)
        # Set size policy to expand horizontally to fill available space initially
        # but we'll constrain it with maximum width in resizeEvent
        #self.container_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Frame layout
        self.frame_layout = QVBoxLayout(self.container_frame)
        self.frame_layout.setContentsMargins(8, 8, 8, 8)
        self.frame_layout.setSpacing(5)

        # Title label
        self.title_label = QLabel()
        self.title_label.setObjectName("skill_title_label")
        self.title_label.setStyleSheet("""
            QLabel#skill_title_label {
                color: #4a90e2;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        self.title_label.setAlignment(Qt.AlignLeft)
        # Allow the title to expand horizontally
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Status label
        self.status_label = QLabel()
        self.status_label.setObjectName("skill_status_label")
        self.status_label.setStyleSheet("""
            QLabel#skill_status_label {
                color: #ffffff;
                font-size: 13px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignLeft)
        self.status_label.setWordWrap(True)
        # Allow the status to expand horizontally
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("skill_progress_bar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #4a90e2;
                border-radius: 3px;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 2px;
            }
        """)
        # Allow the progress bar to expand horizontally
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Add widgets to frame layout
        self.frame_layout.addWidget(self.title_label)
        self.frame_layout.addWidget(self.status_label)
        self.frame_layout.addWidget(self.progress_bar)

        # Add frame to main layout
        self.main_layout.addWidget(self.container_frame)

        # Set initial maximum width to a reasonable default
        # This will be updated when the widget is added to a parent
        # Use a single shot timer to ensure the parent hierarchy is established
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._update_width)
    
    def _apply_initial_state(self):
        """Apply the initial state based on structure content."""
        self.update_content(self.structure_content)

    def resizeEvent(self, event):
        """Handle resize events to update the widget's width."""
        super().resizeEvent(event)
        self._update_width()

    def _update_width(self):
        """Update the widget's width based on the parent's available width."""
        # Find the parent AgentMessageCard to get its available bubble width
        parent = self.parent()
        while parent:
            # Check if this is the bubble container or message card
            if hasattr(parent, '_available_bubble_width'):
                # This is the AgentMessageCard
                available_width = parent._available_bubble_width()
                # Set the maximum width of the container frame to the available width
                self.container_frame.setMaximumWidth(available_width)
                break
            elif hasattr(parent, 'sizeHint') and hasattr(parent, 'width'):
                # If the parent has a width, we can use it as a reference
                parent_width = parent.width()
                if parent_width > 0:
                    # Account for margins and padding
                    margins = self.main_layout.contentsMargins()
                    available_width = max(0, parent_width - margins.left() - margins.right())
                    self.container_frame.setMaximumWidth(available_width)
                    break
            parent = parent.parent()
    
    def update_content(self, structure_content: StructureContent):
        """
        Update the widget with new structure content.
        
        Args:
            structure_content: The new structure content to display
        """
        if structure_content.content_type != ContentType.SKILL:
            return  # This widget only handles skill content
        
        # Extract data from structure content
        data = structure_content.data
        status = data.get("status", "unknown")
        skill_name = data.get("skill_name", "Unknown Skill")
        message = data.get("message", "")
        result = data.get("result", "")
        
        # Update title
        self.title_label.setText(f"Skill: {skill_name}")
        
        # Update status and progress based on skill execution status
        if status == "starting":
            self.status_label.setText(f"Starting execution: {message}")
            self.progress_bar.setVisible(False)
        elif status == "in_progress":
            self.status_label.setText(f"In progress: {message}")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
        elif status == "completed":
            self.status_label.setText(f"Completed: {result}")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText(f"Status: {status}")
            self.progress_bar.setVisible(False)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the widget.
        
        Returns:
            Dictionary representing the current state
        """
        return {
            "title": self.title_label.text(),
            "status_text": self.status_label.text(),
            "progress_visible": self.progress_bar.isVisible(),
            "progress_value": self.progress_bar.value() if self.progress_bar.isVisible() else None
        }
    
    def set_state(self, state: Dict[str, Any]):
        """
        Set the state of the widget.

        Args:
            state: Dictionary representing the state to set
        """
        if "title" in state:
            self.title_label.setText(state["title"])
        if "status_text" in state:
            self.status_label.setText(state["status_text"])
        if "progress_visible" in state:
            self.progress_bar.setVisible(state["progress_visible"])
        if "progress_value" in state and state["progress_value"] is not None:
            self.progress_bar.setValue(state["progress_value"])

    def update_available_width(self, width: int):
        """Update the available width for this widget."""
        self.available_width = width
        if self.available_width is not None:
            # Set the maximum width of the container frame to the available width
            self.container_frame.setMaximumWidth(self.available_width)