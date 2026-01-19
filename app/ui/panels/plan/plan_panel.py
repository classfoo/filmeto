"""
Plan Panel for displaying PlanService data.

This panel shows plans, their instances, and task execution status.
"""
from typing import Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QTextEdit, QSplitter, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from app.ui.panels.base_panel import BasePanel
from app.data.workspace import Workspace
from agent.plan.service import PlanService
from agent.plan.models import Plan, PlanInstance, PlanTask, PlanStatus, TaskStatus


class PlanPanel(BasePanel):
    """Panel for displaying and managing plans and their execution status."""

    def __init__(self, workspace: Workspace, parent=None):
        """
        Initialize the plan panel.

        Args:
            workspace: Workspace instance for data access
            parent: Optional parent widget
        """
        super().__init__(workspace)
        if parent:
            self.setParent(parent)

        self.plan_service = PlanService()
        self.current_project_id = workspace.current_project.id if workspace.current_project else None
        
        # Store selected plan and instance for detail view
        self.selected_plan: Optional[Plan] = None
        self.selected_instance: Optional[PlanInstance] = None

        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header
        header_label = QLabel("Plan Management")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(header_label)

        # Create splitter for plan list and details
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Plan list
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Plan list title
        plan_list_title = QLabel("Plans")
        plan_list_title.setFont(QFont("Arial", 10, QFont.Bold))
        left_layout.addWidget(plan_list_title)
        
        # Plan list tree
        self.plan_tree = QTreeWidget()
        self.plan_tree.setHeaderLabels(["Plan", "Status", "Created"])
        self.plan_tree.header().setSectionResizeMode(0, self.plan_tree.header().Stretch)
        self.plan_tree.header().setSectionResizeMode(1, self.plan_tree.header().ResizeToContents)
        self.plan_tree.header().setSectionResizeMode(2, self.plan_tree.header().ResizeToContents)
        self.plan_tree.itemSelectionChanged.connect(self._on_plan_selected)
        left_layout.addWidget(self.plan_tree)
        
        # Right side: Plan details
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Plan details title
        details_title = QLabel("Plan Details")
        details_title.setFont(QFont("Arial", 10, QFont.Bold))
        right_layout.addWidget(details_title)
        
        # Plan info section
        self.plan_info_text = QTextEdit()
        self.plan_info_text.setReadOnly(True)
        right_layout.addWidget(self.plan_info_text)
        
        # Task list section
        task_list_title = QLabel("Tasks")
        task_list_title.setFont(QFont("Arial", 10, QFont.Bold))
        right_layout.addWidget(task_list_title)
        
        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderLabels(["Task", "Status", "Agent Role", "Started", "Completed"])
        self.task_tree.header().setSectionResizeMode(0, self.task_tree.header().Stretch)
        self.task_tree.header().setSectionResizeMode(1, self.task_tree.header().ResizeToContents)
        self.task_tree.header().setSectionResizeMode(2, self.task_tree.header().ResizeToContents)
        self.task_tree.header().setSectionResizeMode(3, self.task_tree.header().ResizeToContents)
        self.task_tree.header().setSectionResizeMode(4, self.task_tree.header().ResizeToContents)
        right_layout.addWidget(self.task_tree)
        
        # Add frames to splitter
        self.splitter.addWidget(left_frame)
        self.splitter.addWidget(right_frame)
        self.splitter.setSizes([300, 400])  # Default sizes
        
        layout.addWidget(self.splitter)

        # Control buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_data)
        button_layout.addWidget(self.refresh_button)
        
        self.execute_button = QPushButton("Execute Selected Plan")
        self.execute_button.clicked.connect(self._execute_selected_plan)
        button_layout.addWidget(self.execute_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def refresh_data(self):
        """Refresh the displayed data from the PlanService."""
        if not self.current_project_id:
            return
            
        # Clear existing items
        self.plan_tree.clear()
        
        # Load all plans for the current project
        plans = self.plan_service.get_all_plans_for_project(self.current_project_id)
        
        for plan in plans:
            # Create top-level item for the plan
            plan_item = QTreeWidgetItem(self.plan_tree)
            plan_item.setText(0, plan.name)
            plan_item.setText(1, plan.status.value.title())
            
            # Format creation date
            created_str = plan.created_at.strftime("%Y-%m-%d %H:%M") if plan.created_at else "N/A"
            plan_item.setText(2, created_str)
            
            # Store plan ID in the item for later reference
            plan_item.setData(0, Qt.UserRole, plan.id)
            
            # Add instances as child items
            instances = self.plan_service.get_all_instances_for_plan(self.current_project_id, plan.id)
            for instance in instances:
                instance_item = QTreeWidgetItem(plan_item)
                instance_item.setText(0, f"Instance: {instance.instance_id[-8:]}")  # Show last 8 chars of ID
                instance_item.setText(1, instance.status.value.title())
                
                # Format creation date
                created_str = instance.created_at.strftime("%Y-%m-%d %H:%M") if instance.created_at else "N/A"
                instance_item.setText(2, created_str)
                
                # Store instance ID in the item for later reference
                instance_item.setData(0, Qt.UserRole, instance.instance_id)

    def _on_plan_selected(self):
        """Handle plan selection in the tree."""
        selected_items = self.plan_tree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        plan_id = item.data(0, Qt.UserRole)
        
        # Check if this is a plan or an instance
        parent_item = item.parent()
        if parent_item:  # This is an instance
            # Get the plan ID from the parent
            self.selected_plan = self.plan_service.load_plan(self.current_project_id, parent_item.data(0, Qt.UserRole))
            self.selected_instance = self.plan_service.load_plan_instance(
                self.current_project_id, 
                parent_item.data(0, Qt.UserRole), 
                plan_id
            )
        else:  # This is a plan
            self.selected_plan = self.plan_service.load_plan(self.current_project_id, plan_id)
            # For now, just show the first instance if available
            instances = self.plan_service.get_all_instances_for_plan(self.current_project_id, plan_id)
            if instances:
                self.selected_instance = instances[0]
            else:
                self.selected_instance = None

        self._update_details_view()

    def _update_details_view(self):
        """Update the details view based on selected plan/instance."""
        if not self.selected_plan:
            self.plan_info_text.clear()
            self.task_tree.clear()
            return

        # Update plan info
        info_text = f"<h3>{self.selected_plan.name}</h3>"
        info_text += f"<p><b>Description:</b> {self.selected_plan.description}</p>"
        info_text += f"<p><b>Status:</b> {self.selected_plan.status.value.title()}</p>"
        info_text += f"<p><b>Created:</b> {self.selected_plan.created_at.strftime('%Y-%m-%d %H:%M') if self.selected_plan.created_at else 'N/A'}</p>"
        
        if self.selected_instance:
            info_text += f"<p><b>Instance ID:</b> {self.selected_instance.instance_id}</p>"
            info_text += f"<p><b>Instance Status:</b> {self.selected_instance.status.value.title()}</p>"
            info_text += f"<p><b>Started:</b> {self.selected_instance.started_at.strftime('%Y-%m-%d %H:%M') if self.selected_instance.started_at else 'N/A'}</p>"
            info_text += f"<p><b>Completed:</b> {self.selected_instance.completed_at.strftime('%Y-%m-%d %H:%M') if self.selected_instance.completed_at else 'N/A'}</p>"
        
        self.plan_info_text.setHtml(info_text)

        # Update task list
        self.task_tree.clear()
        
        # Use tasks from the instance if available, otherwise from the plan
        tasks = self.selected_instance.tasks if self.selected_instance else self.selected_plan.tasks
        
        for task in tasks:
            task_item = QTreeWidgetItem(self.task_tree)
            task_item.setText(0, task.name)
            task_item.setText(1, task.status.value.title())
            task_item.setText(2, task.agent_role)
            
            # Format start and completion times
            started_str = task.started_at.strftime("%Y-%m-%d %H:%M") if task.started_at else "N/A"
            completed_str = task.completed_at.strftime("%Y-%m-%d %H:%M") if task.completed_at else "N/A"
            
            task_item.setText(3, started_str)
            task_item.setText(4, completed_str)
            
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
        super().on_activated()
        # Refresh data when panel is activated
        self.refresh_data()

    def sizeHint(self):
        """Return recommended size for the panel."""
        return QSize(800, 600)