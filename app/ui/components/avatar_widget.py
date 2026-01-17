"""
Avatar Component

Reusable avatar component for displaying agent icons with consistent styling.
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont, QPen


class AvatarWidget(QWidget):
    """Reusable avatar widget for displaying agent icons."""

    def __init__(self, icon: str = "👤", color: str = "#4a90e2", size: int = 32, shape: str = "circle", parent=None):
        super().__init__(parent)
        self.icon = icon
        self.color = color
        self.size = size
        self.shape = shape  # "circle" or "rounded_rect"

        self._create_avatar()

    def _create_avatar(self):
        """Create the avatar pixmap."""
        pixmap = QPixmap(self.size, self.size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background based on shape
        bg_color = QColor(self.color)
        painter.setBrush(bg_color)
        painter.setPen(QPen(bg_color))

        if self.shape == "circle":
            # Draw circle
            painter.drawEllipse(0, 0, self.size, self.size)
        else:  # rounded_rect
            # Draw rounded rectangle with corner radius of size//4
            painter.drawRoundedRect(0, 0, self.size, self.size, self.size//4, self.size//4)

        # Draw icon
        icon_char = self.icon
        if len(icon_char) == 1 and ord(icon_char) < 128:
            # Regular letter
            font = QFont()
            font.setPointSize(self.size // 2)
            font.setBold(True)
            painter.setFont(font)
        else:
            # Emoji or iconfont
            font = QFont()
            font.setPointSize(self.size // 2 - 2)
            painter.setFont(font)

        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(0, 0, self.size, self.size, Qt.AlignCenter, icon_char)

        painter.end()

        # Set as background
        self.setFixedSize(self.size, self.size)
        self.setStyleSheet(f"border-image: url({self._pixmap_to_base64(pixmap)});")

    def _pixmap_to_base64(self, pixmap):
        """Convert pixmap to base64 string for CSS."""
        # This is a workaround since we can't directly embed pixmaps in stylesheets
        # Instead, we'll override the paintEvent to draw the pixmap
        self.pixmap = pixmap
        return ""

    def paintEvent(self, event):
        """Paint the avatar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, self.pixmap)

    def set_icon(self, icon: str):
        """Update the icon."""
        self.icon = icon
        self._create_avatar()

    def set_color(self, color: str):
        """Update the background color."""
        self.color = color
        self._create_avatar()

    def set_size(self, size: int):
        """Update the size."""
        self.size = size
        self._create_avatar()

    def set_shape(self, shape: str):
        """Update the shape."""
        self.shape = shape
        self._create_avatar()