# -*- coding: utf-8 -*-
"""
Project Info Widget for Startup Mode

This widget displays detailed information about the selected project
in the right workspace area of the startup mode.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QTabWidget, QScrollArea, QProgressBar,
    QTextEdit, QGridLayout, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QPixmap, QPainter

from app.data.workspace import Workspace
from app.data.project import Project
from app.ui.base_widget import BaseWidget
from utils.i18n_utils import tr


class VideoPreviewWidget(QFrame):
    """Widget for previewing project output video."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("video_preview")
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview placeholder
        self.preview_label = QLabel(tr("暂无视频预览"))
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1e1f22;
                color: #666666;
                border-radius: 8px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.preview_label)
        
        self.setStyleSheet("""
            QFrame#video_preview {
                background-color: #1e1f22;
                border-radius: 8px;
            }
        """)
    
    def set_video_path(self, path: str):
        """Set the video path for preview."""
        if path:
            # TODO: Implement actual video preview
            self.preview_label.setText(tr("视频: ") + path.split('/')[-1])
        else:
            self.preview_label.setText(tr("暂无视频预览"))


class StatCard(QFrame):
    """Widget for displaying a single statistic."""
    
    def __init__(self, title: str, value: str, icon: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card")
        self.setFixedHeight(80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #E1E1E1; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_label)
        
        self.setStyleSheet("""
            QFrame#stat_card {
                background-color: #2d2d2d;
                border-radius: 8px;
                border: 1px solid #3c3f41;
            }
        """)
    
    def set_value(self, value: str):
        """Update the value."""
        self.value_label.setText(value)


class BudgetProgressWidget(QFrame):
    """Widget for displaying budget progress."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("budget_progress")
        self.setFixedHeight(100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Title row
        title_row = QHBoxLayout()
        title_label = QLabel(tr("预算使用"))
        title_label.setStyleSheet("color: #888888; font-size: 12px;")
        title_row.addWidget(title_label)
        title_row.addStretch()
        
        self.budget_text = QLabel("$0 / $0")
        self.budget_text.setStyleSheet("color: #E1E1E1; font-size: 14px;")
        title_row.addWidget(self.budget_text)
        layout.addLayout(title_row)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #3c3f41;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #4080ff;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Percentage
        self.percentage_label = QLabel("0%")
        self.percentage_label.setStyleSheet("color: #4080ff; font-size: 12px;")
        layout.addWidget(self.percentage_label)
        
        self.setStyleSheet("""
            QFrame#budget_progress {
                background-color: #2d2d2d;
                border-radius: 8px;
                border: 1px solid #3c3f41;
            }
        """)
    
    def set_budget(self, used: float, total: float):
        """Update the budget progress."""
        self.budget_text.setText(f"${used:.2f} / ${total:.2f}")
        if total > 0:
            percentage = int((used / total) * 100)
            self.progress_bar.setValue(percentage)
            self.percentage_label.setText(f"{percentage}%")
        else:
            self.progress_bar.setValue(0)
            self.percentage_label.setText("0%")


class StoryDescriptionWidget(QFrame):
    """Widget for displaying and editing story description."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("story_description")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(tr("故事描述"))
        title_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Description text
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setPlaceholderText(tr("暂无故事描述..."))
        self.description_text.setMinimumHeight(100)
        self.description_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1f22;
                border: none;
                border-radius: 6px;
                color: #E1E1E1;
                padding: 8px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.description_text)
        
        self.setStyleSheet("""
            QFrame#story_description {
                background-color: #2d2d2d;
                border-radius: 8px;
                border: 1px solid #3c3f41;
            }
        """)
    
    def set_description(self, text: str):
        """Set the story description."""
        self.description_text.setText(text or "")


class ProjectInfoWidget(BaseWidget):
    """Widget for displaying project information in the startup right workspace."""
    
    edit_project = Signal(str)  # Emits project name when edit is requested
    
    def __init__(self, workspace: Workspace, parent=None):
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        
        self.setObjectName("project_info_widget")
        self._current_project_name = None
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 0, 16, 0)
        main_layout.setSpacing(0)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("project_tabs")
        
        # Basic info tab
        basic_tab = QWidget()
        self._setup_basic_tab(basic_tab)
        self.tab_widget.addTab(basic_tab, tr("基础信息"))
        
        main_layout.addWidget(self.tab_widget)
    
    def _setup_basic_tab(self, tab: QWidget):
        """Set up the basic info tab."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(16)
        
        # Header with project name and edit button
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.project_name_label = QLabel()
        self.project_name_label.setStyleSheet("color: #E1E1E1; font-size: 24px; font-weight: bold;")
        header_layout.addWidget(self.project_name_label)
        
        header_layout.addStretch()
        
        self.edit_button = QPushButton(tr("编辑项目"))
        self.edit_button.setFixedHeight(36)
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #4080ff;
                border: none;
                border-radius: 6px;
                color: #FFFFFF;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5090ff;
            }
            QPushButton:pressed {
                background-color: #3070ee;
            }
        """)
        header_layout.addWidget(self.edit_button)
        
        layout.addWidget(header)
        
        # Video preview area
        self.video_preview = VideoPreviewWidget()
        layout.addWidget(self.video_preview)
        
        # Stats grid
        stats_widget = QWidget()
        stats_layout = QGridLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(12)
        
        self.timeline_stat = StatCard(tr("时间线项目"), "0")
        stats_layout.addWidget(self.timeline_stat, 0, 0)
        
        self.task_stat = StatCard(tr("任务数量"), "0")
        stats_layout.addWidget(self.task_stat, 0, 1)
        
        layout.addWidget(stats_widget)
        
        # Budget progress
        self.budget_widget = BudgetProgressWidget()
        layout.addWidget(self.budget_widget)
        
        # Story description
        self.story_widget = StoryDescriptionWidget()
        layout.addWidget(self.story_widget)
        
        layout.addStretch()
        
        scroll_area.setWidget(content)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)
    
    def _apply_styles(self):
        """Apply styles to the widget."""
        self.setStyleSheet("""
            QWidget#project_info_widget {
                background-color: #2b2b2b;
            }
            QTabWidget#project_tabs {
                background-color: #2b2b2b;
            }
            QTabWidget#project_tabs::pane {
                background-color: #2b2b2b;
                border: none;
            }
            QTabWidget#project_tabs > QTabBar::tab {
                background-color: #2b2b2b;
                color: #888888;
                padding: 8px 16px;
                margin-right: 4px;
                border: none;
                border-bottom: 2px solid transparent;
            }
            QTabWidget#project_tabs > QTabBar::tab:selected {
                color: #E1E1E1;
                border-bottom: 2px solid #4080ff;
            }
            QTabWidget#project_tabs > QTabBar::tab:hover:!selected {
                color: #AAAAAA;
            }
        """)
    
    def set_project(self, project_name: str):
        """Set the project to display."""
        self._current_project_name = project_name
        
        if not project_name:
            self.project_name_label.setText("")
            self.timeline_stat.set_value("0")
            self.task_stat.set_value("0")
            self.budget_widget.set_budget(0, 0)
            self.story_widget.set_description("")
            return
        
        self.project_name_label.setText(project_name)
        
        # Get project data
        project = self.workspace.project_manager.get_project(project_name)
        if project:
            config = project.get_config()
            
            # Update stats
            timeline_count = config.get('timeline_index', 0)
            self.timeline_stat.set_value(str(timeline_count))
            
            task_count = config.get('task_index', 0)
            self.task_stat.set_value(str(task_count))
            
            # Budget info (if available)
            budget_used = config.get('budget_used', 0)
            budget_total = config.get('budget_total', 100)
            self.budget_widget.set_budget(budget_used, budget_total)
            
            # Story description
            story = config.get('story_description', '')
            self.story_widget.set_description(story)
    
    def _on_edit_clicked(self):
        """Handle edit button click."""
        if self._current_project_name:
            self.edit_project.emit(self._current_project_name)
