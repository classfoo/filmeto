"""
Canvas layer component that provides drawing functionality for a single layer.
"""
from typing import Optional
from enum import Enum
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap, QCursor, QPainterPath

from app.data.layer import Layer
from PySide6.QtGui import QImage, QPixmap
from app.ui.canvas.canvas_pixmap import CanvasPixMap

from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage
import cv2

class DrawingMode(Enum):
    """Enumeration for different drawing modes"""
    BRUSH = "brush"
    ERASER = "eraser"
    SELECT = "select"
    SHAPE = "shape"


class BrushType(Enum):
    """Enumeration for different brush types"""
    SOLID = Qt.PenStyle.SolidLine
    DASH = Qt.PenStyle.DashLine
    DOTTED = Qt.PenStyle.DotLine
    DASHDOT = Qt.PenStyle.DashDotLine
    DASHDOTDOT = Qt.PenStyle.DashDotLine


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
        self.current_mode = getattr(self.canvas_widget, 'current_mode', DrawingMode.BRUSH)

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

    def set_mode(self, mode):
        self.current_mode = mode
        if mode == DrawingMode.BRUSH:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif mode == DrawingMode.ERASER:
            eraser_pixmap = QPixmap(20, 20)
            eraser_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(eraser_pixmap)
            painter.setPen(QPen(QColor(Qt.GlobalColor.red), 2))
            painter.drawRect(0, 0, 19, 19)
            painter.end()
            eraser_cursor = QCursor(eraser_pixmap)
            self.setCursor(eraser_cursor)
        elif mode == DrawingMode.SELECT:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif mode == DrawingMode.SHAPE:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_scale_factor(self, scale: float):
        if scale <= 0:
            return
        self.scale_factor = scale
        self.setFixedSize(int(self.layer_width * self.scale_factor), int(self.layer_height * self.scale_factor))
        self.update()

    def paintEvent(self, event):
        raise NotImplementedError("Subclasses must implement paintEvent")

    def draw_shape(self, *args, **kwargs):
        pass

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

        self.setFixedSize(self.layer_width, self.layer_height)

        # Drawing properties
        self.drawing = False
        self.last_point = QPoint()

        # Drawing mode properties
        self.brush_color = QColor(Qt.GlobalColor.black)
        self.brush_size = 5
        self.brush_type = BrushType.SOLID

        # Drawing state for shape drawing
        self.drawing_shape = False
        self.shape_start_pos = QPoint()
        self.shape_end_pos = QPoint()

        # Drawing state
        self.current_path = QPainterPath()

        # Current drawing mode
        self.current_mode = self.canvas_widget.current_mode

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

    def set_mode(self, mode):
        """Set the current drawing mode and update cursor"""
        self.current_mode = mode

        # Update cursor based on mode
        if mode == DrawingMode.BRUSH:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif mode == DrawingMode.ERASER:
            # Create a custom eraser cursor
            eraser_pixmap = QPixmap(20, 20)
            eraser_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(eraser_pixmap)
            painter.setPen(QPen(QColor(Qt.GlobalColor.red), 2))
            painter.drawRect(0, 0, 19, 19)
            painter.end()
            eraser_cursor = QCursor(eraser_pixmap)
            self.setCursor(eraser_cursor)
        elif mode == DrawingMode.SELECT:
            self.setCursor(Qt.CursorShape.OpenHandCursor)  # Using OpenHand as pan cursor
        elif mode == DrawingMode.SHAPE:
            self.setCursor(Qt.CursorShape.PointingHandCursor)  # Using PointingHand as shape draw cursor

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

    def set_brush_properties(self, color: QColor, size: int, brush_type: BrushType):
        """Set the brush properties for this layer"""
        self.brush_color = color
        self.brush_size = size
        self.brush_type = brush_type
        # Update brush properties in CanvasPixMap
        self.canvas_pixmap.set_brush_properties(color, size)

    def draw_on_layer(self, start_point: QPoint, end_point: QPoint, mode: DrawingMode = DrawingMode.BRUSH):
        """Draw on this layer's pixmap using CanvasPixMap"""
        if mode == DrawingMode.BRUSH:
            # Ensure we're using a visible color for testing
            brush_color = self.brush_color if self.brush_color.alpha() > 0 else QColor(Qt.GlobalColor.black)
            # Use CanvasPixMap to draw the line
            self.canvas_pixmap.draw_line(start_point, end_point, brush_color, self.brush_size)
        elif mode == DrawingMode.ERASER:
            # Use CanvasPixMap to erase
            self.canvas_pixmap.draw_eraser(start_point, end_point, self.brush_size)
        
        # Instead of updating the entire widget, just update the region that changed
        # Calculate the bounding rect of the drawn line with some padding for the brush size
        update_rect = QRect(start_point, end_point).normalized()
        update_rect.adjust(-self.brush_size, -self.brush_size, self.brush_size, self.brush_size)
        self.update(update_rect)

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

            # Handle different drawing modes using switch-like structure
            if self.canvas_widget:
                mode = self.canvas_widget.current_mode
                if mode == DrawingMode.SHAPE:
                    # Handle shape drawing mode
                    self.drawing_shape = True
                    self.shape_start_pos = mouse_pos
                    self.shape_end_pos = mouse_pos
                elif mode == DrawingMode.SELECT:
                    # For select mode, we might want to implement selection logic
                    # For now, we just set a flag
                    self.drawing = True
                    self.last_point = mouse_pos
                elif mode == DrawingMode.BRUSH:
                    # Handle brush mode
                    self.drawing = True
                    self.last_point = mouse_pos

                    # Draw on the layer with a short line to ensure visibility
                    next_point = QPoint(mouse_pos.x(), mouse_pos.y() + 1)
                    self.draw_on_layer(mouse_pos, next_point, mode)
                elif mode == DrawingMode.ERASER:
                    # Handle eraser mode
                    self.drawing = True
                    self.last_point = mouse_pos

                    # Draw with eraser
                    next_point = QPoint(mouse_pos.x(), mouse_pos.y() + 1)
                    self.draw_on_layer(mouse_pos, next_point, mode)
                else:
                    # Default to brush mode for any other mode
                    self.drawing = True
                    self.last_point = mouse_pos

                    # Draw on the layer with a short line to ensure visibility
                    next_point = QPoint(mouse_pos.x(), mouse_pos.y() + 1)
                    self.draw_on_layer(mouse_pos, next_point, DrawingMode.BRUSH)
            else:
                # Default behavior when no canvas widget
                self.drawing = True
                self.last_point = mouse_pos
                self.draw_on_layer(mouse_pos, QPoint(mouse_pos.x(), mouse_pos.y() + 1))

    def mouseMoveEvent(self, event):
        """Handle mouse move events for drawing"""
        # Check if this layer is part of a canvas and is the active (topmost) layer before processing
        if (not self.canvas_widget or
                self.canvas_widget.active_layer_id != self.layer_id):
            event.ignore()
            return

        # Get mouse position directly in the layer's coordinate system
        mouse_pos = event.position().toPoint()

        # Handle different drawing modes
        if self.canvas_widget:
            mode = self.canvas_widget.current_mode
            if self.drawing_shape and mode == DrawingMode.SHAPE:
                # Update shape end position for visual feedback
                self.shape_end_pos = mouse_pos
                self.update()
            elif self.drawing and event.buttons() & Qt.MouseButton.LeftButton:
                # Handle continuous drawing for brush/eraser modes
                if mode in [DrawingMode.BRUSH, DrawingMode.ERASER]:
                    self.draw_on_layer(self.last_point, mouse_pos, mode)
                    self.last_point = mouse_pos
                elif mode == DrawingMode.SELECT:
                    # For select mode, we might implement panning or selection
                    # For now, just update the last point
                    self.last_point = mouse_pos
                else:
                    # Default to brush mode
                    self.draw_on_layer(self.last_point, mouse_pos, DrawingMode.BRUSH)
                    self.last_point = mouse_pos
            elif self.drawing:
                # Update cursor position even when not pressing the mouse button
                self.last_point = mouse_pos
        else:
            # Default behavior when no canvas widget
            if self.drawing and event.buttons() & Qt.MouseButton.LeftButton:
                self.draw_on_layer(self.last_point, mouse_pos)
                self.last_point = mouse_pos
            elif self.drawing:
                self.last_point = mouse_pos

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        # Check if this layer is part of a canvas and is the active (topmost) layer before processing
        if (not self.canvas_widget or
                self.canvas_widget.active_layer_id != self.layer_id):
            event.ignore()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            if self.drawing_shape and self.canvas_widget and self.canvas_widget.current_mode == DrawingMode.SHAPE:
                # Complete the shape drawing
                self.drawing_shape = False
                self.draw_shape_to_pixmap()
                self.shape_start_pos = QPoint()
                self.shape_end_pos = QPoint()
            elif self.drawing:
                # End drawing for brush/eraser/select modes
                self.drawing = False
                self.last_point = QPoint()
        self.save_level_image()

    def draw_shape_to_pixmap(self):
        """Draw the shape to the layer pixmap using CanvasPixMap"""
        if not self.canvas_widget:
            return

        # Use CanvasPixMap to draw a rectangle shape
        self.canvas_pixmap.draw_shape(
            'rectangle', 
            self.shape_start_pos, 
            self.shape_end_pos, 
            self.brush_color, 
            self.brush_size
        )
        self.update()

    def draw_shape(self, shape_start_pos, shape_end_pos, brush_color, brush_size, brush_type, scale_factor,
                   canvas_offset):
        """Draw a shape on this layer using CanvasPixMap"""
        # Map points to the layer's coordinate system
        adjusted_start = QPoint(int(shape_start_pos.x() / scale_factor),
                                int(shape_start_pos.y() / scale_factor)) + canvas_offset
        adjusted_end = QPoint(int(shape_end_pos.x() / scale_factor),
                              int(shape_end_pos.y() / scale_factor)) + canvas_offset
        # Use CanvasPixMap to draw the shape
        self.canvas_pixmap.draw_shape(
            'rectangle',
            adjusted_start,
            adjusted_end,
            brush_color,
            brush_size
        )
        # Don't call update directly on layer_widget since we're drawing it in the parent's paintEvent
        self.update()

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