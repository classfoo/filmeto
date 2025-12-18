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
        self.setObjectName("main_window_top_bar_button")

        # Server counts
        self._active_count = 0
        self._inactive_count = 0

        # Animation property for hover effect
        self._hover_progress = 0.0

        # Setup button - match language button dimensions
        self.setFixedSize(80, 32)  # Width for icon + text, height matches language button
        self.setToolTip(tr("服务器管理"))
        self.setCursor(Qt.PointingHandCursor)

        # Apply styling - using the same style as language button
        self._apply_styles()

        # Connect click signal
        self.clicked.connect(self.status_clicked)
    
    def _apply_styles(self):
        """Apply button styling - matches language button style"""
        self.setStyleSheet("""
            QPushButton#main_window_top_bar_button {
                background-color: #3c3f41;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                font-size: 14px;
                text-align: center;
                padding: 4px;
            }

            QPushButton#main_window_top_bar_button:hover {
                background-color: #4c5052;
                border: 1px solid #666666;
            }

            QPushButton#main_window_top_bar_button:pressed {
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
        """Custom paint event to draw server icon with text and badge"""
        # Call parent paint first (draws the button background)
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate total servers count
        total_count = self._active_count + self._inactive_count

        # Draw server icon (using Unicode character) - shifted to the left to make space for text
        icon_font = QFont("iconfont", 14)  # Match language button font size
        painter.setFont(icon_font)
        painter.setPen(QColor(255, 255, 255))

        # Vertically center the icon
        icon_metrics = painter.fontMetrics()
        icon_y = (self.height() + icon_metrics.height()) // 2 - 2
        painter.drawText(6, icon_y, "\ue66e")  # Server icon

        # Draw "Server" text to the right of the icon
        text_font = QFont()
        text_font.setPointSize(9)  # Slightly smaller for better fit
        painter.setFont(text_font)
        painter.setPen(QColor(255, 255, 255))

        # Vertically center the text
        text_metrics = painter.fontMetrics()
        text_y = (self.height() + text_metrics.height()) // 2 - 2
        painter.drawText(24, text_y, "Server")  # Draw "Server" text to the right of icon

        # Draw total server count badge, vertically centered on the right side
        # Always draw the badge, but change appearance based on server count
        # Calculate position for the badge (centered vertically on the right)
        badge_radius = 9  # Same as in _draw_badge
        # Position the center of the badge so that the entire badge is within the button
        # Right edge of badge = badge_x + badge_radius <= self.width() - 2 (for edge margin)
        # So badge_x <= self.width() - badge_radius - 2
        badge_x = self.width() - badge_radius - 6  # Position to the right with some margin from edge
        # Vertically center the badge
        badge_y = self.height() // 2

        # Set colors based on server status
        if total_count > 0:
            # Draw full badge when there are servers
            badge_color = QColor(76, 175, 80) if self._active_count > 0 else QColor(244, 67, 54)  # Green if active, red if all inactive
            dark_color = QColor(56, 142, 60) if self._active_count > 0 else QColor(211, 47, 47)
            show_text = True
        else:
            # Draw a more visible gray badge when no servers exist (to maintain consistent UI)
            badge_color = QColor(128, 128, 128)  # Gray
            dark_color = QColor(96, 96, 96)    # Darker gray
            show_text = False

        self._draw_badge(
            painter,
            badge_x,
            badge_y,
            total_count,
            badge_color,
            dark_color,
            show_text
        )

        painter.end()
    
    def _draw_badge(
        self,
        painter: QPainter,
        x: int,
        y: int,
        count: int,
        bg_color: QColor,
        border_color: QColor,
        show_count: bool = True
    ):
        """
        Draw a circular badge with count (no border).

        Args:
            painter: QPainter instance
            x: X coordinate of badge center
            y: Y coordinate of badge center
            count: Number to display
            bg_color: Background color
            border_color: Border color (not used since no border)
            show_count: Whether to display the count number (default True)
        """
        # Badge dimensions
        radius = 9

        # Draw filled circle (no border, just filled)
        painter.setPen(Qt.NoPen)  # No border pen
        painter.setBrush(bg_color)
        painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

        # Draw count text if requested and count > 0
        if show_count and count > 0:
            count_text = str(count) if count < 100 else "99+"
            font = QFont("Arial", 10, QFont.Bold)  # Larger font
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))

            # Center text in badge
            text_rect = painter.fontMetrics().boundingRect(count_text)
            text_x = x - text_rect.width() // 2
            text_y = y + text_rect.height() // 2 - 2  # Adjust vertical position for centering

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

        # Setup refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_status)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

        # Initial refresh
        self._refresh_status()
    
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

