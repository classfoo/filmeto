import os
import traceback

from PySide6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit
from qasync import asyncSlot

from app.data.task import TaskResult, TaskProgress
from app.data.timeline import TimelineItem
from app.plugins.models.comfy_ui.comfy_ui_model import ComfyUiModel
from app.spi.tool import BaseTool
from app.ui.base_widget import BaseTaskWidget
from utils.opencv_utils import extract_last_frame_opencv
from utils.i18n_utils import tr


class Image2Video(BaseTool,BaseTaskWidget):

    def __init__(self, workspace, editor=None):
        super(Image2Video,self).__init__(workspace)
        self.setObjectName("tool_text_to_image")
        self.workspace = workspace
        self.workspace.connect_task_execute(self.execute)
        self.editor = editor
        self.start_frame_path = None
        self.end_frame_path = None

    def generate_image(self):
        self.workspace.submit_task(self.params())

    def params(self):
        timeline_index = self.workspace.get_project().get_timeline_index()
        timeline_item = self.workspace.get_project().get_timeline().get_item(timeline_index)
        input_image_path = timeline_item.get_image_path()
        return {
            "tool":"img2video",
            "model":"comfy_ui",
            "input_image_path":input_image_path,
            "prompt":self.editor.get_prompt(),
            "start_frame_path": self.start_frame_path,
            "end_frame_path": self.end_frame_path
        }

    def init_ui(self, canvas_editor):
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(6)
        title = QLabel(tr("Start/End Frames"))
        layout.addWidget(title)
        # Start frame row
        start_row = QWidget()
        start_layout = QHBoxLayout(start_row)
        start_layout.setContentsMargins(0,0,0,0)
        start_layout.setSpacing(4)
        start_edit = QLineEdit(); start_edit.setReadOnly(True)
        start_btn = QPushButton(tr("Start"))
        def on_pick_start():
            file_path, _ = QFileDialog.getOpenFileName(panel, tr("Select Start Frame"), "", "Images (*.png *.jpg *.jpeg)")
            if file_path:
                self.start_frame_path = file_path
                start_edit.setText(file_path)
        start_btn.clicked.connect(on_pick_start)
        start_layout.addWidget(start_edit, 1)
        start_layout.addWidget(start_btn)
        layout.addWidget(start_row)
        # End frame row
        end_row = QWidget()
        end_layout = QHBoxLayout(end_row)
        end_layout.setContentsMargins(0,0,0,0)
        end_layout.setSpacing(4)
        end_edit = QLineEdit(); end_edit.setReadOnly(True)
        end_btn = QPushButton(tr("End"))
        def on_pick_end():
            file_path, _ = QFileDialog.getOpenFileName(panel, tr("Select End Frame"), "", "Images (*.png *.jpg *.jpeg)")
            if file_path:
                self.end_frame_path = file_path
                end_edit.setText(file_path)
        end_btn.clicked.connect(on_pick_end)
        end_layout.addWidget(end_edit, 1)
        end_layout.addWidget(end_btn)
        layout.addWidget(end_row)
        canvas_editor.set_tool_panel(panel)

    # def on_timeline_switch(self,item:TimelineItem):
    #     # For img2video, show the video if exists, otherwise show image
    #     current_tool = item.get_config_value("current_tool")
    #     if current_tool != self.get_tool_name():
    #         return
    #     if not self.editor:
    #         return
    #
    #     video_path = item.get_video_path()
    #     if os.path.exists(video_path):
    #         self.editor.get_canvas_widget().switch_file(video_path)
    #     else:
    #         image_path = item.get_image_path()
    #         if os.path.exists(image_path):
    #             self.editor.get_canvas_widget().switch_file(image_path)
    #     return
    
    @classmethod
    def get_tool_name(cls):
        return "img2video"
    
    @classmethod
    def get_tool_icon(cls):
        return "\ue712"  # Image to video icon from iconfont.json
    
    @classmethod
    def get_tool_display_name(cls):
        return tr("Image to Video")
    
    def get_media_path(self, timeline_item):
        """Get media path for img2video tool"""
        # Check for video first, then image
        video_path = timeline_item.get_video_path()
        if os.path.exists(video_path):
            return video_path
        else:
            return timeline_item.get_image_path()
    
    @asyncSlot()
    async def execute(self, task):
        # Only process img2video tasks to avoid conflicts with other tools
        if task.tool != "img2video" and task.tool != "image2video":
            return  # Exit early if this is not an img2video task
            
        try:
            print(f"Processing img2video task: {task.options}")
            
            # Get the timeline
            timeline = self.workspace.get_project().get_timeline()

            # If we can't extract from path, try getting from options or workspace
            current_index = task.options.get('timeline_index', self.workspace.get_project().get_timeline_index())

            # Get the appropriate input image
            input_image_path = await self._get_image(task, timeline, current_index)
            
            # Continue with original image-to-video flow
            model = ComfyUiModel()
            progress = TaskProgress(task)
            result = await model.image2video(input_image_path, task.options['prompt'], task.path, progress)
            #刷新当前页面显示
            task_result = TaskResult(task, result)
            self.workspace.on_task_finished(task_result)
        except Exception as e:
            print(str(e))
            traceback.print_exc()

    async def _get_image(self, task, timeline, current_index):
        # Check if input image exists
        timeline_item = timeline.get_item(current_index)
        if timeline_item.get_config() is not None and timeline_item.get_config():
            input_image_path = task.options['input_image_path']
            return input_image_path
        # Get the previous timeline item (current_index - 1)
        prev_index = current_index - 1
        if prev_index >= 1:  # Timeline items start from index 1
            prev_item = timeline.get_item(prev_index)
            input_image_path = task.options['input_image_path']
            # Check if the previous item has a video file
            if os.path.exists(prev_item.get_video_path()):
                # Extract the last frame from the video using ffmpeg_utils
                video_path = prev_item.get_video_path()
                print(f"Getting image from video: {video_path}")

                # First, ensure ffmpeg is available
                print("Failed to extract or save the last frame from video using ffmpeg")
                # Try fallback method using OpenCV if available
                current_item_path = os.path.join(os.path.dirname(input_image_path), "image.png")
                opencv_result = extract_last_frame_opencv(video_path, current_item_path)
                if opencv_result and os.path.exists(opencv_result):
                    input_image_path = opencv_result
                    print(f"Saved last frame with OpenCV as: {input_image_path}")
                    # 刷新时间线显示复制过来的图片
                    # 获取当前时间线项并更新其显示
                    current_item = timeline.get_item(current_index)
                    # 发送信号更新UI显示
                    timeline.timeline_switch.send(current_item)
                else:
                    print("OpenCV fallback also failed to extract the frame")
            elif os.path.exists(prev_item.get_image_path()):
                # Copy the image from previous item
                prev_image_path = prev_item.get_image_path()
                print(f"Getting image from previous item: {prev_image_path}")

                # Copy to current item's directory
                current_item_path = os.path.join(os.path.dirname(input_image_path), "image.png")
                import shutil
                shutil.copy2(prev_image_path, current_item_path)
                input_image_path = current_item_path
                print(f"Copied image to: {input_image_path}")
                
                # 刷新时间线显示复制过来的图片
                # 获取当前时间线项并更新其显示
                current_item = timeline.get_item(current_index)
                # 发送信号更新UI显示
                timeline.timeline_switch.send(current_item)
            else:
                print(f"No image or video found in previous timeline item {prev_index}")
        else:
            print("No previous timeline item exists (at index 1)")

        # If the input image path is still not valid, raise an error
        if not os.path.exists(input_image_path):
            raise FileNotFoundError(f"Input image not found: {input_image_path}")

        print(f"Using input image: {input_image_path}")
        return input_image_path