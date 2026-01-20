"""
Plan Panel for displaying PlanService data.

This panel shows plans, their instances, and task execution status.
"""
from typing import Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QTextEdit, QStackedWidget, QHeaderView
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from app.ui.panels.base_panel import BasePanel
from app.data.workspace import Workspace
from agent.plan.service import PlanService
from agent.plan.models import Plan, PlanInstance, TaskStatus


class PlanPanel(BasePanel):
    """Panel for displaying and managing plans and their execution status."""

    def __init__(self, workspace: Workspace, parent=None):
        """
        Initialize the plan panel.

        Args:
            workspace: Workspace instance for data access
            parent: Optional parent widget
        """
        super().__init__(workspace, parent)

        self.plan_service = PlanService()
        # Set the workspace to ensure proper plan storage location
        self.plan_service.set_workspace(workspace)
        self.current_project_name = workspace.get_project().project_name if workspace.get_project() else None

        # Store selected plan and instance for detail view
        self.selected_plan: Optional[Plan] = None
        self.selected_instance: Optional[PlanInstance] = None

    def load_data(self):
        """Load data for the panel - called by BasePanel when panel is activated."""
        # Update the current project name to ensure we have the latest
        if self.workspace and self.workspace.get_project():
            self.current_project_name = self.workspace.get_project().project_name
        self.refresh_data()

    def setup_ui(self):
        """Set up the user interface."""
        self.set_panel_title("Plan")

        content_container = QWidget()
        layout = QVBoxLayout(content_container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.view_stack = QStackedWidget()
        layout.addWidget(self.view_stack, 1)

        # List view for plans and instances
        self.list_view = QWidget()
        list_layout = QVBoxLayout(self.list_view)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(6)

        plan_list_title = QLabel("Plans")
        plan_list_title.setFont(QFont("Arial", 10, QFont.Bold))
        list_layout.addWidget(plan_list_title)

        self.plan_tree = QTreeWidget()
        self.plan_tree.setHeaderHidden(True)
        self.plan_tree.setIndentation(12)
        self.plan_tree.itemSelectionChanged.connect(self._on_plan_selected)
        list_layout.addWidget(self.plan_tree, 1)

        self.empty_label = QLabel("No plans available")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setObjectName("empty_label")
        list_layout.addWidget(self.empty_label)

        self.view_stack.addWidget(self.list_view)

        # Details view for selected plan/instance
        self.details_view = QWidget()
        details_layout = QVBoxLayout(self.details_view)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(6)

        details_header_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self._show_list_view)
        details_header_layout.addWidget(self.back_button)

        self.details_title = QLabel("Plan Details")
        self.details_title.setFont(QFont("Arial", 10, QFont.Bold))
        details_header_layout.addWidget(self.details_title)
        details_header_layout.addStretch()
        details_layout.addLayout(details_header_layout)

        self.plan_info_text = QTextEdit()
        self.plan_info_text.setReadOnly(True)
        details_layout.addWidget(self.plan_info_text)

        task_list_title = QLabel("Tasks")
        task_list_title.setFont(QFont("Arial", 10, QFont.Bold))
        details_layout.addWidget(task_list_title)

        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderLabels(["Task", "Status"])
        self.task_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.task_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        details_layout.addWidget(self.task_tree, 1)

        self.view_stack.addWidget(self.details_view)
        self.view_stack.setCurrentWidget(self.list_view)

        # Control buttons
        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_data)
        button_layout.addWidget(self.refresh_button)

        self.execute_button = QPushButton("Execute")
        self.execute_button.clicked.connect(self._execute_selected_plan)
        self.execute_button.setEnabled(False)
        button_layout.addWidget(self.execute_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.content_layout.addWidget(content_container)

    def refresh_data(self):
        """Refresh the displayed data from the PlanService."""
        # Update the current project name in case it has changed
        if self.workspace and self.workspace.get_project():
            self.current_project_name = self.workspace.get_project().project_name
        else:
            # Clear the tree if no project is loaded
            self.plan_tree.clear()
            self._set_empty_state(True)
            self._clear_details()
            return

        if not self.current_project_name:
            # Clear the tree if no project name is available
            self.plan_tree.clear()
            self._set_empty_state(True)
            self._clear_details()
            return

        # Clear existing items
        self.plan_tree.clear()
        self.selected_plan = None
        self.selected_instance = None
        self.execute_button.setEnabled(False)
        self._clear_details()

        # Load all plans for the current project
        plans = self.plan_service.get_all_plans_for_project(self.current_project_name)

        if not plans:
            self._set_empty_state(True)
            self._show_list_view()
            return

        self._set_empty_state(False)

        for plan in plans:
            # Create top-level item for the plan
            plan_item = QTreeWidgetItem(self.plan_tree)
            plan_name = plan.name or "Untitled Plan"
            plan_item.setText(0, f"{plan_name} ({plan.status.value.title()})")

            # Store plan ID in the item for later reference
            plan_item.setData(0, Qt.UserRole, ("plan", plan.id))

            # Add instances as child items
            instances = self.plan_service.get_all_instances_for_plan(self.current_project_name, plan.id)
            for instance in instances:
                instance_item = QTreeWidgetItem(plan_item)
                instance_item.setText(
                    0,
                    f"Instance {instance.instance_id[-8:]} ({instance.status.value.title()})"
                )

                # Store instance ID in the item for later reference
                instance_item.setData(0, Qt.UserRole, ("instance", plan.id, instance.instance_id))

                # Instance tooltip with key timestamps
                instance_tooltip = (
                    f"Created: {self._format_datetime(instance.created_at)}\n"
                    f"Started: {self._format_datetime(instance.started_at)}\n"
                    f"Completed: {self._format_datetime(instance.completed_at)}"
                )
                instance_item.setToolTip(0, instance_tooltip)

            # Plan tooltip with summary
            plan_tooltip = (
                f"Created: {self._format_datetime(plan.created_at)}\n"
                f"Tasks: {len(plan.tasks)}\n"
                f"Instances: {len(instances)}"
            )
            plan_item.setToolTip(0, plan_tooltip)
            plan_item.setExpanded(True)

        self._show_list_view()

    def _set_empty_state(self, is_empty: bool):
        """Show or hide the empty state for the list view."""
        self.plan_tree.setVisible(not is_empty)
        self.empty_label.setVisible(is_empty)

    def _clear_details(self):
        """Clear details view content."""
        if hasattr(self, "plan_info_text"):
            self.plan_info_text.clear()
        if hasattr(self, "task_tree"):
            self.task_tree.clear()
        if hasattr(self, "details_title"):
            self.details_title.setText("Plan Details")

    def _format_datetime(self, value: Optional[datetime]) -> str:
        """Format datetime for display."""
        return value.strftime("%Y-%m-%d %H:%M") if value else "N/A"

    def _get_latest_instance(self, plan_id: str) -> Optional[PlanInstance]:
        """Get the latest instance for a plan."""
        instances = self.plan_service.get_all_instances_for_plan(self.current_project_name, plan_id)
        if not instances:
            return None
        return max(instances, key=lambda item: item.created_at or datetime.min)

    def _show_list_view(self, _checked: bool = False):
        """Switch to list view."""
        self.view_stack.setCurrentWidget(self.list_view)
        self.plan_tree.clearSelection()

    def _show_details_view(self):
        """Switch to details view."""
        self.view_stack.setCurrentWidget(self.details_view)

    def _on_plan_selected(self):
        """Handle plan selection in the tree."""
        selected_items = self.plan_tree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        item_data = item.data(0, Qt.UserRole)
        self.selected_plan = None
        self.selected_instance = None

        if isinstance(item_data, tuple) and item_data:
            item_type = item_data[0]
            if item_type == "plan" and len(item_data) >= 2:
                plan_id = item_data[1]
                self.selected_plan = self.plan_service.load_plan(self.current_project_name, plan_id)
                self.selected_instance = self._get_latest_instance(plan_id)
            elif item_type == "instance" and len(item_data) >= 3:
                plan_id = item_data[1]
                instance_id = item_data[2]
                self.selected_plan = self.plan_service.load_plan(self.current_project_name, plan_id)
                self.selected_instance = self.plan_service.load_plan_instance(
                    self.current_project_name,
                    plan_id,
                    instance_id,
                )
        else:
            # Backward-compatible handling if item stores only IDs
            plan_id = item_data
            parent_item = item.parent()
            if parent_item:
                parent_id = parent_item.data(0, Qt.UserRole)
                self.selected_plan = self.plan_service.load_plan(self.current_project_name, parent_id)
                self.selected_instance = self.plan_service.load_plan_instance(
                    self.current_project_name,
                    parent_id,
                    plan_id,
                )
            else:
                self.selected_plan = self.plan_service.load_plan(self.current_project_name, plan_id)
                self.selected_instance = self._get_latest_instance(plan_id)

        self._update_details_view()
        self._show_details_view()

    def _update_details_view(self):
        """Update the details view based on selected plan/instance."""
        if not self.selected_plan:
            self._clear_details()
            self.execute_button.setEnabled(False)
            return

        self.execute_button.setEnabled(True)

        plan_name = self.selected_plan.name or "Untitled Plan"
        self.details_title.setText(f"Plan: {plan_name}")

        description = self.selected_plan.description or "No description"
        info_lines = [
            f"Name: {plan_name}",
            f"Description: {description}",
            f"Status: {self.selected_plan.status.value.title()}",
            f"Created: {self._format_datetime(self.selected_plan.created_at)}",
        ]

        if self.selected_instance:
            info_lines.extend([
                "",
                f"Instance ID: {self.selected_instance.instance_id}",
                f"Instance Status: {self.selected_instance.status.value.title()}",
                f"Started: {self._format_datetime(self.selected_instance.started_at)}",
                f"Completed: {self._format_datetime(self.selected_instance.completed_at)}",
            ])

        self.plan_info_text.setPlainText("\n".join(info_lines))

        # Update task list
        self.task_tree.clear()

        # Use tasks from the instance if available, otherwise from the plan
        tasks = self.selected_instance.tasks if self.selected_instance else self.selected_plan.tasks

        if not tasks:
            empty_item = QTreeWidgetItem(self.task_tree)
            empty_item.setText(0, "No tasks available")
            empty_item.setFlags(Qt.ItemIsEnabled)
            return

        for task in tasks:
            task_item = QTreeWidgetItem(self.task_tree)
            task_name = task.name or "Untitled Task"
            task_item.setText(0, task_name)
            task_item.setText(1, task.status.value.title())

            # Tooltip with extra details for narrow view
            started_str = self._format_datetime(task.started_at)
            completed_str = self._format_datetime(task.completed_at)
            tooltip_lines = [
                f"Description: {task.description or 'No description'}",
                f"Agent Role: {task.agent_role or 'N/A'}",
                f"Started: {started_str}",
                f"Completed: {completed_str}",
            ]
            if task.error_message:
                tooltip_lines.append(f"Error: {task.error_message}")
            tooltip_text = "\n".join(tooltip_lines)
            task_item.setToolTip(0, tooltip_text)
            task_item.setToolTip(1, tooltip_text)

            # Color code based on status
            if task.status == TaskStatus.COMPLETED:
                for col in range(self.task_tree.columnCount()):
                    task_item.setBackground(col, Qt.green)
            elif task.status == TaskStatus.FAILED:
                for col in range(self.task_tree.columnCount()):
                    task_item.setBackground(col, Qt.red)
            elif task.status == TaskStatus.RUNNING:
                for col in range(self.task_tree.columnCount()):
                    task_item.setBackground(col, Qt.yellow)
            elif task.status == TaskStatus.READY:
                for col in range(self.task_tree.columnCount()):
                    task_item.setBackground(col, Qt.blue)

    def _execute_selected_plan(self):
        """Execute the currently selected plan."""
        if not self.selected_plan:
            return

        # Create a new instance of the plan and start execution
        plan_instance = self.plan_service.create_plan_instance(self.selected_plan)
        self.plan_service.start_plan_execution(plan_instance)
        
        # Refresh the data to show the new instance
        self.refresh_data()

    def on_activated(self):
        """Called when the panel becomes active."""
        # Update the current project name to ensure we have the latest
        if self.workspace and self.workspace.get_project():
            self.current_project_name = self.workspace.get_project().project_name
        super().on_activated()
        # The parent class will call load_data() which refreshes the data

    def on_project_switched(self, project_name: str):
        """Called when the project is switched."""
        # Update the current project name
        self.current_project_name = project_name
        # Refresh data for the new project
        self.refresh_data()

    def sizeHint(self):
        """Return recommended size for the panel."""
        return QSize(320, 600)