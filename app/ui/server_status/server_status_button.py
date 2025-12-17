"""
Server Status Button

A button widget that displays the count of active and inactive servers
with a beautiful badge UI. Clicking opens the server management dialog.
"""

from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QFont, QPaintEvent

from app.ui.base_widget import BaseWidget
from utils.i18n_utils import tr


class ServerStatusButton(QPushButton):
    """
    A custom button that displays server status with badges.
    Shows active and inactive server counts with color-coded indicators.
    """
    
    # Signal emitted when button is clicked
    status_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("server_status_button")
        
        # Server counts
        self._active_count = 0
        self._inactive_count = 0
        
        # Animation property for hover effect
        self._hover_progress = 0.0
        
        # Setup button
        self.setFixedSize(80, 32)
        self.setToolTip(tr("服务器状态"))
        self.setCursor(Qt.PointingHandCursor)
        
        # Apply styling
        self._apply_styles()
        
        # Connect click signal
        self.clicked.connect(self.status_clicked)
    
    def _apply_styles(self):
        """Apply button styling"""
        self.setStyleSheet("""
            QPushButton#server_status_button {
                background-color: #3c3f41;
                border: 1px solid #555555;
                border-radius: 4px;
                margin: 2px;
                color: #ffffff;
                font-size: 12px;
                padding: 4px 8px;
                text-align: left;
            }
            
            QPushButton#server_status_button:hover {
                background-color: #4c5052;
                border: 1px solid #666666;
            }
            
            QPushButton#server_status_button:pressed {
                background-color: #2c2f31;
            }
        """)
    
    def set_server_counts(self, active: int, inactive: int):
        """
        Update server counts and refresh display.
        
        Args:
            active: Number of active servers
            inactive: Number of inactive servers
        """
        self._active_count = active
        self._inactive_count = inactive
        self.update()
    
    def get_active_count(self) -> int:
        """Get active server count"""
        return self._active_count
    
    def get_inactive_count(self) -> int:
        """Get inactive server count"""
        return self._inactive_count
    
    def paintEvent(self, event: QPaintEvent):
        """Custom paint event to draw badges"""
        # Call parent paint first (draws the button background)
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw server icon (using Unicode character)
        icon_font = QFont("iconfont", 12)
        painter.setFont(icon_font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(8, 20, "\ue66e")  # Server icon
        
        # Calculate badge positions
        badge_y = 10
        active_badge_x = 30
        inactive_badge_x = 55
        
        # Draw active server badge (green)
        self._draw_badge(
            painter,
            active_badge_x,
            badge_y,
            self._active_count,
            QColor(76, 175, 80),  # Green
            QColor(56, 142, 60)   # Dark green
        )
        
        # Draw inactive server badge (orange/red)
        badge_color = QColor(255, 152, 0) if self._inactive_count == 0 else QColor(244, 67, 54)  # Orange or Red
        dark_color = QColor(230, 120, 0) if self._inactive_count == 0 else QColor(211, 47, 47)
        
        self._draw_badge(
            painter,
            inactive_badge_x,
            badge_y,
            self._inactive_count,
            badge_color,
            dark_color
        )
        
        painter.end()
    
    def _draw_badge(
        self,
        painter: QPainter,
        x: int,
        y: int,
        count: int,
        bg_color: QColor,
        border_color: QColor
    ):
        """
        Draw a circular badge with count.
        
        Args:
            painter: QPainter instance
            x: X coordinate of badge center
            y: Y coordinate of badge center
            count: Number to display
            bg_color: Background color
            border_color: Border color
        """
        # Badge dimensions
        radius = 9
        
        # Draw border (outer circle)
        painter.setPen(border_color)
        painter.setBrush(border_color)
        painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
        
        # Draw background (inner circle)
        inner_radius = radius - 1
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawEllipse(x - inner_radius, y - inner_radius, inner_radius * 2, inner_radius * 2)
        
        # Draw count text
        count_text = str(count) if count < 100 else "99+"
        font = QFont("Arial", 7, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        
        # Center text in badge
        text_rect = painter.fontMetrics().boundingRect(count_text)
        text_x = x - text_rect.width() // 2
        text_y = y + text_rect.height() // 2 - 2
        
        painter.drawText(text_x, text_y, count_text)


class ServerStatusWidget(BaseWidget):
    """
    Widget wrapper for ServerStatusButton with auto-refresh capability.
    Integrates with ServerManager to fetch and display real-time status.
    """
    
    # Signal emitted when status needs to be shown
    show_status_dialog = Signal()
    
    def __init__(self, workspace):
        super().__init__(workspace)
        
        # Create status button
        self.status_button = ServerStatusButton(self)
        self.status_button.status_clicked.connect(self._on_button_clicked)
        
        # # Setup refresh timer
        # self.refresh_timer = QTimer(self)
        # self.refresh_timer.timeout.connect(self._refresh_status)
        # self.refresh_timer.start(5000)  # Refresh every 5 seconds
        #
        # # Initial refresh
        # self._refresh_status()
    
    def _on_button_clicked(self):
        """Handle button click - emit signal to show dialog"""
        self.show_status_dialog.emit()
    
    def _refresh_status(self):
        """Refresh server status from ServerManager"""
        try:
            # Import here to avoid circular dependency
            from server.server import ServerManager
            import os
            
            # Get workspace path
            workspace_path = self.workspace.workspace_path
            
            # Create server manager
            server_manager = ServerManager(workspace_path)
            
            # Get server counts
            servers = server_manager.list_servers()
            active_count = sum(1 for s in servers if s.is_enabled)
            inactive_count = sum(1 for s in servers if not s.is_enabled)
            
            # Update button
            self.status_button.set_server_counts(active_count, inactive_count)
            
        except Exception as e:
            print(f"Failed to refresh server status: {e}")
            # Set default counts on error
            self.status_button.set_server_counts(0, 0)
    
    def force_refresh(self):
        """Force an immediate status refresh"""
        self._refresh_status()

