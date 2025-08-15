from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout,
                               QPushButton, QVBoxLayout, QSplitter, QMenu, QComboBox)
from PySide6.QtCore import Qt, Signal

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from app.ui.drawing_tools import DrawingToolsWidget
from app.ui.editor import ToolEditorWidget
from app.ui.layers import LayersWidget
from app.ui.mac_button import MacTitleBar
from app.ui.project_menu.project_menu import ProjectMenu
from app.ui.task_list import TaskListWidget
from app.ui.timeline.timeline import HorizontalTimeline
from app.ui.timeline.timeline_container import TimelineContainer
from app.ui.timeline.subtitle_timeline import SubtitleTimeline
from app.ui.timeline.voiceover_timeline import VoiceoverTimeline
from utils.i18n_utils import translation_manager, tr


class MainWindowTopBar(BaseWidget):
    # Signal to notify when language changes
    language_changed = Signal(str)

    def __init__(self, window, workspace: Workspace):
        super(MainWindowTopBar, self).__init__(workspace)
        self.setObjectName("main_window_top_bar")
        self.window = window
        # central_widget = QWidget(self)
        # central_widget.setObjectName("main_window_top_bar")
        # self.setAutoFillBackground(True)
        self.setFixedHeight(40)
        # widget = QWidget(self)
        # widget.setObjectName("main_window_top_bar")
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # mac title bar
        self.title_bar = MacTitleBar(window)
        self.title_bar.setObjectName("main_window_top_bar_left")
        # add to layout
        self.layout.addWidget(self.title_bar)
        self.layout.addWidget(ProjectMenu(workspace))
        self.layout.addSpacing(100)
        self.layout.addWidget(QPushButton("\ue83f", self))
        self.layout.addWidget(QPushButton("\ue846", self))
        # Add drawing tools widget
        self.layout.addSpacing(300)
        self.drawing_tools = DrawingToolsWidget(self, workspace)
        self.layout.addWidget(self.drawing_tools)


        self.layout.addStretch()

        # Language switcher button
        self.language_button = QPushButton("🌐", self)
        self.language_button.setObjectName("main_window_top_bar_button")
        self.language_button.setToolTip(tr("切换语言"))
        self.language_button.clicked.connect(self._show_language_menu)
        self.layout.addWidget(self.language_button)

        # Export button
        self.export_button = QPushButton("\ue61e", self)  # Play icon for export
        self.export_button.setObjectName("main_window_top_bar_button")
        self.export_button.setToolTip(tr("导出时间线"))
        self.export_button.clicked.connect(self._show_export_dialog)
        self.layout.addWidget(self.export_button)
        # settings
        # self.setting_button = QPushButton("C", self)
        # self.setting_button.setObjectName("main_window_top_bar_button")
        # self.layout.addWidget(self.setting_button)
        # mouse move
        self.draggable = True
        self.drag_start_position = None

        # Connect to language change signal
        translation_manager.language_changed.connect(self._on_language_changed)

    def mousePressEvent(self, event: QMouseEvent):
        self.draggable = True
        self.drag_start_position = event.globalPosition().toPoint() - self.window.pos()
        self.window.mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drag_start_position is None:
            return
        if self.draggable:
            # 移动窗口
            self.window.move(event.globalPosition().toPoint() - self.drag_start_position)
        self.window.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.draggable = False
        self.window.mouseReleaseEvent(event)

    def _show_language_menu(self):
        """Show language selection menu"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2c2c2c;
                color: #E1E1E1;
                border: 1px solid #505254;
            }
            QMenu::item:selected {
                background-color: #4080ff;
            }
        """)

        # Get available languages
        languages = translation_manager.get_available_languages()
        current_lang = translation_manager.get_current_language()

        for lang_code, lang_name in languages.items():
            action = menu.addAction(lang_name)
            action.setData(lang_code)
            # Mark current language
            if lang_code == current_lang:
                action.setText(f"✓ {lang_name}")
            action.triggered.connect(lambda checked=False, code=lang_code: self._switch_language(code))

        # Show menu below the button
        menu.exec(self.language_button.mapToGlobal(
            self.language_button.rect().bottomLeft()))

    def _switch_language(self, language_code):
        """Switch application language"""
        if translation_manager.switch_language(language_code):
            # Language changed signal will trigger _on_language_changed
            pass

    def _on_language_changed(self, language_code):
        """Called when language changes - update all UI text"""
        # Temporarily disable layout updates to prevent window expansion
        self.setUpdatesEnabled(False)
        self._update_ui_text()
        self.setUpdatesEnabled(True)
        # Force a single repaint
        self.update()

    def _update_ui_text(self):
        """Update UI text after language change"""
        self.language_button.setToolTip(tr("切换语言"))
        self.export_button.setToolTip(tr("导出时间线"))

    def _show_export_dialog(self):
        """Show the floating export panel"""
        # Import here to avoid circular imports
        from app.ui.export_video.export_video_widget import FloatingExportPanel

        # Check if the export panel is already open, close it if it is
        if hasattr(self, '_export_panel') and self._export_panel:
            self._export_panel.close()
            self._export_panel = None
        else:
            # Create and show the floating export panel
            self._export_panel = FloatingExportPanel(self.workspace, self.window)

            # Position the panel relative to the main window
            self._export_panel.update_position(self.window.geometry().topLeft(),
                                               self.window.geometry())

            # Show the panel
            self._export_panel.show()

    def _on_resolution_changed(self, index):
        """处理分辨率更改事件"""
        # 获取选中的分辨率
        resolution = self.resolution_combo.currentData()
        if resolution:
            width, height = resolution

            # 获取预览组件并设置新分辨率
            preview_widget = self.workspace.get_preview_widget()
            if preview_widget:
                preview_widget.set_preview_size(width, height)
            else:
                print("Preview widget not found")


class MainWindowBottomBar(BaseWidget):

    def __init__(self, workspace, parent):
        super(MainWindowBottomBar, self).__init__(workspace)
        self.setObjectName("main_window_bottom_bar")
        self.parent = parent
        self.setFixedHeight(28)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # close
        # self.setting_button = QPushButton("S", self)
        # self.setting_button.setObjectName("main_window_bottom_bar_button")
        # self.layout.addWidget(self.setting_button)


class MainWindowLeftBar(BaseWidget):

    def __init__(self, workspace, parent):
        super(MainWindowLeftBar, self).__init__(workspace)
        self.setObjectName("main_window_left_bar")
        self.parent = parent
        self.setFixedWidth(40)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        # buttons
        self.resource_button = QPushButton("\ue6b0", self)  # Play icon for resource
        self.resource_button.setFixedSize(30, 30)
        self.layout.addWidget(self.resource_button, alignment=Qt.AlignCenter)

        self.model_button = QPushButton("\ue66e", self)  # Text2Img icon
        self.model_button.setFixedSize(30, 30)
        self.layout.addWidget(self.model_button, alignment=Qt.AlignCenter)

        self.attach_button = QPushButton("\ue69d", self)  # Image edit icon
        self.attach_button.setFixedSize(30, 30)
        self.layout.addWidget(self.attach_button, alignment=Qt.AlignCenter)

        self.layout.addStretch(0)
        self.timeline_button = QPushButton("\ue6b2", self)  # Image to video icon
        self.timeline_button.setFixedSize(30, 30)
        self.layout.addWidget(self.timeline_button, alignment=Qt.AlignCenter)

        self.message_button = QPushButton("\ue707", self)  # Barrage icon for message
        self.message_button.setFixedSize(30, 30)
        self.layout.addWidget(self.message_button, alignment=Qt.AlignCenter)

        self.video_button = QPushButton("\ue6de", self)  # Image to video icon
        self.video_button.setFixedSize(30, 30)
        self.layout.addWidget(self.video_button, alignment=Qt.AlignCenter)

        self.camera_button = QPushButton("\ue6ce", self)  # Picture icon for camera
        self.camera_button.setFixedSize(30, 30)
        self.layout.addWidget(self.camera_button, alignment=Qt.AlignCenter)


class MainWindowRightBar(BaseWidget):

    def __init__(self, workspace: Workspace, parent):
        super(MainWindowRightBar, self).__init__(workspace)
        self.setObjectName("main_window_right_bar")
        self.parent = parent
        self.setFixedWidth(40)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setting_button = QPushButton("S", self)
        self.setting_button.setObjectName("main_window_bottom_bar_button")
        self.setting_button.setFixedSize(45, 30)
        self.layout.addWidget(self.setting_button)


class MainWindowWorkspaceTop(BaseWidget):

    def __init__(self, parent, workspace):
        super(MainWindowWorkspaceTop, self).__init__(workspace)
        self.setObjectName("main_window_workspace_top")
        self.parent = parent
        # 主布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.splitter = QSplitter(Qt.Horizontal)
        self.setObjectName("main_window_workspace_top_splitter")
        # Disable stretching on splitter to maintain fixed sizes
        self.splitter.setChildrenCollapsible(False)

        # Left panel - tool widgets
        self.v_splitter = QSplitter(Qt.Vertical)
        self.v_splitter.setChildrenCollapsible(False)
        self.left = TaskListWidget(self, workspace)
        self.left.setObjectName("main_window_workspace_top_left")
        self.left.setMinimumWidth(200)
        self.left.setMaximumWidth(200)
        self.splitter.addWidget(self.left)

        # Center panel - preview (this should expand)
        self.center: ToolEditorWidget = ToolEditorWidget(workspace)
        self.splitter.addWidget(self.center)

        self.right = LayersWidget(self, workspace)
        self.right.setObjectName("main_window_workspace_top_right")
        self.splitter.addWidget(self.right)

        # Set initial sizes and stretch factors
        # Left panel: 300px, Center: expand, Right panel: 300px
        self.splitter.setSizes([200, 1000, 200])
        self.splitter.setStretchFactor(0, 0)  # Left panel: don't stretch
        self.splitter.setStretchFactor(1, 1)  # Center panel: stretch
        self.splitter.setStretchFactor(2, 0)  # Right panel: don't stretch

        self.layout.addWidget(self.splitter)


class MainWindowWorkspaceBottom(BaseWidget):

    def __init__(self, parent, workspace: Workspace):
        super(MainWindowWorkspaceBottom, self).__init__(workspace)
        self.setObjectName("main_window_workspace_bottom")
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Create the timeline widget
        self.timeline = HorizontalTimeline(self, workspace)

        # Create subtitle timeline
        self.subtitle_timeline = SubtitleTimeline(workspace)

        # Create voiceover timeline
        self.voiceover_timeline = VoiceoverTimeline(workspace)

        # Wrap the timeline in a container that draws the cursor line
        self.timeline_container = TimelineContainer(self.timeline, self)
        self.timeline_container.set_subtitle_timeline(self.subtitle_timeline)
        self.timeline_container.set_voiceover_timeline(self.voiceover_timeline)

        # Set fixed height for timeline to prevent it from expanding
        self.setMinimumHeight(220)  # Increased to accommodate additional timelines
        self.setMaximumHeight(260)  # Increased to accommodate additional timelines

        # Add the container (which contains the timeline) to the layout
        self.layout.addWidget(self.timeline_container)


class MainWindowWorkspace(BaseWidget):

    def __init__(self, parent, workspace: Workspace):
        super(MainWindowWorkspace, self).__init__(workspace)
        self.setObjectName("main_window_workspace")
        self.parent = parent

        # 主布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setObjectName("main_window_workspace_splitter")
        self.splitter.setChildrenCollapsible(False)

        self.workspace_top = MainWindowWorkspaceTop(self, workspace)
        self.splitter.addWidget(self.workspace_top)

        self.workspace_bottom = MainWindowWorkspaceBottom(self, workspace)
        self.splitter.addWidget(self.workspace_bottom)

        # Set initial sizes and stretch factors
        # Top area should expand, bottom (timeline) should stay fixed
        self.splitter.setSizes([1200, 200])
        self.splitter.setStretchFactor(0, 1)  # Top: stretch
        self.splitter.setStretchFactor(1, 0)  # Bottom (timeline): don't stretch

        self.layout.addWidget(self.splitter)


class MainWindowHLayout(BaseWidget):

    def __init__(self, parent, workspace: Workspace):
        super(MainWindowHLayout, self).__init__(workspace)
        self.setObjectName("main_window_h_layout")
        self.parent = parent
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.left_bar = MainWindowLeftBar(workspace, self)
        layout.addWidget(self.left_bar)
        self.workspace = MainWindowWorkspace(self, workspace)
        layout.addWidget(self.workspace, 1)
        self.right_bar = MainWindowRightBar(workspace, self)
        layout.addWidget(self.right_bar)


# --- 主窗口 ---
class MainWindow(QMainWindow):

    def __init__(self, workspace: Workspace):
        super(MainWindow, self).__init__()
        self.setGeometry(100, 100, 1600, 900)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.workspace = workspace
        self.project = workspace.get_project()
        # 设置主窗口引用到 workspace，方便访问预览组件
        self.workspace._main_window = self
        central_widget = QWidget()
        central_widget.setObjectName("main_window")
        # 主布局
        layout = QVBoxLayout()
        layout.setObjectName("main_window_layout")
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.top_bar = MainWindowTopBar(self, self.workspace)
        self.top_bar.setObjectName("main_window_top_bar")
        layout.addWidget(self.top_bar)
        self.h_layout = MainWindowHLayout(self, workspace)
        layout.addWidget(self.h_layout, 1)
        self.bottom_bar = MainWindowBottomBar(workspace, self)
        self.bottom_bar.setObjectName("main_window_bottom_bar")
        layout.addWidget(self.bottom_bar)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def workspace(self):
        return self.workspace

    def project(self):
        return self.project



