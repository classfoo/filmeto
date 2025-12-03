"""
Canvas component that provides drawing functionality with multiple modes.
"""
from typing import List, Optional
from PySide6.QtWidgets import QApplication, QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from PySide6.QtCore import Qt, QPoint, QRect, Signal

from app.ui.base_widget import BaseTaskWidget
from app.data.layer import Layer, LayerType, LayerManager
from app.data.timeline import TimelineItem
from app.data.workspace import Workspace
from app.ui.canvas.canvas_layer import CanvasImageLayerWidget, CanvasVideoLayerWidget, CanvasLayerWidget
from app.ui.canvas.canvas_preview import CanvasPreview
from app.ui.signals import Signals
import os


class CanvasWidget(BaseTaskWidget):
    """
    A canvas widget that supports drawing with multiple modes:
    - Brush mode: Draw with different brush types and thickness
    - Eraser mode: Erase parts of the canvas
    - Selection mode: Pan/translate the canvas
    - Shape mode: Add shapes to the canvas
    
    Now supports multi-layer drawing with transparent layer widgets
    """

    def __init__(self, workspace: Workspace):
        super().__init__(workspace)
        
        # Scale factor for displaying the canvas (1.0 = 100%)
        self.layer_widgets: dict[int, CanvasLayerWidget] = {}
        # Currently active layer
        self.active_layer_id: Optional[int] = None
        # Drawing properties (for active layer)
        self.drawing = False
        self.last_point = QPoint()
        # Background placeholder widget
        self.background_widget = None
        self.current_tool_id = 'pen'  # Using tool ID instead of DrawingMode enum
        self.canvas_width = None
        self.canvas_height =  None
        
        # Create preview overlay widget
        self.canvas_preview: Optional[CanvasPreview] = None
        
        # Set up UI with overlapped layout for layers
        self.init_ui()
        print("CanvasWidget initialized")
    
    def init_ui(self):
        """Initialize the user interface"""
        # Set size policy to allow the canvas to expand and fill available space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Enable mouse tracking for better responsiveness
        self.setMouseTracking(True)
        # Make sure canvas can have children widgets (layers)
        self.setAttribute(Qt.WidgetAttribute.WA_StaticContents, False)
        
        # Create preview overlay (initially hidden)
        self._create_preview_overlay()
        
        # Connect to playback state signal
        Signals().connect(Signals.PLAYBACK_STATE_CHANGED, self._on_playback_state_changed)

    def resizeEvent(self, event):
        """Handle resize events to adjust the canvas content scale"""
        super().resizeEvent(event)
        # Update all layer widgets to match the new canvas size based on scale
        for layer_widget in self.layer_widgets.values():
            layer_widget.on_canvas_resize(self.width(),self.height())
        
        # Update preview overlay if it exists
        if self.canvas_preview:
            self.canvas_preview._update_geometry()

    def on_timeline_switch(self, timeline_item: TimelineItem):
        """Set the timeline item and initialize layer management"""
        self.timeline_item = timeline_item
        self.layer_manager = timeline_item.get_layer_manager()
        self.layers = self.layer_manager.get_layers()

        # Remove background placeholder if it exists
        if self.background_widget:
            self.background_widget.setParent(None)
            self.background_widget.deleteLater()
            self.background_widget = None
        
        # Create layer widgets for existing layers
        self._create_layer_widgets()
    
    def get_drawing_config(self):
        """
        Get the current drawing configuration from the project.
        
        Returns:
            Drawing configuration object or None
        """
        if not hasattr(self, 'workspace') or not self.workspace:
            return None
        
        project = self.workspace.get_project()
        if not project:
            return None
        
        return project.get_drawing()
    
    def _create_layer_widgets(self):
        """Create layer widgets for all layers"""
        # Clear existing layer widgets
        for widget in self.layer_widgets.values():
            widget.setParent(None)
            widget.deleteLater()
        self.layer_widgets.clear()
        
        # Create layer widgets only for visible layers
        for layer in self.layers:
            # 只为可见图层创建控件，如果visible属性为空则认为是可见的
            is_visible = getattr(layer, 'visible', True)
            if is_visible:
                layer_widget = self._create_layer_widget(layer)
                if layer_widget is None:
                    continue
                # Add to our mapping
                self.layer_widgets[layer.id] = layer_widget
                
                # Set visibility based on layer visibility and ensure visibility is properly applied
                layer_widget.setVisible(is_visible)
                if is_visible:
                    layer_widget.show()  # Explicitly show if it should be visible
        
        # Set the topmost visible layer as active by default
        visible_layers = [l for l in self.layers if getattr(l, 'visible', True) and l.id in self.layer_widgets]
        if visible_layers:
            self.active_layer_id = visible_layers[-1].id  # Topmost layer
        elif self.layers:
            # If no visible layers exist, make the topmost layer visible and set as active
            top_layer = self.layers[-1]
            self.active_layer_id = top_layer.id
            
            # Ensure the active layer is visible so drawing can be seen
            if top_layer.id in self.layer_widgets:
                layer_widget = self.layer_widgets[top_layer.id]
                layer_widget.setVisible(True)
                layer_widget.show()
                
                # Also update the layer's visibility in the layer manager and config
                if self.layer_manager:
                    # First check current visibility and toggle if needed to make it visible
                    current_layer_obj = self.layer_manager.get_layer(top_layer.id)
                    if current_layer_obj and not getattr(current_layer_obj, 'visible', True):
                        # Toggle to make it visible
                        self.layer_manager.toggle_visibility(top_layer.id)
            elif self.layer_widgets:
                # If we have layer widgets but none are visible, make the last one active
                last_layer_widget_id = list(self.layer_widgets.keys())[-1]
                self.active_layer_id = last_layer_widget_id

    def _create_layer_widget(self, layer: Layer) -> CanvasLayerWidget:
        """Create a layer widget for a specific layer"""
        # Use layer dimensions if available, otherwise use default layer dimensions
        layer_widget_x = getattr(layer, 'x')
        layer_widget_y = getattr(layer, 'y')
        layer_widget_width = getattr(layer, 'width')
        layer_widget_height = getattr(layer, 'height')
        # Pass layer's x and y coordinates to the LayerWidget, along with canvas reference
        if layer.type == LayerType.VIDEO:
            layer_widget = CanvasVideoLayerWidget(self, layer.id, layer, layer_widget_width, layer_widget_height, layer_widget_x, layer_widget_y)
            return layer_widget
        elif layer.type == LayerType.IMAGE:
            layer_widget = CanvasImageLayerWidget(self, layer.id, layer, layer_widget_width, layer_widget_height, layer_widget_x, layer_widget_y)
            return layer_widget
        else:
            return None

    def paintEvent(self, event):
        """Paint the canvas - handle background, panning and temporary shape drawing"""
        # Draw the placeholder background first
        painter = QPainter(self)
        
        # Draw a subtle background pattern or grid
        self._draw_placeholder_background(painter)

    def _draw_placeholder_background(self, painter: QPainter):
        """Draw a placeholder background when no layers exist or for visual reference"""
        # Draw a subtle background pattern or grid
        widget_width = self.width()
        widget_height = self.height()
        
        # Draw a subtle background rectangle with a light gray color
        background_rect = QRect(0, 0, widget_width, widget_height)
        
        # Use a light gray color for the background
        bg_color = QColor(240, 240, 240, 80)  # Semi-transparent light gray
        painter.fillRect(background_rect, bg_color)
        
        # Draw a subtle grid pattern over the background
        grid_color = QColor(220, 220, 220, 40)  # Very light gray for the grid
        painter.setPen(grid_color)
        
        # Draw a grid every 50 pixels (in unscaled coordinates), but adjust based on scale
        grid_size = max(int(50), 10)  # Ensure grid is visible and not too dense
        if grid_size >= 5:  # Only draw grid if it's visible enough
            for x in range(0, widget_width, grid_size):
                painter.drawLine(x, 0, x, widget_height)
            for y in range(0, widget_height, grid_size):
                painter.drawLine(0, y, widget_width, y)

    def _create_background_placeholder(self):
        """Create a background placeholder when no timeline item is set"""
        # Remove any existing default layers that might have been created
        self._remove_default_layers()
        
        # Create background placeholder if it doesn't exist
        if self.background_widget is None:
            self.background_widget = QWidget(self)
            self.background_widget.setGeometry(0, 0, self.canvas_width, self.canvas_height)
            self.background_widget.setStyleSheet("""
                background-color: #2d2d2d;
                border: 1px dashed #555;
            """)
            
            # Add a label to indicate this is a placeholder
            from PySide6.QtWidgets import QLabel, QVBoxLayout
            layout = QVBoxLayout(self.background_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Show both canvas size and layer size in the placeholder
            label = QLabel(f"Canvas Area{self.canvas_width}×{self.canvas_height}Layer Size{self.layer_width}×{self.layer_height}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("""
                color: #888;
                font-size: 14px;
                background-color: transparent;
            """)
            layout.addWidget(label)
            
            self.background_widget.setVisible(True)
            self.background_widget.lower()  # Ensure it's behind other widgets

    def on_layer_changed(self, layer_manager:LayerManager, layer:Layer, change_type:str):
        # Handle different types of changes
        layer_id = layer.id
        if change_type == 'added' and layer:
            # Check if a layer widget already exists for this layer ID to prevent duplicates
            if layer.id not in self.layer_widgets:
                # Create a new layer widget for this layer
                layer_widget = self._create_layer_widget(layer)
                if layer_widget is None:
                    return
                self.layer_widgets[layer.id] = layer_widget
                
                # Set visibility based on layer visibility
                is_visible = getattr(layer, 'visible', True)
                layer_widget.setVisible(is_visible)
                if is_visible:
                    layer_widget.show()
                else:
                    layer_widget.hide()
            
            # Make this the active layer
            self.active_layer_id = layer.id
        elif change_type == 'removed' and layer_id:
            # Remove corresponding layer widget
            if layer_id in self.layer_widgets:
                layer_widget = self.layer_widgets[layer_id]
                layer_widget.setParent(None)
                layer_widget.deleteLater()
                del self.layer_widgets[layer_id]
            
            # Update active layer if needed
            if self.active_layer_id == layer_id:
                visible_layers = [l for l in self.layers if getattr(l, 'visible', True) and l.id in self.layer_widgets]
                if visible_layers:
                    self.active_layer_id = visible_layers[-1].id  # Topmost visible
                elif self.layers:
                    # Find the last layer that still has a widget
                    for layer in reversed(self.layers):
                        if layer.id in self.layer_widgets:
                            self.active_layer_id = layer.id
                            break
                    else:
                        self.active_layer_id = None
                else:
                    self.active_layer_id = None
            
        elif change_type in ['modified', 'reordered']:
            # For general modifications, update the layer widget as needed
            if layer and layer.id in self.layer_widgets:
                is_visible = getattr(layer, 'visible', True)
                self.layer_widgets[layer.id].setVisible(is_visible)
                
                # Show or hide the layer widget based on visibility
                if is_visible:
                    self.layer_widgets[layer.id].show()
                    # When a layer becomes visible, make it the active layer if there isn't one already
                    if not self.active_layer_id:
                        self.active_layer_id = layer.id
                else:
                    self.layer_widgets[layer.id].hide()
                    # If the active layer is hidden, switch to the topmost visible layer
                    if self.active_layer_id == layer.id:
                        # Find next visible layer to activate
                        visible_layers = [l for l in self.layers if getattr(l, 'visible', True) and l.id in self.layer_widgets]
                        if visible_layers:
                            self.active_layer_id = visible_layers[-1].id  # Topmost visible
                        else:
                            self.active_layer_id = None
        
        # Update canvas layers list
        if self.layer_manager:
            self.layers = self.layer_manager.get_layers()
        
        # Refresh the display
        self.update()

    def _remove_default_layers(self):
        """Remove any default layers that might have been created"""
        # Clear existing layer widgets
        for widget in self.layer_widgets.values():
            widget.setParent(None)
            widget.deleteLater()
        self.layer_widgets.clear()
        
        # Clear layer list
        self.layers = []
    
    def _create_preview_overlay(self):
        """Create the preview overlay widget for timeline playback."""
        if self.canvas_preview is None:
            self.canvas_preview = CanvasPreview(self.workspace, self)
            # Initially hidden
            self.canvas_preview.hide()
    
    def get_preview_overlay(self) -> Optional[CanvasPreview]:
        """Get the preview overlay widget.
        
        Returns:
            The CanvasPreview widget or None if not created
        """
        return self.canvas_preview
    
    def update_preview_dimensions(self):
        """Update preview overlay dimensions based on first visible layer."""
        if not self.canvas_preview:
            return
        
        # Get dimensions from first visible layer widget
        if self.layer_widgets:
            first_layer_widget = next(iter(self.layer_widgets.values()))
            self.canvas_preview.set_layer_dimensions(
                first_layer_widget.layer_width,
                first_layer_widget.layer_height
            )
    
    def _on_playback_state_changed(self, sender, params=None, **kwargs):
        """Handle playback state change signal from PlayControl.
        
        Args:
            sender: Signal sender
            params: Boolean indicating playback state (True=playing, False=paused)
        """
        if params is None:
            return
        
        is_playing = params
        if self.canvas_preview:
            self.canvas_preview.on_playback_state_changed(is_playing)