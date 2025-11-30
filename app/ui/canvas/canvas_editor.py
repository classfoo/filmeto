"""
Canvas Editor Component
This module implements a canvas editor with a left toolbar and right canvas area using PySide6.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QSizePolicy, QLabel)

from app.ui.base_widget import BaseWidget
from app.ui.canvas.canvas import CanvasWidget
from app.data.workspace import Workspace
from app.data.timeline import TimelineItem
from app.data.task import TaskResult


class CanvasEditor(BaseWidget):
    """
    Main canvas editor component with left toolbar and right canvas.
    Left panel: Top section (tools/properties) + Bottom section (layers)
    Right panel: Canvas
    """
    
    def __init__(self, workspace: Workspace):
        super().__init__(workspace)
        try:
            self.setWindowTitle("Canvas Editor")
            self.timeline_item = workspace.get_current_timeline_item()
            
            # Initialize canvas widget - will be sized based on parent when added to layout
            # 使用默认尺寸，让CanvasWidget自适应父容器
            self.canvas_widget = CanvasWidget(workspace)

            # Make the canvas widget expand to fill available space in the layout
            self.canvas_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            # Create layout
            main_layout = QHBoxLayout(self)
            main_layout.setContentsMargins(0, 0, 0, 0)
            
            # Create left panel with vertical layout for tools on top and layers on bottom (fixed 160px width)
            left_panel = QWidget()
            left_panel.setFixedWidth(160)  # Fixed width of 160px
            left_layout = QVBoxLayout(left_panel)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(0)
            # Tool panel container at top
            self.tool_panel_container = QWidget(left_panel)
            self.tool_panel_layout = QVBoxLayout(self.tool_panel_container)
            self.tool_panel_layout.setContentsMargins(8, 8, 8, 8)
            self.tool_panel_layout.setSpacing(6)
            # Placeholder label when no tool is selected
            placeholder = QLabel("No Tool Config")
            self.tool_panel_layout.addWidget(placeholder)
            left_layout.addWidget(self.tool_panel_container)
            left_layout.addStretch()

            # Create right panel for canvas only (adaptive width)
            right_panel = QWidget()
            # Make right panel (canvas) expand to take all available space
            right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            right_layout = QVBoxLayout(right_panel)
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(0)
            right_layout.addWidget(self.canvas_widget)
            
            # Add left panel and right panel to main layout
            main_layout.addWidget(left_panel)
            main_layout.addWidget(right_panel, 1)  # 使用拉伸因子让右侧画布占满剩余空间

            # Make CanvasEditor expand to fill available space
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            #self.canvas_widget.set_timeline_item(self.timeline_item)
        except Exception as e:
            print(f"Error initializing CanvasEditor: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def set_tool_panel(self, widget: QWidget):
        """Replace tool config panel content in the left panel."""
        # Clear previous widgets
        while self.tool_panel_layout.count():
            item = self.tool_panel_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        if widget:
            self.tool_panel_layout.addWidget(widget)
        else:
            from PySide6.QtWidgets import QLabel
            self.tool_panel_layout.addWidget(QLabel("No Tool Config"))
    
    def on_task_finished(self, result: TaskResult):
        """Handle task finished event - add generated image as a new layer"""
        print(f"Task finished: {result.get_task_id()}")
        # Get the image path from the task result
        image_path = result.get_image_path()
        if image_path and self.canvas_widget:
            self.canvas_widget.reload()