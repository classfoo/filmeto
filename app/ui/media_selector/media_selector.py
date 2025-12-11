from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QStackedWidget, QApplication, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal, QMimeData, QEvent, QSize, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QPainter, QPen, QColor, QFont, QTransform
import os
from typing import List, Optional


class MediaSelector(QWidget):
    """
    Media selector component that allows selecting various types of files and previewing them.
    
    Features:
    1. Supports multiple file types including images, audio, video, text, models, etc.
    2. Shows preview in a 100px wide box
    3. Shows drag-and-drop area when no file is selected
    4. Supports file selection via dialog or drag-and-drop
    5. Configurable supported file types
    6. Value represents the selected file path
    """
    
    # Signal emitted when file selection changes
    file_selected = Signal(str)  # file_path
    file_cleared = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_path: Optional[str] = None
        self._supported_types: List[str] = []  # Empty means all types supported
        self._preview_width = 60
        self._preview_height = 90
        self._placeholder_text = ""  # Default empty text, can be customized
        
        self.setup_ui()
        self.setAcceptDrops(True)
        
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget to switch between preview and placeholder
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Preview widget
        self.preview_widget = MediaPreviewWidget(self._preview_width, self._preview_height)
        self.preview_widget.clicked.connect(self._on_preview_clicked)
        self.stacked_widget.addWidget(self.preview_widget)
        
        # Placeholder widget
        self.placeholder_widget = MediaPlaceholderWidget(self._preview_width, self._preview_height, self._placeholder_text)
        self.placeholder_widget.clicked.connect(self._on_placeholder_clicked)
        self.stacked_widget.addWidget(self.placeholder_widget)
        
        # Initially show placeholder
        self.stacked_widget.setCurrentWidget(self.placeholder_widget)
        
    def set_supported_types(self, types: List[str]):
        """
        Set supported file types.
        
        Args:
            types: List of supported file extensions (e.g., ['png', 'jpg', 'mp4'])
                  Empty list means all types are supported
        """
        self._supported_types = [t.lower().strip('.') for t in types] if types else []
        
    def get_supported_types(self) -> List[str]:
        """Get currently supported file types"""
        return self._supported_types[:]
    
    def set_placeholder_text(self, text: str):
        """Set the placeholder text displayed when no file is selected"""
        self._placeholder_text = text
        if hasattr(self, 'placeholder_widget'):
            self.placeholder_widget.set_text(text)
        
    def set_value(self, file_path: Optional[str]):
        """
        Set the selected file path.
        
        Args:
            file_path: Path to the selected file, or None to clear selection
        """
        if file_path == self._file_path:
            return
            
        self._file_path = file_path
        
        if file_path and os.path.exists(file_path):
            self.preview_widget.set_file(file_path)
            self.stacked_widget.setCurrentWidget(self.preview_widget)
            self.file_selected.emit(file_path)
        else:
            self.stacked_widget.setCurrentWidget(self.placeholder_widget)
            if file_path is None:
                self.file_cleared.emit()
                
    def get_value(self) -> Optional[str]:
        """Get the selected file path"""
        return self._file_path
        
    def clear(self):
        """Clear the current selection"""
        self.set_value(None)
        
    def _on_preview_clicked(self):
        """Handle preview widget click"""
        self._open_file_dialog()
        
    def _on_placeholder_clicked(self):
        """Handle placeholder widget click"""
        self._open_file_dialog()
        
    def _open_file_dialog(self):
        """Open file dialog to select a file"""
        # Build filter string
        if self._supported_types:
            extensions = [f"*.{ext}" for ext in self._supported_types]
            filter_str = f"Supported Files ({' '.join(extensions)});;All Files (*)"
        else:
            filter_str = "All Files (*)"
            
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", filter_str)
        if file_path:
            self.set_value(file_path)
            
    def _is_file_type_supported(self, file_path: str) -> bool:
        """Check if the file type is supported"""
        if not self._supported_types:
            return True  # All types supported
            
        _, ext = os.path.splitext(file_path)
        return ext.lower().strip('.') in self._supported_types
        
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if os.path.isfile(file_path) and self._is_file_type_supported(file_path):
                    event.acceptProposedAction()
                    return
        event.ignore()
        
    def dropEvent(self, event):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if os.path.isfile(file_path) and self._is_file_type_supported(file_path):
                    self.set_value(file_path)
                    event.acceptProposedAction()
                    return
        event.ignore()


class MediaPreviewWidget(QWidget):
    """Widget to preview the selected media file with floating paper effect"""
    
    clicked = Signal()
    
    def __init__(self, width: int, height: int, parent=None):
        super().__init__(parent)
        self._base_width = width
        self._base_height = height
        # Add extra space for shadow and hover scale
        self.setFixedSize(width + 8, height + 8)
        self._file_path: Optional[str] = None
        self._pixmap: Optional[QPixmap] = None
        self._file_type: str = "unknown"  # image, audio, video, text, model, unknown
        self._scale = 1.0
        self._tilt_angle = -3  # Slight tilt angle in degrees
        
        # Setup hover animation
        self._scale_animation = QPropertyAnimation(self, b"scale")
        self._scale_animation.setDuration(150)
        self._scale_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Enable mouse tracking for hover effect
        self.setMouseTracking(True)
    
    def get_scale(self):
        return self._scale
    
    def set_scale(self, value):
        self._scale = value
        self.update()
    
    scale = Property(float, get_scale, set_scale)
        
    def set_file(self, file_path: str):
        """Set the file to preview"""
        self._file_path = file_path
        self._determine_file_type()
        
        if self._file_type == "image":
            self._load_image_preview()
        else:
            self._pixmap = None
            
        self.update()
        
    def _determine_file_type(self):
        """Determine the file type based on extension"""
        if not self._file_path:
            self._file_type = "unknown"
            return
            
        _, ext = os.path.splitext(self._file_path)
        ext = ext.lower()
        
        image_exts = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.svg']
        audio_exts = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a']
        video_exts = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
        text_exts = ['.txt', '.md', '.rst', '.log']
        model_exts = ['.pt', '.pth', '.h5', '.onnx', '.pb', '.tflite', '.ckpt']
        
        if ext in image_exts:
            self._file_type = "image"
        elif ext in audio_exts:
            self._file_type = "audio"
        elif ext in video_exts:
            self._file_type = "video"
        elif ext in text_exts:
            self._file_type = "text"
        elif ext in model_exts:
            self._file_type = "model"
        else:
            self._file_type = "unknown"
            
    def _load_image_preview(self):
        """Load image preview"""
        if not self._file_path:
            self._pixmap = None
            return
            
        pixmap = QPixmap(self._file_path)
        if pixmap.isNull():
            self._pixmap = None
        else:
            self._pixmap = pixmap.scaled(
                self._base_width - 4, 
                self._base_height - 4, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
    def paintEvent(self, event):
        """Paint the preview with floating paper effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Calculate center for transformations
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Apply transformations: translate to center, scale, rotate, translate back
        transform = QTransform()
        transform.translate(center_x, center_y)
        transform.scale(self._scale, self._scale)
        transform.rotate(self._tilt_angle)
        transform.translate(-center_x, -center_y)
        painter.setTransform(transform)
        
        # Calculate paper rect (centered in widget)
        paper_x = (self.width() - self._base_width) / 2
        paper_y = (self.height() - self._base_height) / 2
        
        # Draw shadow (offset from paper)
        shadow_offset = 3
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 40))
        painter.drawRoundedRect(paper_x + shadow_offset, paper_y + shadow_offset, 
                                self._base_width, self._base_height, 3, 3)
        
        # Draw paper background (no border, clean white)
        painter.setBrush(QColor("#ffffff"))
        painter.drawRoundedRect(paper_x, paper_y, self._base_width, self._base_height, 3, 3)
        
        if self._file_type == "image" and self._pixmap:
            # Draw image centered on paper
            img_x = paper_x + (self._base_width - self._pixmap.width()) / 2
            img_y = paper_y + (self._base_height - self._pixmap.height()) / 2
            painter.drawPixmap(int(img_x), int(img_y), self._pixmap)
        else:
            # Draw file type icon/text
            self._draw_file_icon(painter, paper_x, paper_y)
            
        painter.end()
    
    def _draw_file_icon(self, painter: QPainter, paper_x: float, paper_y: float):
        """Draw an icon representing the file type"""
        # Draw icon based on file type centered on paper
        center_x = paper_x + self._base_width / 2
        center_y = paper_y + self._base_height / 2
        
        font = QFont()
        font.setBold(True)
        font.setPixelSize(10)
        painter.setFont(font)
        
        if self._file_type == "audio":
            painter.setPen(QColor("#4caf50"))
            painter.drawText(int(paper_x), int(paper_y), 
                           int(self._base_width), int(self._base_height),
                           Qt.AlignCenter, "♪")
        elif self._file_type == "video":
            painter.setPen(QColor("#f44336"))
            painter.drawText(int(paper_x), int(paper_y), 
                           int(self._base_width), int(self._base_height),
                           Qt.AlignCenter, "▶")
        elif self._file_type == "text":
            painter.setPen(QColor("#2196f3"))
            painter.drawText(int(paper_x), int(paper_y), 
                           int(self._base_width), int(self._base_height),
                           Qt.AlignCenter, "TXT")
        elif self._file_type == "model":
            painter.setPen(QColor("#9c27b0"))
            painter.drawText(int(paper_x), int(paper_y), 
                           int(self._base_width), int(self._base_height),
                           Qt.AlignCenter, "AI")
        else:
            painter.setPen(QColor("#9e9e9e"))
            painter.drawText(int(paper_x), int(paper_y), 
                           int(self._base_width), int(self._base_height),
                           Qt.AlignCenter, "FILE")
    
    def enterEvent(self, event):
        """Handle mouse enter - scale up"""
        self._scale_animation.stop()
        self._scale_animation.setStartValue(self._scale)
        self._scale_animation.setEndValue(1.08)
        self._scale_animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave - scale down"""
        self._scale_animation.stop()
        self._scale_animation.setStartValue(self._scale)
        self._scale_animation.setEndValue(1.0)
        self._scale_animation.start()
        super().leaveEvent(event)
            
    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MediaPlaceholderWidget(QWidget):
    """Placeholder widget shown when no file is selected with floating paper effect"""
    
    clicked = Signal()
    
    def __init__(self, width: int, height: int, text: str = "", parent=None):
        super().__init__(parent)
        self._base_width = width
        self._base_height = height
        # Add extra space for shadow and hover scale
        self.setFixedSize(width + 8, height + 8)
        self.setAcceptDrops(True)
        self._text = text
        self._scale = 1.0
        self._tilt_angle = -3  # Slight tilt angle in degrees
        
        # Setup hover animation
        self._scale_animation = QPropertyAnimation(self, b"scale")
        self._scale_animation.setDuration(150)
        self._scale_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Enable mouse tracking for hover effect
        self.setMouseTracking(True)
    
    def get_scale(self):
        return self._scale
    
    def set_scale(self, value):
        self._scale = value
        self.update()
    
    scale = Property(float, get_scale, set_scale)
        
    def set_text(self, text: str):
        """Set the placeholder text"""
        self._text = text
        self.update()
    
    def paintEvent(self, event):
        """Paint the placeholder with floating paper effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Calculate center for transformations
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Apply transformations: translate to center, scale, rotate, translate back
        transform = QTransform()
        transform.translate(center_x, center_y)
        transform.scale(self._scale, self._scale)
        transform.rotate(self._tilt_angle)
        transform.translate(-center_x, -center_y)
        painter.setTransform(transform)
        
        # Calculate paper rect (centered in widget)
        paper_x = (self.width() - self._base_width) / 2
        paper_y = (self.height() - self._base_height) / 2
        
        # Draw shadow (offset from paper)
        shadow_offset = 3
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 40))
        painter.drawRoundedRect(paper_x + shadow_offset, paper_y + shadow_offset, 
                                self._base_width, self._base_height, 3, 3)
        
        # Draw paper background (no border, clean white/light gray)
        painter.setBrush(QColor("#f8f8f8"))
        painter.drawRoundedRect(paper_x, paper_y, self._base_width, self._base_height, 3, 3)
        
        # Draw plus icon (smaller size)
        pen = QPen(QColor("#9e9e9e"))
        pen.setWidth(2)
        painter.setPen(pen)
        
        icon_center_x = paper_x + self._base_width / 2
        icon_center_y = paper_y + self._base_height / 2 if not self._text else paper_y + self._base_height / 2 - 6
        line_length = 12
        
        # Horizontal line
        painter.drawLine(int(icon_center_x - line_length / 2), int(icon_center_y), 
                        int(icon_center_x + line_length / 2), int(icon_center_y))
        # Vertical line
        painter.drawLine(int(icon_center_x), int(icon_center_y - line_length / 2),
                        int(icon_center_x), int(icon_center_y + line_length / 2))
        
        # Draw text if provided
        if self._text:
            painter.setPen(QColor("#9e9e9e"))
            font = QFont()
            font.setPixelSize(8)
            painter.setFont(font)
            text_rect_y = paper_y + self._base_height - 12
            painter.drawText(int(paper_x), int(text_rect_y), 
                           int(self._base_width), 12,
                           Qt.AlignHCenter | Qt.AlignTop, self._text)
        
        painter.end()
    
    def enterEvent(self, event):
        """Handle mouse enter - scale up"""
        self._scale_animation.stop()
        self._scale_animation.setStartValue(self._scale)
        self._scale_animation.setEndValue(1.08)
        self._scale_animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave - scale down"""
        self._scale_animation.stop()
        self._scale_animation.setStartValue(self._scale)
        self._scale_animation.setEndValue(1.0)
        self._scale_animation.start()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
        
    def dragEnterEvent(self, event):
        """Handle drag enter event - just accept for visual feedback"""
        event.acceptProposedAction()
        
    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        super().dragLeaveEvent(event)
        
    def dropEvent(self, event):
        """Handle drop event - just accept for visual feedback"""
        event.acceptProposedAction()