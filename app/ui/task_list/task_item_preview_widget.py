import os
import logging
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QScrollArea, QFrame, QTextEdit
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from utils.i18n_utils import tr
from utils.yaml_utils import load_yaml

logger = logging.getLogger(__name__)


class TaskItemPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task = None
        self.init_ui()

    def init_ui(self):
        # Set window properties
        self.setWindowTitle(tr("Task Preview"))
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)  # Make it a floating tool window without title bar
        
        self.setGeometry(0, 0, 300, 400)
        
        # Set a minimal dark theme style - only border, no background
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: 1px solid #505254;
                border-radius: 4px;
            }
        """)
        
        # Create the layout for the preview panel - minimal margins
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Preview content area - simplified, no scroll area wrapper
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignCenter)
        self.content_layout.setSpacing(2)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(self.content_widget)
        
        # Hide initially
        self.hide()

    def set_task(self, task):
        """Set the task to preview"""
        self.task = task
        self.populate_preview()

    def populate_preview(self):
        """Populate the preview panel with the selected task's content"""
        if not self.task:
            return
        
        # Clear previous content
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        
        # Get resource paths from task config.yaml
        result_files = []
        try:
            # Load task config
            task_config = load_yaml(self.task.config_path) or {}
            
            # Get project path to resolve relative resource paths
            project_path = None
            if hasattr(self.task, 'task_manager') and hasattr(self.task.task_manager, 'project'):
                project_path = self.task.task_manager.project.project_path
            
            # Try to get resources from config
            resources = task_config.get('resources', [])
            if resources:
                # Use resources list from config
                for resource_info in resources:
                    resource_path = resource_info.get('resource_path', '')
                    if resource_path and project_path:
                        absolute_path = os.path.join(project_path, resource_path)
                        if os.path.exists(absolute_path):
                            result_files.append(absolute_path)
            else:
                # Fallback to individual resource paths for backward compatibility
                image_path = task_config.get('image_resource_path', '')
                video_path = task_config.get('video_resource_path', '')
                
                if image_path and project_path:
                    absolute_path = os.path.join(project_path, image_path)
                    if os.path.exists(absolute_path):
                        result_files.append(absolute_path)
                
                if video_path and project_path:
                    absolute_path = os.path.join(project_path, video_path)
                    if os.path.exists(absolute_path):
                        result_files.append(absolute_path)
            
            # If no resources found in config, fallback to scanning task directory
            if not result_files and os.path.exists(self.task.path):
                for filename in os.listdir(self.task.path):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.avi', '.mov', '.webm')):
                        result_files.append(os.path.join(self.task.path, filename))
        except Exception as e:
            logger.error(f"Error loading resources from task config: {e}")
            # Fallback to scanning task directory
            if os.path.exists(self.task.path):
                for filename in os.listdir(self.task.path):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.avi', '.mov', '.webm')):
                        result_files.append(os.path.join(self.task.path, filename))
        
        # Maximum preview size
        max_preview_size = 280
        
        # Add preview widgets for each result file
        for filepath in result_files:
            filename = os.path.basename(filepath)
            
            # If it's an image, show a preview
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                try:
                    pixmap = QPixmap(filepath)
                    if not pixmap.isNull():
                        # Calculate scaled size maintaining aspect ratio
                        original_size = pixmap.size()
                        if original_size.width() > max_preview_size or original_size.height() > max_preview_size:
                            scaled_pixmap = pixmap.scaled(
                                max_preview_size, max_preview_size, 
                                Qt.KeepAspectRatio, Qt.SmoothTransformation
                            )
                        else:
                            scaled_pixmap = pixmap
                        
                        img_label = QLabel()
                        img_label.setPixmap(scaled_pixmap)
                        img_label.setAlignment(Qt.AlignCenter)
                        img_label.setStyleSheet("background-color: transparent;")
                        self.content_layout.addWidget(img_label)
                except Exception as e:
                    logger.error(f"Error loading image {filepath}: {e}")
            
            # If it's a video, show a video player
            elif filename.lower().endswith(('.mp4', '.avi', '.mov', '.webm')):
                # Create video player components
                video_widget = QVideoWidget()
                # Calculate video widget size maintaining aspect ratio
                # For now, use a fixed reasonable size, but could be improved to read video dimensions
                video_widget.setMinimumSize(max_preview_size, max_preview_size)
                video_widget.setMaximumSize(max_preview_size, max_preview_size)
                video_widget.setStyleSheet("background-color: #000000;")
                
                media_player = QMediaPlayer()
                audio_output = QAudioOutput()
                media_player.setAudioOutput(audio_output)
                media_player.setVideoOutput(video_widget)
                
                # Set the video source
                url = QUrl.fromLocalFile(filepath)
                media_player.setSource(url)
                
                # Store references to prevent garbage collection
                video_widget._media_player = media_player
                
                # Create play/pause button overlay
                play_button = QPushButton("▶")
                play_button.setFixedSize(40, 40)
                play_button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(90, 110, 127, 200);
                        color: white;
                        border: none;
                        border-radius: 20px;
                        font-weight: bold;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background-color: rgba(120, 141, 162, 220);
                    }
                """)
                
                video_widget._play_button = play_button
                
                # Connect play button to toggle playback
                def toggle_playback():
                    if media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                        media_player.pause()
                        play_button.setText("▶")
                    else:
                        media_player.play()
                        play_button.setText("⏸")
                
                play_button.clicked.connect(toggle_playback)
                
                # Update button when playback state changes
                def on_playback_state_changed(state):
                    if state == QMediaPlayer.PlaybackState.PlayingState:
                        play_button.setText("⏸")
                    else:
                        play_button.setText("▶")
                
                media_player.playbackStateChanged.connect(on_playback_state_changed)
                
                # Create a container for the video widget with control button
                container_widget = QWidget()
                container_layout = QVBoxLayout(container_widget)
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setSpacing(2)
                container_layout.setAlignment(Qt.AlignCenter)
                
                # Add video widget to the layout
                container_layout.addWidget(video_widget)
                
                # Add play button below video (centered, compact)
                button_layout = QHBoxLayout()
                button_layout.addStretch()
                button_layout.addWidget(play_button)
                button_layout.addStretch()
                container_layout.addLayout(button_layout)
                
                self.content_layout.addWidget(container_widget)
                
                # Start playback automatically for preview
                media_player.play()
        
        # Adjust window size based on content
        self.adjustSize()