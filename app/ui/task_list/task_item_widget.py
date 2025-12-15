# task_item_widget.py
import os
import math
from datetime import datetime
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal, QTimer, QRectF, QPointF
from PySide6.QtGui import QFont, QPainter, QPainterPath, QPen, QColor, QPixmap, QMovie

from app.ui.base_widget import BaseWidget


class TaskItemWidget(BaseWidget):
    clicked = Signal(object)  # Signal emitted when task item is clicked

    def __init__(self, task, workspace=None, parent=None):
        # 如果没有提供workspace，则不进行连接
        if workspace is not None:
            super().__init__(workspace)
        else:
            super().__init__(None)  # 这将触发错误检查
        self.task_id = task.task_id
        self.task = task
        self.is_selected = False
        self.is_hovered = False
        
        # Animation timer for waiting state
        self.animation_angle = 0
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_animation)
        
        # Enable hover events for highlight effect
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        
        self.init_ui()
        self.update_display(task)

    def init_ui(self):
        # 设置固定尺寸
        self.setFixedSize(200, 200)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Preview area (main content)
        self.preview_widget = QWidget()
        self.preview_widget.setFixedSize(200, 200)
        preview_layout = QVBoxLayout(self.preview_widget)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        preview_layout.setAlignment(Qt.AlignCenter)
        
        # Placeholder for tool icon and name
        self.tool_icon_label = QLabel()
        self.tool_icon_label.setAlignment(Qt.AlignCenter)
        self.tool_icon_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 48px;
            }
        """)
        
        self.tool_name_label = QLabel()
        self.tool_name_label.setAlignment(Qt.AlignCenter)
        self.tool_name_label.setFont(QFont("Arial", 10))
        self.tool_name_label.setStyleSheet("color: #808080;")
        
        # Image/Video preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setScaledContents(False)
        
        # Center status label (waiting/countdown/duration)
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background-color: rgba(0, 0, 0, 120);
                border-radius: 4px;
                padding: 5px 10px;
            }
        """)
        
        preview_layout.addWidget(self.tool_icon_label)
        preview_layout.addWidget(self.tool_name_label)
        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.status_label)
        
        # Task number bubble (top-right corner)
        self.task_number_label = QLabel(self.preview_widget)
        self.task_number_label.setAlignment(Qt.AlignCenter)
        self.task_number_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.task_number_label.setFixedSize(40, 40)
        self.task_number_label.move(152, 8)  # Position in top-right
        self.task_number_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background-color: #4A90E2;
                border-radius: 20px;
            }
        """)
        
        layout.addWidget(self.preview_widget)
        
        # Store progress border properties
        self.progress_percent = 0
        self.border_width = 4
        
    def _update_animation(self):
        """Update animation angle for waiting state"""
        self.animation_angle = (self.animation_angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """Custom paint event to draw progress border"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw progress border
        rect = self.rect().adjusted(self.border_width//2, self.border_width//2, 
                                    -self.border_width//2, -self.border_width//2)
        
        # Determine color based on status
        if self.task.status == "completed" or self.task.status == "finished":
            border_color = QColor(76, 175, 80)  # Green
        elif self.task.status == "failed" or self.task.status == "error":
            border_color = QColor(244, 67, 54)  # Red
        elif self.task.status == "running" or self.task.status == "executing":
            border_color = QColor(66, 165, 245)  # Blue
        else:
            border_color = QColor(158, 158, 158)  # Gray for waiting
        
        # Draw background border (gray)
        pen = QPen(QColor(80, 82, 84), self.border_width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 8, 8)
        
        # Draw progress border clockwise from bottom-left
        if self.progress_percent > 0:
            pen = QPen(border_color, self.border_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            # Calculate path for progress border
            path = QPainterPath()
            
            # Total perimeter
            width = rect.width()
            height = rect.height()
            corner_radius = 8
            
            # Approximate perimeter (simplified, not accounting for rounded corners exactly)
            perimeter = 2 * (width + height)
            progress_length = (self.progress_percent / 100.0) * perimeter
            
            # Start from bottom-left corner
            start_x = rect.left()
            start_y = rect.bottom()
            
            # Draw clockwise: left edge (up), top edge (right), right edge (down), bottom edge (left)
            path.moveTo(start_x, start_y)
            
            remaining = progress_length
            
            # Left edge (going up)
            left_edge = height
            if remaining > 0:
                draw_length = min(remaining, left_edge)
                path.lineTo(start_x, start_y - draw_length)
                remaining -= draw_length
            
            # Top edge (going right)
            if remaining > 0:
                top_edge = width
                draw_length = min(remaining, top_edge)
                path.lineTo(rect.left() + draw_length, rect.top())
                remaining -= draw_length
            
            # Right edge (going down)
            if remaining > 0:
                right_edge = height
                draw_length = min(remaining, right_edge)
                path.lineTo(rect.right(), rect.top() + draw_length)
                remaining -= draw_length
            
            # Bottom edge (going left)
            if remaining > 0:
                bottom_edge = width
                draw_length = min(remaining, bottom_edge)
                path.lineTo(rect.right() - draw_length, rect.bottom())
            
            painter.drawPath(path)
        
        # Draw hover/selection effect
        if self.is_selected:
            pen = QPen(QColor(255, 255, 255, 180), 2)
            painter.setPen(pen)
            painter.drawRoundedRect(rect.adjusted(-1, -1, 1, 1), 8, 8)
        elif self.is_hovered:
            pen = QPen(QColor(255, 255, 255, 80), 1)
            painter.setPen(pen)
            painter.drawRoundedRect(rect.adjusted(-1, -1, 1, 1), 8, 8)

    def mousePressEvent(self, event):
        """Handle mouse click events"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self)

    def set_selected(self, selected):
        """Set the selected state and update appearance"""
        self.is_selected = selected
        self.update()

    def update_display(self, task):
        """Update widget display based on task data"""
        self.task = task
        self.progress_percent = task.percent
        
        # Update task number bubble
        self.task_number_label.setText(f"#{task.task_id}")
        
        # Tool icon mapping
        icon_map = {
            "download": "⬇️",
            "upload": "⬆️",
            "convert": "🔄",
            "backup": "📦",
            "sync": "🔁",
            "text2img": "🖼️",
            "img2video": "🎬",
            "imgedit": "✏️",
            "generate": "🔄",
            "default": "📋"
        }
        
        # Check if result files exist
        result_file = None
        if hasattr(task, 'path') and os.path.exists(task.path):
            for filename in os.listdir(task.path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.avi', '.mov', '.webm')):
                    result_file = os.path.join(task.path, filename)
                    break
        
        # Show preview or placeholder
        if result_file and os.path.exists(result_file):
            # Show preview
            self.tool_icon_label.hide()
            self.tool_name_label.hide()
            self.preview_label.show()
            
            if result_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                pixmap = QPixmap(result_file)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(184, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.preview_label.setPixmap(scaled_pixmap)
            else:
                # Video thumbnail placeholder
                self.preview_label.setText("🎬 Video")
                self.preview_label.setStyleSheet("color: #808080; font-size: 24px;")
        else:
            # Show placeholder
            self.preview_label.hide()
            self.tool_icon_label.show()
            self.tool_name_label.show()
            
            emoji = icon_map.get(task.tool, "📋")
            self.tool_icon_label.setText(emoji)
            self.tool_name_label.setText(task.tool.upper())
        
        # Update center status label
        self._update_status_label(task)
        
        # Start/stop animation based on status
        if task.status == "waiting" or task.status == "pending":
            self.animation_timer.start(50)
        else:
            self.animation_timer.stop()
        
        self.update()
    
    def _update_status_label(self, task):
        """Update the center status label based on task status"""
        status = task.status
        
        if status == "waiting" or status == "pending":
            # Show waiting animation
            self.status_label.setText("⏳ Waiting...")
            self.status_label.show()
        elif status == "running" or status == "executing":
            # Show countdown or progress
            if hasattr(task, 'estimated_time') and task.estimated_time:
                self.status_label.setText(f"⏱️ {task.estimated_time}s")
            else:
                self.status_label.setText(f"🔄 {task.percent}%")
            self.status_label.show()
        elif status == "completed" or status == "finished":
            # Show execution duration
            if hasattr(task, 'duration') and task.duration:
                self.status_label.setText(f"✓ {task.duration}s")
            else:
                self.status_label.setText("✓ Done")
            self.status_label.show()
        elif status == "failed" or status == "error":
            self.status_label.setText("✗ Failed")
            self.status_label.show()
        else:
            self.status_label.hide()

    def enterEvent(self, event):
        """Handle mouse enter event"""
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)