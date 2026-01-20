"""Agent chat plan widget for showing active execution plan."""

from typing import Dict, Optional, Tuple, List
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QFont, QPen

from app.ui.base_widget import BaseWidget
from app.ui.components.avatar_widget import AvatarWidget
from agent.plan.service import PlanService
from agent.plan.models import Plan, PlanInstance, PlanStatus, PlanTask, TaskStatus
from agent.crew.crew_service import CrewService
from utils.i18n_utils import tr


class ClickableFrame(QFrame):
    """Frame that emits clicked signal on mouse press."""

    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class StatusIconWidget(QWidget):
    """Small circular status icon with text."""

    def __init__(self, text: str, color: str, size: int = 14, parent=None):
        super().__init__(parent)
        self._text = text
        self._color = QColor(color)
        self._size = size
        self.setFixedSize(size, size)

    def set_style(self, text: str, color: str):
        self._text = text
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.setBrush(self._color)
        painter.setPen(QPen(self._color))
        painter.drawEllipse(rect)

        font = QFont()
        font.setPointSize(max(7, self._size // 2))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(rect, Qt.AlignCenter, self._text)


class StatusCountWidget(QWidget):
    """Status icon with numeric count."""

    def __init__(self, label: str, color: str, tooltip: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.icon = StatusIconWidget(label, color, size=12, parent=self)
        layout.addWidget(self.icon)

        self.count_label = QLabel("0", self)
        self.count_label.setStyleSheet("color: #d0d0d0; font-size: 12px;")
        layout.addWidget(self.count_label)

        self.setToolTip(tooltip)

    def set_count(self, value: int):
        self.count_label.setText(str(value))


class PlanTaskRow(QFrame):
    """Row widget for a single plan task."""

    def __init__(
        self,
        task: PlanTask,
        crew_member,
        status_label: str,
        status_color: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("plan_task_row")
        self.setStyleSheet("""
            QFrame#plan_task_row {
                background-color: #2b2d30;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        status_icon = StatusIconWidget(status_label, status_color, size=14, parent=self)
        top_row.addWidget(status_icon, 0, Qt.AlignVCenter)

        task_text = task.name or task.description or tr("Untitled Task")
        task_label = QLabel(task_text, self)
        task_label.setStyleSheet("color: #e1e1e1; font-size: 12px;")
        task_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        task_label.setToolTip(task.description or task_text)
        top_row.addWidget(task_label, 1)
        layout.addLayout(top_row)

        crew_row = QHBoxLayout()
        crew_row.setContentsMargins(0, 0, 0, 0)
        crew_row.setSpacing(6)

        if crew_member:
            avatar_icon = crew_member.config.icon
            avatar_color = crew_member.config.color
            crew_name = crew_member.config.name
        else:
            avatar_icon = "A"
            avatar_color = "#5c5f66"
            crew_name = task.agent_role or tr("Unknown")

        avatar = AvatarWidget(icon=avatar_icon, color=avatar_color, size=16, shape="rounded_rect", parent=self)
        crew_row.addWidget(avatar, 0, Qt.AlignVCenter)

        crew_label = QLabel(crew_name, self)
        crew_label.setStyleSheet("color: #b0b0b0; font-size: 11px;")
        crew_row.addWidget(crew_label, 0, Qt.AlignVCenter)
        crew_row.addStretch()
        layout.addLayout(crew_row)


class AgentChatPlanWidget(BaseWidget):
    """Plan widget embedded in agent chat."""

    def __init__(self, workspace, parent=None):
        super().__init__(workspace)
        if parent:
            self.setParent(parent)

        self.plan_service = PlanService()
        self.plan_service.set_workspace(workspace)
        self.crew_service = CrewService()

        self._crew_member_metadata: Dict[str, object] = {}
        self._preferred_plan_id: Optional[str] = None
        self._current_plan_id: Optional[str] = None
        self._is_expanded = False
        self._details_max_height = 220

        self._setup_ui()
        self._load_crew_member_metadata()
        self.refresh_plan()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(2000)
        self._refresh_timer.timeout.connect(self.refresh_plan)
        self._refresh_timer.start()

    def _setup_ui(self):
        self.setObjectName("agent_chat_plan_widget")
        self.setStyleSheet("""
            QWidget#agent_chat_plan_widget {
                background-color: transparent;
            }
            QFrame#plan_container {
                background-color: #2b2d30;
                border-radius: 6px;
            }
            QFrame#plan_header {
                background-color: #2b2d30;
            }
            QLabel#plan_summary {
                color: #e1e1e1;
                font-size: 13px;
            }
            QLabel#plan_toggle {
                color: #b0b0b0;
                font-size: 13px;
            }
            QScrollArea#plan_details_scroll {
                background-color: #252525;
                border: none;
            }
            QWidget#plan_details_container {
                background-color: #252525;
            }
            QScrollBar:vertical {
                background-color: #2b2d30;
                width: 8px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #505254;
                min-height: 20px;
                border-radius: 4px;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.container = QFrame(self)
        self.container.setObjectName("plan_container")
        outer_layout.addWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.header_frame = ClickableFrame(self.container)
        self.header_frame.setObjectName("plan_header")
        self.header_frame.setCursor(Qt.PointingHandCursor)
        self.header_frame.clicked.connect(self.toggle_expanded)

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.plan_icon = AvatarWidget(icon="P", color="#4080ff", size=20, shape="circle", parent=self.header_frame)
        header_layout.addWidget(self.plan_icon, 0, Qt.AlignVCenter)

        self.summary_label = QLabel(tr("No active plan"), self.header_frame)
        self.summary_label.setObjectName("plan_summary")
        self.summary_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_layout.addWidget(self.summary_label, 1)

        self.status_container = QWidget(self.header_frame)
        status_layout = QHBoxLayout(self.status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(6)

        self.running_count = StatusCountWidget("R", "#f4c542", tr("Running"), parent=self.status_container)
        self.waiting_count = StatusCountWidget("W", "#3498db", tr("Waiting"), parent=self.status_container)
        self.success_count = StatusCountWidget("S", "#2ecc71", tr("Success"), parent=self.status_container)
        self.failed_count = StatusCountWidget("F", "#e74c3c", tr("Failed"), parent=self.status_container)

        status_layout.addWidget(self.running_count)
        status_layout.addWidget(self.waiting_count)
        status_layout.addWidget(self.success_count)
        status_layout.addWidget(self.failed_count)

        header_layout.addWidget(self.status_container, 0, Qt.AlignVCenter)

        self.toggle_label = QLabel(">", self.header_frame)
        self.toggle_label.setObjectName("plan_toggle")
        header_layout.addWidget(self.toggle_label, 0, Qt.AlignVCenter)

        layout.addWidget(self.header_frame)

        self.details_scroll = QScrollArea(self.container)
        self.details_scroll.setObjectName("plan_details_scroll")
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.details_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.details_scroll.setMaximumHeight(self._details_max_height)

        self.details_container = QWidget()
        self.details_container.setObjectName("plan_details_container")
        self.details_layout = QVBoxLayout(self.details_container)
        self.details_layout.setContentsMargins(6, 6, 6, 6)
        self.details_layout.setSpacing(6)

        self.empty_label = QLabel(tr("No tasks available"), self.details_container)
        self.empty_label.setStyleSheet("color: #9a9a9a; font-size: 12px;")
        self.details_layout.addWidget(self.empty_label)

        self.details_scroll.setWidget(self.details_container)
        self.details_scroll.setVisible(False)
        layout.addWidget(self.details_scroll)

    def on_project_switched(self, project_name: str):
        self._preferred_plan_id = None
        self._current_plan_id = None
        self._load_crew_member_metadata()
        self.refresh_plan()

    def toggle_expanded(self):
        self._is_expanded = not self._is_expanded
        self.details_scroll.setVisible(self._is_expanded)
        self.toggle_label.setText("v" if self._is_expanded else ">")

        # If this widget is inside a splitter, adjust the height accordingly
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == 'QSplitter':
                # Get the index of this widget in the splitter
                index = parent.indexOf(self)
                if index != -1:
                    sizes = parent.sizes()
                    if self._is_expanded:
                        # Restore previous size or use a default expanded size
                        sizes[index] = self._details_max_height + 80  # Header height + details height
                    else:
                        # Minimize to just the header
                        sizes[index] = 40  # Just enough for the header
                    parent.setSizes(sizes)
                break
            parent = parent.parent()

        self.updateGeometry()

    def handle_stream_event(self, event, _session=None):
        if not event:
            return
        if event.event_type == "plan_update":
            plan_id = event.data.get("plan_id") if event.data else None
            if plan_id:
                self._preferred_plan_id = plan_id
            self.refresh_plan()

    def refresh_plan(self):
        project_name = self._get_project_name()
        if not project_name:
            self._set_no_plan()
            return

        plan, instance = self._resolve_active_plan(project_name)
        self._update_summary(plan, instance)
        self._update_task_list(plan, instance)

    def _get_project_name(self) -> Optional[str]:
        project = self.workspace.get_project() if self.workspace else None
        if not project:
            return None
        if hasattr(project, "project_name"):
            return project.project_name
        if hasattr(project, "name"):
            return project.name
        if isinstance(project, str):
            return project
        return None

    def _resolve_active_plan(self, project_name: str) -> Tuple[Optional[Plan], Optional[PlanInstance]]:
        active_statuses = {PlanStatus.RUNNING, PlanStatus.CREATED, PlanStatus.PAUSED}

        if self._preferred_plan_id:
            plan = self.plan_service.load_plan(project_name, self._preferred_plan_id)
            if plan:
                instance = self._load_latest_instance(project_name, plan.id)
                if instance and instance.status in active_statuses:
                    return plan, instance
                return plan, instance

        candidates: List[Tuple[Plan, PlanInstance]] = []
        plans = self.plan_service.get_all_plans_for_project(project_name)
        for plan in plans:
            instance = self._load_latest_instance(project_name, plan.id)
            if instance and instance.status in active_statuses:
                candidates.append((plan, instance))

        if not candidates:
            return None, None

        return max(candidates, key=lambda item: self._instance_sort_key(item[1]))

    def _load_latest_instance(self, project_name: str, plan_id: str) -> Optional[PlanInstance]:
        instances = self.plan_service.get_all_instances_for_plan(project_name, plan_id)
        if not instances:
            return None
        return max(instances, key=self._instance_sort_key)

    def _instance_sort_key(self, instance: PlanInstance) -> datetime:
        return instance.started_at or instance.created_at or datetime.min

    def _update_summary(self, plan: Optional[Plan], instance: Optional[PlanInstance]):
        if not plan:
            self.summary_label.setText(tr("No active plan"))
            self.summary_label.setToolTip("")
            self._set_counts(0, 0, 0, 0)
            return

        tasks = instance.tasks if instance else plan.tasks
        running, waiting, success, failed = self._count_task_status(tasks)
        self._set_counts(running, waiting, success, failed)

        summary_text = self._build_summary_text(plan, tasks)
        self.summary_label.setText(summary_text)
        self.summary_label.setToolTip(plan.description or summary_text)

    def _build_summary_text(self, plan: Plan, tasks: List[PlanTask]) -> str:
        running = [t for t in tasks if t.status == TaskStatus.RUNNING]
        waiting = [t for t in tasks if t.status in {TaskStatus.CREATED, TaskStatus.READY}]
        if running:
            task_text = running[0].name or running[0].description or tr("Running task")
            return f"{tr('Running')}: {self._truncate_text(task_text, 80)}"
        if waiting:
            task_text = waiting[0].name or waiting[0].description or tr("Waiting task")
            return f"{tr('Waiting')}: {self._truncate_text(task_text, 80)}"
        if plan.name:
            return self._truncate_text(plan.name, 80)
        if plan.description:
            return self._truncate_text(plan.description, 80)
        return tr("Plan in progress")

    def _truncate_text(self, text: str, limit: int) -> str:
        if text is None:
            return ""
        cleaned = text.strip()
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[: max(0, limit - 3)].rstrip() + "..."

    def _count_task_status(self, tasks: List[PlanTask]) -> Tuple[int, int, int, int]:
        running = 0
        waiting = 0
        success = 0
        failed = 0
        for task in tasks:
            if task.status == TaskStatus.RUNNING:
                running += 1
            elif task.status in {TaskStatus.CREATED, TaskStatus.READY}:
                waiting += 1
            elif task.status == TaskStatus.COMPLETED:
                success += 1
            elif task.status in {TaskStatus.FAILED, TaskStatus.CANCELLED}:
                failed += 1
        return running, waiting, success, failed

    def _set_counts(self, running: int, waiting: int, success: int, failed: int):
        self.running_count.set_count(running)
        self.waiting_count.set_count(waiting)
        self.success_count.set_count(success)
        self.failed_count.set_count(failed)

    def _update_task_list(self, plan: Optional[Plan], instance: Optional[PlanInstance]):
        self._clear_layout(self.details_layout)

        tasks = []
        if instance:
            tasks = instance.tasks
        elif plan:
            tasks = plan.tasks

        if not tasks:
            self.empty_label = QLabel(tr("No tasks available"), self.details_container)
            self.empty_label.setStyleSheet("color: #9a9a9a; font-size: 12px;")
            self.details_layout.addWidget(self.empty_label)
            self._update_details_height()
            return

        for task in tasks:
            status_label, status_color = self._status_style(task.status)
            crew_member = self._find_crew_member(task.agent_role)
            row = PlanTaskRow(task, crew_member, status_label, status_color, parent=self.details_container)
            self.details_layout.addWidget(row)

        self.details_layout.addStretch()
        self._update_details_height()

    def _status_style(self, status: TaskStatus) -> Tuple[str, str]:
        if status == TaskStatus.RUNNING:
            return "R", "#f4c542"
        if status in {TaskStatus.CREATED, TaskStatus.READY}:
            return "W", "#3498db"
        if status == TaskStatus.COMPLETED:
            return "S", "#2ecc71"
        return "F", "#e74c3c"

    def _clear_layout(self, layout: QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def _set_no_plan(self):
        self.summary_label.setText(tr("No active plan"))
        self.summary_label.setToolTip("")
        self._set_counts(0, 0, 0, 0)
        self._update_task_list(None, None)

    def _load_crew_member_metadata(self):
        try:
            project = self.workspace.get_project() if self.workspace else None
            if not project:
                self._crew_member_metadata = {}
                return

            crew_members = self.crew_service.get_project_crew_members(project)
            self._crew_member_metadata = {}
            for name, crew_member in crew_members.items():
                if not crew_member or not crew_member.config:
                    continue
                self._crew_member_metadata[name.lower()] = crew_member
                crew_title = crew_member.config.metadata.get("crew_title") if crew_member.config.metadata else None
                if crew_title:
                    self._crew_member_metadata[crew_title.lower()] = crew_member
        except Exception:
            self._crew_member_metadata = {}

    def _find_crew_member(self, agent_role: Optional[str]):
        if not agent_role:
            return None
        if not self._crew_member_metadata:
            self._load_crew_member_metadata()
        return self._crew_member_metadata.get(agent_role.lower())

    def _update_details_height(self):
        if not self.details_scroll:
            return
        content_height = self.details_container.sizeHint().height()
        target_height = min(self._details_max_height, max(0, content_height))
        self.details_scroll.setFixedHeight(target_height)
