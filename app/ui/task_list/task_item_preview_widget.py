import os
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QScrollArea, QFrame, QTextEdit
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from utils.i18n_utils import tr


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
        
        # Set a dark theme style
        self.setStyleSheet("""
            QWidget {
                background-color: #323436;
                border: 2px solid #505254;
                border-radius: 8px;
            }
        """)
        
        # Create the layout for the preview panel
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title label
        self.preview_title = QLabel()
        self.preview_title.setStyleSheet("""
            QLabel {
                color: #E1E1E1;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(self.preview_title)
        
        # Preview content area
        self.preview_content = QScrollArea()
        self.preview_content.setStyleSheet("""
            QScrollArea {
                background-color: #292b2e;
                border: 1px solid #505254;
                border-radius: 4px;
            }
        """)
        self.preview_content.setWidgetResizable(True)
        
        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(5)
        
        self.preview_content.setWidget(self.content_widget)
        layout.addWidget(self.preview_content)
        
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

        # Set title
        self.preview_title.setText(f"{self.task.title} [{self.task.tool}-{self.task.model}]")
        
        # Clear previous content
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        
        # Look for result files in the task directory
        result_files = []
        if os.path.exists(self.task.path):
            for filename in os.listdir(self.task.path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.avi', '.mov', '.webm')):
                    result_files.append(os.path.join(self.task.path, filename))
        
        # Add labels and preview widgets for each result file
        for filepath in result_files:
            filename = os.path.basename(filepath)
            label = QLabel(filename)
            label.setStyleSheet("color: #E1E1E1; font-size: 12px;")
            self.content_layout.addWidget(label)
            
            # If it's an image, show a preview
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                try:
                    pixmap = QPixmap(filepath)
                    if not pixmap.isNull():
                        # Scale the image to fit while maintaining aspect ratio
                        scaled_pixmap = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        img_label = QLabel()
                        img_label.setPixmap(scaled_pixmap)
                        img_label.setAlignment(Qt.AlignCenter)
                        img_label.setStyleSheet("border: 1px solid #505254; border-radius: 4px;")
                        self.content_layout.addWidget(img_label)
                except Exception as e:
                    error_label = QLabel(f"Error loading image: {str(e)}")
                    error_label.setStyleSheet("color: #ff6b6b; font-size: 10px;")
                    self.content_layout.addWidget(error_label)
            
            # If it's a video, show a video player
            elif filename.lower().endswith(('.mp4', '.avi', '.mov', '.webm')):
                # Create video player components
                video_widget = QVideoWidget()
                video_widget.setFixedSize(250, 250)
                video_widget.setStyleSheet("border: 1px solid #505254; border-radius: 4px;")
                
                media_player = QMediaPlayer()
                audio_output = QAudioOutput()
                media_player.setAudioOutput(audio_output)
                media_player.setVideoOutput(video_widget)
                
                # Set the video source
                url = QUrl.fromLocalFile(filepath)
                media_player.setSource(url)
                
                # Create play/pause button
                play_button = QPushButton("▶")
                play_button.setFixedSize(30, 30)
                play_button.setStyleSheet("""
                    QPushButton {
                        background-color: #5a6e7f;
                        color: white;
                        border: none;
                        border-radius: 15px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #788da2;
                    }
                """)
                
                # Store references to prevent garbage collection
                # Add custom attributes to widget to store references
                video_widget._media_player = media_player
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
                
                # Create a container for the video widget and play button
                container_widget = QWidget()
                container_layout = QVBoxLayout(container_widget)
                container_layout.setContentsMargins(0, 0, 0, 0)
                
                # Add video widget to the layout
                container_layout.addWidget(video_widget)
                
                # Create a centered play button layout
                button_layout = QHBoxLayout()
                button_layout.addStretch()
                button_layout.addWidget(play_button)
                button_layout.addStretch()
                container_layout.addLayout(button_layout)
                
                self.content_layout.addWidget(container_widget)
                
                # Start playback automatically for preview
                media_player.play()