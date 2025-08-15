"""
Export Video Dialog - Allows users to export timeline items as videos
"""
import asyncio
import os
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, 
    QRadioButton, QSpinBox, QPushButton, QLabel, 
    QProgressBar, QFileDialog, QMessageBox, QWidget, QDialog
)
from PySide6.QtCore import Qt, Signal, QThread, QRunnable, QThreadPool, QObject
from PySide6.QtGui import QDesktopServices
from qasync import asyncSlot

from utils.ffmpeg_utils import images_to_video, merge_videos, check_ffmpeg, ensure_ffmpeg

from app.ui.base_widget import BaseWidget


class ExportWorkerSignals(QObject):
    """Signals for the export worker"""
    progress = Signal(int)  # Progress percentage (0-100)
    finished = Signal()
    error = Signal(str)


import re

class ExportWorker(QRunnable):
    """Worker thread for video export operations"""
    def __init__(self, export_params):
        super().__init__()
        self.export_params = export_params
        self.signals = ExportWorkerSignals()
    
    def _get_unique_filename(self, base_path):
        """Generate a unique filename by adding a numeric suffix if the file already exists"""
        if not os.path.exists(base_path):
            return base_path
        
        directory = os.path.dirname(base_path)
        filename = os.path.basename(base_path)
        name, ext = os.path.splitext(filename)
        
        # Look for pattern "name (number).ext" or "name_number.ext"
        counter = 1
        while True:
            # Try format: name (1).ext
            new_filename = f"{name} ({counter}){ext}"
            new_path = os.path.join(directory, new_filename)
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    def run(self):
        import asyncio
        # Run the async function in a new event loop
        try:
            # Import here to avoid circular imports
            from utils.ffmpeg_utils import images_to_video, merge_videos, ensure_ffmpeg
            
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self._async_run())
            finally:
                loop.close()
        except Exception as e:
            self.signals.error.emit(str(e))

    async def _async_run(self):
        """Internal async run method"""
        # Import here to avoid circular imports
        from utils.ffmpeg_utils import images_to_video, merge_videos, ensure_ffmpeg
        
        # Ensure FFmpeg is available
        if not await ensure_ffmpeg():
            self.signals.error.emit("FFmpeg is required but could not be installed.")
            return

        # Extract parameters
        timeline_items = self.export_params['timeline_items']
        export_mode = self.export_params['export_mode']
        items_per_video = self.export_params['items_per_video']
        output_dir = self.export_params['output_dir']
        fps = self.export_params['fps']
        
        if export_mode == 'all_as_one':
            # Export all items as a single video
            await self._export_all_as_one(timeline_items, output_dir, fps)
        elif export_mode == 'grouped':
            # Export in groups of N items
            await self._export_grouped(timeline_items, items_per_video, output_dir, fps)
        elif export_mode == 'individual':
            # Export each item as a separate video
            await self._export_individual(timeline_items, output_dir, fps)
            
        self.signals.finished.emit()

    async def _export_all_as_one(self, timeline_items, output_dir, fps):
        """Export all timeline items as a single video"""
        # Collect all media paths, prioritizing video over image for each item
        all_media_paths = []
        for item in timeline_items:
            # Prioritize video over image for each timeline item
            video_path = item.get_video_path()
            image_path = item.get_image_path()
            
            # If video exists and is valid, use it
            if video_path and os.path.exists(video_path):
                all_media_paths.append(video_path)
            # If video doesn't exist but image does, use the image (to be converted)
            elif image_path and os.path.exists(image_path):
                all_media_paths.append(image_path)
            # If neither exists, skip this item (don't add anything to the list)
        
        if not all_media_paths:
            self.signals.error.emit("No media items found to export.")
            return

        base_output_path = os.path.join(output_dir, "timeline_export_all.mp4")
        output_path = self._get_unique_filename(base_output_path)
        
        # If all items are images, convert to video
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        all_images = all(path.lower().endswith(image_extensions) for path in all_media_paths)
        
        if all_images:
            success = await images_to_video(all_media_paths, output_path, duration_per_image=1.0, fps=fps)
        else:
            # Some are images, some are videos - need to handle differently
            # For now, just merge videos if they exist
            video_paths = [p for p in all_media_paths if not p.lower().endswith(image_extensions)]
            if video_paths:
                success = await merge_videos(video_paths, output_path)
            else:
                success = await images_to_video(all_media_paths, output_path, duration_per_image=1.0, fps=fps)
        
        if not success:
            self.signals.error.emit("Failed to create video from timeline items.")

    async def _export_grouped(self, timeline_items, items_per_video, output_dir, fps):
        """Export timeline items in groups of N"""
        # Group timeline items
        groups = []
        for i in range(0, len(timeline_items), items_per_video):
            group = timeline_items[i:i + items_per_video]
            groups.append(group)
        
        total_groups = len(groups)
        
        for idx, group in enumerate(groups):
            # Collect media paths for this group, prioritizing video over image for each item
            group_media_paths = []
            for item in group:
                # Prioritize video over image for each timeline item
                video_path = item.get_video_path()
                image_path = item.get_image_path()
                
                # If video exists and is valid, use it
                if video_path and os.path.exists(video_path):
                    group_media_paths.append(video_path)
                # If video doesn't exist but image does, use the image (to be converted)
                elif image_path and os.path.exists(image_path):
                    group_media_paths.append(image_path)
                # If neither exists, skip this item (don't add anything to the list)
            
            if not group_media_paths:
                continue
            
            base_output_path = os.path.join(output_dir, f"timeline_group_{idx+1:03d}.mp4")
            output_path = self._get_unique_filename(base_output_path)
            
            # Determine if all are images
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
            all_images = all(path.lower().endswith(image_extensions) for path in group_media_paths)
            
            if all_images:
                success = await images_to_video(group_media_paths, output_path, duration_per_image=1.0, fps=fps)
            else:
                video_paths = [p for p in group_media_paths if not p.lower().endswith(image_extensions)]
                if video_paths:
                    success = await merge_videos(video_paths, output_path)
                else:
                    success = await images_to_video(group_media_paths, output_path, duration_per_image=1.0, fps=fps)
            
            if not success:
                self.signals.error.emit(f"Failed to create video for group {idx+1}")
                return
            
            # Update progress
            progress = int((idx + 1) / total_groups * 100)
            self.signals.progress.emit(progress)

    async def _export_individual(self, timeline_items, output_dir, fps):
        """Export each timeline item as a separate video"""
        total_items = len(timeline_items)
        
        for idx, item in enumerate(timeline_items):
            media_path = None
            video_path = item.get_video_path()
            image_path = item.get_image_path()
            
            # Prioritize video over image for each timeline item
            # If video exists and is valid, use it
            if video_path and os.path.exists(video_path):
                media_path = video_path
            # If video doesn't exist but image does, use the image (to be converted)
            elif image_path and os.path.exists(image_path):
                media_path = image_path
            # If neither exists, skip this item
            else:
                continue  # Skip this timeline item if neither video nor image exists
            
            # For images, create a short video; for videos, copy or process
            if media_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                base_output_path = os.path.join(output_dir, f"item_{item.get_timeline_index():03d}.mp4")
                output_path = self._get_unique_filename(base_output_path)
                success = await images_to_video([media_path], output_path, duration_per_image=2.0, fps=fps)
            else:
                # For existing videos, we could copy or process them
                # For now, just copy the video to the output directory with new naming
                base_output_path = os.path.join(output_dir, f"item_{item.get_timeline_index():03d}_video.mp4")
                output_path = self._get_unique_filename(base_output_path)
                # This would require a video copy function - using merge_videos with single video
                success = await merge_videos([media_path], output_path, codec='copy')
            
            if not success:
                self.signals.error.emit(f"Failed to process item {idx+1}")
                return
            
            # Update progress
            progress = int((idx + 1) / total_items * 100)
            self.signals.progress.emit(progress)


class ExportDialog(BaseWidget):
    """Export dialog for timeline items"""
    
    def __init__(self, workspace):
        super().__init__(workspace)
        self.setObjectName("ExportDialog")
        
        # Store reference to workspace to get timeline
        self.workspace = workspace
        
        # Load saved directory from config or use default
        self.last_export_dir = self.workspace.get_project().config.get('last_export_dir', os.path.expanduser("~"))
        
        self.setup_ui()
        self.connect_signals()
    
    @staticmethod
    def show_dialog(workspace):
        """Show export dialog as modal dialog"""
        # Create a new instance of the widget for the dialog
        export_widget = ExportDialog(workspace)
        
        dialog = QDialog()
        dialog.setWindowTitle("Export Timeline")
        dialog.setModal(True)
        dialog.resize(500, 500)
        
        # Apply application styles (it should inherit automatically with QApplication)
        layout = QVBoxLayout(dialog)
        layout.addWidget(export_widget)
        
        result = dialog.exec()
        return result, export_widget
        
    def setup_ui(self):
        """Setup the UI for the export dialog"""
        # Don't set window properties directly on BaseWidget
        # Instead, we'll handle dialog behavior through a parent QDialog when shown
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Export mode selection
        mode_group = QGroupBox("Export Mode")
        mode_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 1ex;
                padding-top: 12px;
                padding-left: 6px;
                padding-right: 6px;
                padding-bottom: 8px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px 0 6px;
                color: #495057;
            }
        """)
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(8)
        
        # Radio buttons for export modes
        self.export_all_radio = QRadioButton("Export all items as one video")
        self.export_all_radio.setChecked(True)  # Default selection
        self.export_all_radio.setStyleSheet("""
            QRadioButton {
                font-size: 12px;
                padding: 6px;
                border-radius: 3px;
                margin: 2px;
            }
            QRadioButton:hover {
                background-color: #e9ecef;
            }
        """)
        
        self.export_grouped_radio = QRadioButton("Export every N items as a video")
        self.export_grouped_radio.setStyleSheet("""
            QRadioButton {
                font-size: 12px;
                padding: 6px;
                border-radius: 3px;
                margin: 2px;
            }
            QRadioButton:hover {
                background-color: #e9ecef;
            }
        """)
        self.export_grouped_layout = QHBoxLayout()
        items_per_video_label = QLabel("Items per video:")
        items_per_video_label.setStyleSheet("font-weight: bold; color: #495057; min-width: 110px;")
        self.export_grouped_layout.addWidget(items_per_video_label)
        self.items_per_video_spin = QSpinBox()
        self.items_per_video_spin.setRange(1, 100)
        self.items_per_video_spin.setValue(10)
        self.items_per_video_spin.setStyleSheet("""
            QSpinBox {
                padding: 4px;
                border: 1px solid #ced4da;
                border-radius: 3px;
                min-width: 70px;
                background-color: #ffffff;
                selection-background-color: #4e73df;
            }
            QSpinBox:focus {
                border: 1px solid #4e73df;
                outline: none;
            }
        """)
        self.export_grouped_layout.addWidget(self.items_per_video_spin)
        self.export_grouped_layout.addStretch()
        
        self.export_individual_radio = QRadioButton("Export each item individually")
        self.export_individual_radio.setStyleSheet("""
            QRadioButton {
                font-size: 12px;
                padding: 6px;
                border-radius: 3px;
                margin: 2px;
            }
            QRadioButton:hover {
                background-color: #e9ecef;
            }
        """)
        
        mode_layout.addWidget(self.export_all_radio)
        mode_layout.addWidget(self.export_grouped_radio)
        mode_layout.addLayout(self.export_grouped_layout)
        mode_layout.addWidget(self.export_individual_radio)
        
        layout.addWidget(mode_group)
        
        # Video settings
        settings_group = QGroupBox("Video Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 1ex;
                padding-top: 12px;
                padding-left: 6px;
                padding-right: 6px;
                padding-bottom: 8px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px 0 6px;
                color: #495057;
            }
        """)
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(8)
        
        fps_layout = QHBoxLayout()
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet("font-weight: bold; color: #495057; min-width: 110px;")
        fps_layout.addWidget(fps_label)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(30)
        self.fps_spin.setStyleSheet("""
            QSpinBox {
                padding: 4px;
                border: 1px solid #ced4da;
                border-radius: 3px;
                min-width: 70px;
                background-color: #ffffff;
                selection-background-color: #4e73df;
            }
            QSpinBox:focus {
                border: 1px solid #4e73df;
                outline: none;
            }
        """)
        fps_layout.addWidget(self.fps_spin)
        fps_layout.addStretch()
        settings_layout.addLayout(fps_layout)
        
        layout.addWidget(settings_group)
        
        # Output directory selection
        output_group = QGroupBox("Output Directory")
        output_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 1ex;
                padding-top: 12px;
                padding-left: 6px;
                padding-right: 6px;
                padding-bottom: 8px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px 0 6px;
                color: #495057;
            }
        """)
        output_layout = QVBoxLayout(output_group)
        output_layout.setSpacing(8)
        
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Directory:")
        dir_label.setStyleSheet("font-weight: bold; color: #495057; min-width: 110px;")
        dir_layout.addWidget(dir_label)
        self.output_dir_label = QLabel(self.last_export_dir)
        self.output_dir_label.setWordWrap(True)
        self.output_dir_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #ced4da;
                border-radius: 3px;
                padding: 5px;
                color: #495057;
                min-height: 20px;
            }
        """)
        dir_layout.addWidget(self.output_dir_label)
        
        # Add both browse and save as buttons
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #1cc88a;
                color: white;
                border: none;
                padding: 6px 8px;
                border-radius: 3px;
                font-weight: bold;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #17a279;
            }
            QPushButton:pressed {
                background-color: #148966;
            }
        """)
        dir_layout.addWidget(self.browse_button)
        
        self.save_as_button = QPushButton("Save As...")
        self.save_as_button.setStyleSheet("""
            QPushButton {
                background-color: #36b9cc;
                color: white;
                border: none;
                padding: 6px 8px;
                border-radius: 3px;
                font-weight: bold;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #2c97a8;
            }
            QPushButton:pressed {
                background-color: #268490;
            }
        """)
        dir_layout.addWidget(self.save_as_button)
        output_layout.addLayout(dir_layout)
        
        layout.addWidget(output_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: #e9ecef;
                text-align: center;
                font-weight: bold;
                height: 16px;
            }
            QProgressBar::chunk {
                background-color: #4e73df;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e74a3b;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #d13a2b;
            }
            QPushButton:pressed {
                background-color: #b92c1f;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        self.export_button = QPushButton("Export")
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #36b9cc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 70px;
                margin-left: 8px;
            }
            QPushButton:hover {
                background-color: #2c97a8;
            }
            QPushButton:pressed {
                background-color: #268490;
            }
        """)
        button_layout.addWidget(self.export_button)
        layout.addLayout(button_layout)
        
        # Initially disable grouped options
        self._toggle_grouped_options()

    def connect_signals(self):
        """Connect UI signals"""
        self.export_grouped_radio.toggled.connect(self._toggle_grouped_options)
        self.browse_button.clicked.connect(self._browse_directory)
        self.save_as_button.clicked.connect(self._save_as_directory)
        self.export_button.clicked.connect(self._start_export)
        self.cancel_button.clicked.connect(self.close)

    def _toggle_grouped_options(self):
        """Toggle visibility of grouped export options"""
        is_grouped = self.export_grouped_radio.isChecked()
        self.items_per_video_spin.setEnabled(is_grouped)
        for widget in self.export_grouped_layout.parentWidget().children():
            if hasattr(widget, 'setEnabled'):
                widget.setEnabled(is_grouped)

    def _browse_directory(self):
        """Open directory browser dialog"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            self.last_export_dir
        )
        
        if directory:
            self.last_export_dir = directory
            self.output_dir_label.setText(directory)
    
    def _save_as_directory(self):
        """Open save as dialog to select export directory"""
        # Use getSaveFileName but we'll just use the directory part
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Exported Video",
            os.path.join(self.last_export_dir, "exported_video.mp4"),
            "Video Files (*.mp4 *.avi *.mov);;All Files (*)"
        )
        
        if file_path:
            # Extract directory from the file path
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            
            # Update the export directory
            self.last_export_dir = directory
            self.output_dir_label.setText(directory)
            
            # Store the desired filename base for use during export
            self.desired_export_filename = os.path.splitext(filename)[0]  # Without extension

    def _start_export(self):
        """Start the export process"""
        # Validate export directory
        if not os.path.exists(self.last_export_dir):
            QMessageBox.warning(self, "Warning", "Export directory does not exist!")
            return
        
        # Disable UI during export
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Get timeline items
        timeline = self.workspace.get_project().get_timeline()
        timeline_items = timeline.get_items()  # Assuming this returns items in order
        
        if not timeline_items:
            QMessageBox.warning(self, "Warning", "No timeline items to export!")
            self._set_ui_enabled(True)
            self.progress_bar.setVisible(False)
            return
        
        # Determine export mode
        if self.export_all_radio.isChecked():
            export_mode = 'all_as_one'
        elif self.export_grouped_radio.isChecked():
            export_mode = 'grouped'
        else:
            export_mode = 'individual'
        
        # Prepare export parameters
        export_params = {
            'timeline_items': timeline_items,
            'export_mode': export_mode,
            'items_per_video': self.items_per_video_spin.value(),
            'output_dir': self.last_export_dir,
            'fps': self.fps_spin.value()
        }
        
        # Save the last export directory
        project = self.workspace.get_project()
        project.update_config('last_export_dir', self.last_export_dir)
        
        # Start the export worker
        self.export_worker = ExportWorker(export_params)
        
        # Connect worker signals
        self.export_worker.signals.progress.connect(self._update_progress)
        self.export_worker.signals.finished.connect(self._export_finished)
        self.export_worker.signals.error.connect(self._export_error)
        
        # Run the worker
        self._run_worker()

    def _run_worker(self):
        """Run the export worker using QThreadPool"""
        # Import here to avoid circular imports at module level
        from PySide6.QtCore import QThreadPool
        
        # Get the global thread pool and start the worker
        pool = QThreadPool.globalInstance()
        pool.start(self.export_worker)

    def _update_progress(self, value):
        """Update the progress bar"""
        self.progress_bar.setValue(value)

    def _export_finished(self):
        """Handle export completion"""

        # Open the export directory in the system file explorer
        export_dir = self.last_export_dir
        if os.path.exists(export_dir):
            QDesktopServices.openUrl(f"file://{export_dir}")
        
        self._set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.close()

    def _export_error(self, error_msg):
        """Handle export error"""
        QMessageBox.critical(self, "Error", f"Export failed: {error_msg}")
        self._set_ui_enabled(True)
        self.progress_bar.setVisible(False)

    def _set_ui_enabled(self, enabled):
        """Enable/disable UI elements"""
        self.export_all_radio.setEnabled(enabled)
        self.export_grouped_radio.setEnabled(enabled)
        self.export_individual_radio.setEnabled(enabled)
        self.items_per_video_spin.setEnabled(enabled and self.export_grouped_radio.isChecked())
        self.fps_spin.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)
        self.export_button.setEnabled(enabled)
        self.cancel_button.setEnabled(enabled)