# -*- coding: utf-8 -*-
"""
Project List Widget for Startup Mode

This widget displays a list of projects in the left panel of the startup mode.
It includes a logo at the top, project list in the middle, and a toolbar at the bottom.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QLineEdit, QDialog,
    QDialogButtonBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QPainterPath

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from utils.i18n_utils import tr


class ProjectItemWidget(QFrame):
    """Widget representing a single project item in the list."""
    
    clicked = Signal(str)  # Emits project name when clicked
    edit_clicked = Signal(str)  # Emits project name when edit button clicked
    
    def __init__(self, project_name: str, is_selected: bool = False, parent=None):
        super().__init__(parent)
        self.project_name = project_name
        self._is_selected = is_selected
        
        self.setObjectName("project_item")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Project icon (first letter)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(32, 32)
        self._create_icon()
        layout.addWidget(self.icon_label)
        
        # Project name
        self.name_label = QLabel(project_name)
        self.name_label.setStyleSheet("color: #E1E1E1; font-size: 14px;")
        layout.addWidget(self.name_label, 1)
        
        # Edit button (only visible on hover or when selected)
        self.edit_button = QPushButton("\ue601")  # Edit icon
        self.edit_button.setFixedSize(24, 24)
        self.edit_button.setVisible(False)
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #888888;
                font-family: iconfont;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #4080ff;
            }
        """)
        layout.addWidget(self.edit_button)
        
        self._update_style()
    
    def _create_icon(self):
        """Create a rounded letter icon for the project."""
        size = 32
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background circle
        bg_color = QColor("#4080ff")
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawEllipse(0, 0, size, size)
        
        # Draw letter
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Sans-serif", 14, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 0, size, size, Qt.AlignCenter, self.project_name[0].upper())
        
        painter.end()
        self.icon_label.setPixmap(pixmap)
    
    def _update_style(self):
        """Update widget style based on selection state."""
        if self._is_selected:
            self.setStyleSheet("""
                QFrame#project_item {
                    background-color: #3d4f7c;
                    border-radius: 6px;
                    border: 1px solid #4080ff;
                }
            """)
            self.edit_button.setVisible(True)
        else:
            self.setStyleSheet("""
                QFrame#project_item {
                    background-color: transparent;
                    border-radius: 6px;
                    border: 1px solid transparent;
                }
                QFrame#project_item:hover {
                    background-color: #3c3f41;
                }
            """)
    
    def set_selected(self, selected: bool):
        """Set the selection state."""
        self._is_selected = selected
        self._update_style()
        self.edit_button.setVisible(selected)
    
    def enterEvent(self, event):
        """Show edit button on hover."""
        if not self._is_selected:
            self.edit_button.setVisible(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Hide edit button when not hovered (unless selected)."""
        if not self._is_selected:
            self.edit_button.setVisible(False)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press to select project."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.project_name)
        super().mousePressEvent(event)
    
    def _on_edit_clicked(self):
        """Handle edit button click."""
        self.edit_clicked.emit(self.project_name)


class ProjectListWidget(BaseWidget):
    """Widget for displaying the project list in the startup left panel."""
    
    project_selected = Signal(str)  # Emits project name when selected
    project_edit = Signal(str)  # Emits project name when edit is requested
    project_created = Signal(str)  # Emits project name when a new project is created
    
    def __init__(self, workspace: Workspace, parent=None):
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        
        self.setObjectName("project_list_widget")
        self.setFixedWidth(280)
        
        self._selected_project = None
        self._project_items = {}
        
        self._setup_ui()
        self._load_projects()
        self._apply_styles()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with logo and app name
        header = QWidget()
        header.setObjectName("project_list_header")
        header.setFixedHeight(80)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.setSpacing(12)
        
        # Logo placeholder
        logo_label = QLabel()
        logo_label.setFixedSize(40, 40)
        logo_pixmap = self._create_logo_pixmap()
        logo_label.setPixmap(logo_pixmap)
        header_layout.addWidget(logo_label)
        
        # App name
        app_name = QLabel("AniMaker")
        app_name.setStyleSheet("color: #E1E1E1; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(app_name)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #3c3f41;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # Project list area (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)
        
        self.project_list_container = QWidget()
        self.project_list_layout = QVBoxLayout(self.project_list_container)
        self.project_list_layout.setContentsMargins(8, 8, 8, 8)
        self.project_list_layout.setSpacing(4)
        self.project_list_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.project_list_container)
        layout.addWidget(scroll_area, 1)
        
        # Bottom toolbar
        toolbar = QWidget()
        toolbar.setObjectName("project_list_toolbar")
        toolbar.setFixedHeight(56)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(8)
        
        # Add project button
        self.add_button = QPushButton("\ue6b3")  # Add icon
        self.add_button.setToolTip(tr("新建项目"))
        self.add_button.setFixedSize(40, 40)
        self.add_button.clicked.connect(self._on_add_project)
        toolbar_layout.addWidget(self.add_button)
        
        toolbar_layout.addStretch()
        
        layout.addWidget(toolbar)
    
    def _create_logo_pixmap(self) -> QPixmap:
        """Create a placeholder logo pixmap."""
        size = 40
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw gradient background
        from PySide6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, size, size)
        gradient.setColorAt(0, QColor("#4080ff"))
        gradient.setColorAt(1, QColor("#8040ff"))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        
        # Draw rounded rectangle
        path = QPainterPath()
        path.addRoundedRect(0, 0, size, size, 8, 8)
        painter.drawPath(path)
        
        # Draw "A" letter
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Sans-serif", 20, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 0, size, size, Qt.AlignCenter, "A")
        
        painter.end()
        return pixmap
    
    def _apply_styles(self):
        """Apply styles to the widget."""
        self.setStyleSheet("""
            QWidget#project_list_widget {
                background-color: #1e1f22;
            }
            QWidget#project_list_header {
                background-color: #1e1f22;
            }
            QWidget#project_list_toolbar {
                background-color: #1e1f22;
                border-top: 1px solid #3c3f41;
            }
            QPushButton {
                background-color: #3c3f41;
                border: none;
                border-radius: 6px;
                color: #E1E1E1;
                font-family: iconfont;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #4c5052;
            }
            QPushButton:pressed {
                background-color: #2c2f31;
            }
        """)
    
    def _load_projects(self):
        """Load projects from the workspace."""
        project_names = self.workspace.project_manager.list_projects()
        
        # Clear existing items
        for item in self._project_items.values():
            item.deleteLater()
        self._project_items.clear()
        
        # Add project items
        for name in project_names:
            self._add_project_item(name)
        
        # Select the first project by default
        if project_names:
            self._select_project(project_names[0])
    
    def _add_project_item(self, project_name: str):
        """Add a project item to the list."""
        item = ProjectItemWidget(project_name)
        item.clicked.connect(self._select_project)
        item.edit_clicked.connect(self._on_project_edit)
        
        self.project_list_layout.addWidget(item)
        self._project_items[project_name] = item
    
    def _select_project(self, project_name: str):
        """Select a project in the list."""
        # Deselect previous
        if self._selected_project and self._selected_project in self._project_items:
            self._project_items[self._selected_project].set_selected(False)
        
        # Select new
        self._selected_project = project_name
        if project_name in self._project_items:
            self._project_items[project_name].set_selected(True)
        
        self.project_selected.emit(project_name)
    
    def _on_project_edit(self, project_name: str):
        """Handle project edit request."""
        self.project_edit.emit(project_name)
    
    def _on_add_project(self):
        """Handle add project button click."""
        from app.ui.dialog.custom_dialog import CustomDialog
        
        dialog = CustomDialog(self)
        dialog.set_title(tr("新建项目"))
        
        # Create content layout
        content_layout = QVBoxLayout()
        
        # Label
        label = QLabel(tr("请输入项目名称:"))
        label.setStyleSheet("color: #E1E1E1; font-size: 14px;")
        content_layout.addWidget(label)
        
        # Input field
        line_edit = QLineEdit()
        line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1e1f22;
                border: 1px solid #505254;
                border-radius: 5px;
                padding: 8px;
                color: #E1E1E1;
                selection-background-color: #4080ff;
                font-size: 14px;
            }
        """)
        content_layout.addWidget(line_edit)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            dialog
        )
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #3d3f4e;
                color: #E1E1E1;
                border: 1px solid #505254;
                border-radius: 5px;
                padding: 6px 15px;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #444654;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        content_layout.addWidget(button_box)
        
        dialog.setContentLayout(content_layout)
        line_edit.setFocus()
        
        if dialog.exec() == QDialog.Accepted:
            project_name = line_edit.text().strip()
            if project_name:
                try:
                    self.workspace.project_manager.create_project(project_name)
                    self._add_project_item(project_name)
                    self._select_project(project_name)
                    self.project_created.emit(project_name)
                except Exception as e:
                    print(f"Error creating project: {e}")
    
    def get_selected_project(self) -> str:
        """Get the currently selected project name."""
        return self._selected_project
    
    def refresh(self):
        """Refresh the project list."""
        self._load_projects()
