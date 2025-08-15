"""
Canvas Editor Component
This module implements a canvas editor with a left toolbar and right canvas area using PySide6.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QSizePolicy)

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
    
    def set_background_size(self, width: int, height: int):
        """Set the background size for the canvas widget"""
        self.canvas_widget.background_width = width
        self.canvas_widget.background_height = height
        self.canvas_widget.update()
    
    def on_task_finished(self, result: TaskResult):
        """Handle task finished event - add generated image as a new layer"""
        print(f"Task finished: {result.get_task_id()}")
        # Get the image path from the task result
        image_path = result.get_image_path()
        if image_path and self.canvas_widget:
            self.canvas_widget.reload()