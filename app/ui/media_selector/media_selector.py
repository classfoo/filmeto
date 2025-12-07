from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QStackedWidget, QApplication
from PySide6.QtCore import Qt, Signal, QMimeData, QEvent, QSize
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QPainter, QPen, QColor, QFont
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
        self._preview_width = 100
        self._preview_height = 100
        
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
        self.placeholder_widget = MediaPlaceholderWidget(self._preview_width, self._preview_height)
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
    """Widget to preview the selected media file"""
    
    clicked = Signal()
    
    def __init__(self, width: int, height: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._file_path: Optional[str] = None
        self._pixmap: Optional[QPixmap] = None
        self._file_type: str = "unknown"  # image, audio, video, text, model, unknown
        
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
                self.width() - 4, 
                self.height() - 4, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
    def paintEvent(self, event):
        """Paint the preview"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw border
        pen = QPen(QColor("#4080ff"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(QColor("#f0f0f0"))
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 4, 4)
        
        if self._file_type == "image" and self._pixmap:
            # Draw image centered
            x = (self.width() - self._pixmap.width()) // 2
            y = (self.height() - self._pixmap.height()) // 2
            painter.drawPixmap(x, y, self._pixmap)
        else:
            # Draw file type icon/text
            self._draw_file_icon(painter)
            
        painter.end()
        
    def _draw_file_icon(self, painter: QPainter):
        """Draw an icon representing the file type"""
        # Draw a generic file icon
        painter.setBrush(QColor("#ffffff"))
        painter.drawRect(20, 15, 60, 70)
        
        # Draw icon based on file type
        if self._file_type == "audio":
            painter.setBrush(QColor("#4caf50"))
            painter.drawEllipse(45, 30, 20, 20)
        elif self._file_type == "video":
            painter.setBrush(QColor("#f44336"))
            painter.drawRoundedRect(40, 30, 30, 20, 2, 2)
        elif self._file_type == "text":
            painter.setPen(QColor("#2196f3"))
            font = QFont()
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "TXT")
        elif self._file_type == "model":
            painter.setPen(QColor("#9c27b0"))
            font = QFont()
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "AI")
        else:
            painter.setPen(QColor("#9e9e9e"))
            font = QFont()
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "FILE")
            
    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MediaPlaceholderWidget(QWidget):
    """Placeholder widget shown when no file is selected"""
    
    clicked = Signal()
    
    def __init__(self, width: int, height: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setAcceptDrops(True)
        
    def paintEvent(self, event):
        """Paint the placeholder"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw dashed border
        pen = QPen(QColor("#cccccc"))
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(QColor("#fafafa"))
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 4, 4)
        
        # Draw plus icon
        pen.setStyle(Qt.SolidLine)
        pen.setWidth(3)
        pen.setColor(QColor("#9e9e9e"))
        painter.setPen(pen)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        line_length = 20
        
        # Horizontal line
        painter.drawLine(center_x - line_length // 2, center_y, 
                        center_x + line_length // 2, center_y)
        # Vertical line
        painter.drawLine(center_x, center_y - line_length // 2,
                        center_x, center_y + line_length // 2)
        
        # Draw text
        painter.setPen(QColor("#9e9e9e"))
        font = QFont()
        font.setPixelSize(12)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignHCenter | Qt.AlignBottom, "Click or Drop")
        
        painter.end()
        
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