"""Resource preview widget for displaying resource details and thumbnails."""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame,
    QGridLayout
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap

from app.data.resource import Resource


class ResourcePreview(QWidget):
    """Widget for previewing selected resource with metadata."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_resource = None
        self.project_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the preview UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Preview area
        self.preview_frame = QFrame(self)
        self.preview_frame.setFrameStyle(QFrame.StyledPanel)
        self.preview_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #3c3f41;
                border-radius: 4px;
            }
        """)
        
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        
        # Preview image label
        self.preview_label = QLabel("No resource selected", self.preview_frame)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(120)
        self.preview_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
            }
        """)
        preview_layout.addWidget(self.preview_label)
        
        layout.addWidget(self.preview_frame)
        
        # Metadata area
        self.metadata_frame = QFrame(self)
        self.metadata_frame.setFrameStyle(QFrame.StyledPanel)
        self.metadata_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #3c3f41;
                border-radius: 4px;
            }
        """)
        
        metadata_layout = QVBoxLayout(self.metadata_frame)
        metadata_layout.setContentsMargins(10, 10, 10, 10)
        metadata_layout.setSpacing(5)
        
        # Metadata title
        title_label = QLabel("Resource Information", self.metadata_frame)
        title_label.setStyleSheet("""
            QLabel {
                color: #E1E1E1;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        metadata_layout.addWidget(title_label)
        
        # Metadata grid
        self.metadata_grid = QGridLayout()
        self.metadata_grid.setSpacing(5)
        self.metadata_grid.setColumnStretch(1, 1)
        
        # Create metadata labels
        self.metadata_labels = {}
        metadata_fields = [
            ("Name:", "name"),
            ("Type:", "type"),
            ("Size:", "size"),
            ("Source:", "source"),
            ("Created:", "created"),
            ("Dimensions:", "dimensions"),
        ]
        
        for i, (label_text, field_key) in enumerate(metadata_fields):
            # Label
            label = QLabel(label_text, self.metadata_frame)
            label.setStyleSheet("color: #888888; font-size: 11px;")
            self.metadata_grid.addWidget(label, i, 0, Qt.AlignTop)
            
            # Value
            value_label = QLabel("—", self.metadata_frame)
            value_label.setWordWrap(True)
            value_label.setStyleSheet("color: #bbbbbb; font-size: 11px;")
            self.metadata_grid.addWidget(value_label, i, 1)
            self.metadata_labels[field_key] = value_label
        
        metadata_layout.addLayout(self.metadata_grid)
        metadata_layout.addStretch()
        
        layout.addWidget(self.metadata_frame, 1)
    
    def set_resource(self, resource: Resource, project_path: str):
        """
        Display preview for the given resource.
        
        Args:
            resource: Resource object to preview
            project_path: Absolute path to project directory
        """
        self.current_resource = resource
        self.project_path = project_path
        
        if not resource:
            self.clear_preview()
            return
        
        # Update preview image
        self._update_preview_image()
        
        # Update metadata
        self._update_metadata()
    
    def _update_preview_image(self):
        """Update the preview image/icon."""
        if not self.current_resource:
            return
        
        resource_path = self.current_resource.get_absolute_path(self.project_path)
        
        # Try to load image preview
        if self.current_resource.media_type == 'image' and os.path.exists(resource_path):
            try:
                pixmap = QPixmap(resource_path)
                if not pixmap.isNull():
                    # Scale to fit preview area
                    scaled_pixmap = pixmap.scaled(
                        QSize(180, 180),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.preview_label.setPixmap(scaled_pixmap)
                    self.preview_label.setText("")
                else:
                    self.preview_label.clear()
                    self.preview_label.setText(f"[{self.current_resource.media_type.upper()}]")
            except Exception as e:
                print(f"⚠️ Error loading preview: {e}")
                self.preview_label.clear()
                self.preview_label.setText(f"[Preview unavailable]")
        else:
            # Show media type icon
            self.preview_label.clear()
            media_type = self.current_resource.media_type.upper()
            self.preview_label.setText(f"[{media_type}]")
    
    def _update_metadata(self):
        """Update metadata display."""
        if not self.current_resource:
            return
        
        resource = self.current_resource
        
        # Name
        self.metadata_labels['name'].setText(resource.name)
        
        # Type
        self.metadata_labels['type'].setText(resource.media_type.capitalize())
        
        # Size
        size_text = self._format_size(resource.file_size)
        self.metadata_labels['size'].setText(size_text)
        
        # Source
        source_text = f"{resource.source_type}"
        if resource.source_id:
            source_text += f" ({resource.source_id[:8]}...)"
        self.metadata_labels['source'].setText(source_text)
        
        # Created
        from datetime import datetime
        try:
            created_date = datetime.fromisoformat(resource.created_at)
            created_text = created_date.strftime("%Y-%m-%d %H:%M")
        except:
            created_text = resource.created_at[:16]
        self.metadata_labels['created'].setText(created_text)
        
        # Dimensions (from metadata)
        dimensions_text = "—"
        if 'width' in resource.metadata and 'height' in resource.metadata:
            dimensions_text = f"{resource.metadata['width']} × {resource.metadata['height']}"
            if 'fps' in resource.metadata:
                dimensions_text += f" @ {resource.metadata['fps']:.1f} fps"
            elif 'duration' in resource.metadata:
                duration = resource.metadata['duration']
                dimensions_text += f" ({self._format_duration(duration)})"
        self.metadata_labels['dimensions'].setText(dimensions_text)
    
    def clear_preview(self):
        """Clear the preview display."""
        self.current_resource = None
        self.preview_label.clear()
        self.preview_label.setText("No resource selected")
        
        # Reset metadata
        for value_label in self.metadata_labels.values():
            value_label.setText("—")
    
    def _format_size(self, size_bytes):
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        return f"{size:.1f} {size_names[i]}"
    
    def _format_duration(self, seconds):
        """Format duration in seconds to readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if minutes < 60:
            return f"{minutes}m {secs}s"
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}h {minutes}m"
