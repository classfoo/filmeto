"""
Canvas layer component that provides drawing functionality for a single layer.
"""
from typing import Optional
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap, QCursor, QPainterPath

from app.data.layer import Layer
from PySide6.QtGui import QImage, QPixmap
from app.ui.canvas.canvas_pixmap import CanvasPixMap
from app.ui.drawing_tools import DrawingToolsWidget
from app.ui.drawing_tools.drawing_tool import DrawingTool

from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage
import cv2


class CanvasLayerWidget(QWidget):
    """
    Abstract base class for canvas layer widgets. Provides common geometry,
    scaling, mode handling, and centering behavior. Subclasses implement
    specific painting and interactions.
    """
    def __init__(self, canvas_widget, layer_id: int, layer: Layer, width: int, height: int, layer_x: int = 0,
                 layer_y: int = 0):
        super().__init__(canvas_widget)
        self.canvas_widget = canvas_widget
        self.layer_id = layer_id
        self.layer = layer
        self.layer_width = width
        self.layer_height = height
        self.layer_x = layer_x
        self.layer_y = layer_y
        self.scale_factor = 1.0
        # No longer using DrawingMode, but keeping this for compatibility during transition
        self.current_tool_id = 'pen'  # Default tool

        # General widget setup
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StaticContents, False)
        self.setVisible(True)
        self.on_canvas_resize(self.canvas_widget.width(), self.canvas_widget.height())
        self.show()

    def on_canvas_resize(self, canvas_width, canvas_height):
        width_scale = canvas_width / self.layer_width if self.layer_width > 0 else 1.0
        height_scale = canvas_height / self.layer_height if self.layer_height > 0 else 1.0
        scale_factor = min(width_scale, height_scale)
        self.set_scale_factor(scale_factor)
        widget_width = self.layer_width * scale_factor
        widget_height = self.layer_height * scale_factor
        self.setFixedSize(widget_width, widget_height)
        center_x = max(0, (canvas_width - widget_width) // 2)
        center_y = max(0, (canvas_height - widget_height) // 2)
        self.move(center_x, center_y)


    def set_scale_factor(self, scale: float):
        if scale <= 0:
            return
        self.scale_factor = scale
        self.setFixedSize(int(self.layer_width * self.scale_factor), int(self.layer_height * self.scale_factor))
        # Also update the canvas_pixmap scale factor if it exists
        if hasattr(self, 'canvas_pixmap'):
            self.canvas_pixmap.set_scale_factor(scale)
        self.update()

    def paintEvent(self, event):
        raise NotImplementedError("Subclasses must implement paintEvent")

    def clear_draw(self):
        pass


class CanvasImageLayerWidget(CanvasLayerWidget):
    """
    A transparent widget representing a single layer that can be drawn on
    """

    def __init__(self, canvas_widget, layer_id: int, layer: Layer, width: int, height: int, layer_x: int = 0,
                 layer_y: int = 0):
        super().__init__(canvas_widget, layer_id, layer, width, height, layer_x, layer_y)
        self.canvas_widget = canvas_widget
        self.layer_id = layer_id
        self.layer = layer
        self.layer_width = width
        self.layer_height = height
        self.layer_x = layer_x  # X offset of the layer
        self.layer_y = layer_y  # Y offset of the layer
        self.scale_factor = 1.0  # Default scale
        
        # Initialize canvas_pixmap first to avoid AttributeError
        layer_path = layer.get_layer_path()
        layer_pixmap = QPixmap(layer_path)
        self.canvas_pixmap = CanvasPixMap(layer_pixmap)
        # Initialize the canvas_pixmap scale factor
        self.canvas_pixmap.set_scale_factor(self.scale_factor)

        self.setFixedSize(self.layer_width, self.layer_height)

        # Drawing properties
        self.drawing = False
        self.last_point = QPoint()

        # Drawing state
        self.current_path = QPainterPath()

        # Enable mouse tracking for better responsiveness
        self.setMouseTracking(True)

        # Make sure the widget can be transparent and receives mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # Ensure the widget can have children and is visible
        self.setAttribute(Qt.WidgetAttribute.WA_StaticContents, False)
        self.setVisible(True)
        self.on_canvas_resize(self.canvas_widget.width(), self.canvas_widget.height())
        self.show()

    def save_level_image(self):
        image_path = self.layer.get_layer_path()
        # Get the original pixmap from CanvasPixMap
        original_pixmap = self.canvas_pixmap.get_original_pixmap()
        original_pixmap.save(image_path)
        # Trigger layer change event through layer manager
        if self.layer.layer_manager:
            self.layer.layer_manager.save_layer(self.layer)

    def set_mode(self, mode):
        """Set the current drawing mode and update cursor"""
        self.current_tool_id = mode  # mode is now the tool ID

        # Update cursor based on the current tool's cursor
        drawing_tool = self.get_drawing_tool()
        if drawing_tool:
            cursor = drawing_tool.get_cursor()
            self.setCursor(cursor)

    def paintEvent(self, event):
        """Paint the layer contents"""
        painter = QPainter(self)
        # Get the scaled pixmap from CanvasPixMap for display
        scaled_pixmap = self.canvas_pixmap.get_scaled_pixmap()
        if scaled_pixmap:
            painter.drawPixmap(0, 0, scaled_pixmap)
        # Draw a visual border to distinguish the layer, especially when debugging
        if self.canvas_widget and self.canvas_widget.active_layer_id == self.layer_id:
            # Draw a red border for the active layer
            painter.setPen(QPen(QColor(255, 0, 0), 1))
            painter.drawRect(0, 0, self.width(), self.height())

    def get_drawing_tool(self) -> Optional[DrawingTool]:
        project = self.canvas_widget.workspace.get_project()
        drawing = project.get_drawing()
        drawing_tools = DrawingToolsWidget.get_instance()
        tool = drawing_tools.get_tool(drawing.current_tool)
        
        # Apply the latest configuration from the project to the tool
        if tool and drawing.current_tool in drawing.tool_settings:
            tool_config = drawing.tool_settings[drawing.current_tool]
            tool.set_config(tool_config)
        
        return tool

    def mousePressEvent(self, event):
        """Handle mouse press events directly on the layer"""
        # Check if this layer is part of a canvas and is the active (topmost) layer before processing
        if (not self.canvas_widget or
                self.canvas_widget.active_layer_id != self.layer_id):
            event.ignore()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # Get mouse position directly in the layer's coordinate system
            mouse_pos = event.position().toPoint()
            # Default to pen mode for any other mode
            self.drawing = True
            self.last_point = mouse_pos

            # Draw on the layer with a short line to ensure visibility
            next_point = QPoint(mouse_pos.x(), mouse_pos.y() + 1)
            self.draw_on_layer(mouse_pos, next_point)

    def mouseMoveEvent(self, event):
        """Handle mouse move events for drawing"""
        # Check if this layer is part of a canvas and is the active (topmost) layer before processing
        if (not self.canvas_widget or
                self.canvas_widget.active_layer_id != self.layer_id):
            event.ignore()
            return
        drawing_tool = self.get_drawing_tool()
        cursor = drawing_tool.get_cursor()
        self.setCursor(cursor)
        # Get mouse position directly in the layer's coordinate system
        mouse_pos = event.position().toPoint()
        # Handle different drawing modes
        if self.canvas_widget and self.drawing and event.buttons() & Qt.MouseButton.LeftButton:
            self.draw_on_layer(self.last_point, mouse_pos)
            self.last_point = mouse_pos

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        # Check if this layer is part of a canvas and is the active (topmost) layer before processing
        if (not self.canvas_widget or
                self.canvas_widget.active_layer_id != self.layer_id):
            event.ignore()
            return

        if self.drawing and event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            self.last_point = QPoint()
        self.save_level_image()


    def draw_on_layer(self, start_point: QPoint, end_point: QPoint):
        """Draw on this layer's pixmap using DrawingTool"""
        # Get the current drawing tool from project configuration
        drawing_tool = self.get_drawing_tool()

        if drawing_tool:
            # Use the drawing tool to paint on the original pixmap
            drawing_tool.paint(
                self.canvas_pixmap.original_pixmap,
                start_point,
                end_point,
                self.scale_factor
            )
            # Update the scaled pixmap after drawing
            self.canvas_pixmap.update_scaled_pixmap()

        # Update the region that changed
        update_rect = QRect(start_point, end_point).normalized()
        brush_size = getattr(self, 'brush_size', 20)
        update_rect.adjust(-brush_size, -brush_size, brush_size, brush_size)
        self.update(update_rect)

    def clear_draw(self):
        """Clear the drawing using CanvasPixMap"""
        self.canvas_pixmap.clear()
        self.update()


class CanvasVideoLayerWidget(CanvasLayerWidget):
    """
    Video layer implementation that previews and plays video via OpenCV frames
    rendered into the widget.
    """
    def __init__(self, canvas_widget, layer_id: int, layer: Layer, width: int, height: int, layer_x: int = 0,
                 layer_y: int = 0):
        super().__init__(canvas_widget, layer_id, layer, width, height, layer_x, layer_y)
        self.video_path = layer.get_layer_path()
        self.cap = cv2.VideoCapture(self.video_path) if self.video_path else None
        self.fps = 30
        if self.cap and self.cap.isOpened():
            fps_val = self.cap.get(cv2.CAP_PROP_FPS)
            if fps_val and fps_val > 0:
                self.fps = int(fps_val)
        self.timer = QTimer(self)
        self.timer.setInterval(int(1000 / max(1, self.fps)))
        self.timer.timeout.connect(self._update_frame)
        self.current_frame_pixmap = None
        self.play()

    def play(self):
        if self.cap and self.cap.isOpened():
            self.timer.start()

    def pause(self):
        self.timer.stop()

    def stop(self):
        self.timer.stop()
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.current_frame_pixmap = None
        self.update()

    def _update_frame(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret:
                return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame_rgb.shape
        bytes_per_line = 3 * w
        qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        target_w = int(self.layer_width * self.scale_factor)
        target_h = int(self.layer_height * self.scale_factor)
        scaled_img = qimg.scaled(target_w, target_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.current_frame_pixmap = QPixmap.fromImage(scaled_img)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.current_frame_pixmap:
            painter.drawPixmap(0, 0, self.current_frame_pixmap)
        else:
            painter.fillRect(self.rect(), QColor(30, 30, 30))
        if self.canvas_widget and self.canvas_widget.active_layer_id == self.layer_id:
            painter.setPen(QPen(QColor(0, 128, 255), 1))
            painter.drawRect(0, 0, self.width(), self.height())

    def mousePressEvent(self, event):
        event.ignore()

    def mouseMoveEvent(self, event):
        event.ignore()

    def mouseReleaseEvent(self, event):
        event.ignore()