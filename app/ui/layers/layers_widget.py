"""
Layers Management Widget

Provides a vertical list of layers with add, delete, and reorder functionality.
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QPushButton, 
                               QLabel, QHBoxLayout, QMenu, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from app.data.layer import LayerManager, Layer, LayerType
from app.data.task import TaskResult
from app.data.timeline import TimelineItem
from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget, BaseTaskWidget
from app.ui.layers.layer_item_widget import LayerItemWidget

logger = logging.getLogger(__name__)


class LayersWidget(BaseTaskWidget):
    """
    Layer management widget displaying a vertical list of layers.
    
    Features:
    - Vertical stacking of layer items (top to bottom)
    - Add/delete layers
    - Drag to reorder (placeholder for now)
    - Auto-adjusting height
    - Minimal fixed width
    """
    
    # This widget forwards layer-related events from LayerManager to other UI components
    # These signals are emitted based on LayerManager events, not independent actions
    layer_changed = Signal()  # Emitted when any layer is modified
    layer_added = Signal(Layer)  # Emitted when a layer is added
    layer_removed = Signal(int)  # Emitted when a layer is removed (layer_id)
    
    def __init__(self, parent, workspace: Workspace):
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        
        self.workspace = workspace  # Store workspace reference for creating child widgets
        self.layer_manager: Optional[LayerManager] = None
        self.layer_widgets = []
        
        # Fixed width, auto height - compact design
        self.setFixedWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header with title and add button
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Scroll area for layer items
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""QScrollArea { 
            background-color: #1e1e1e; 
            border: none; 
        }""")
        
        # Container for layer items
        self.layers_container = QWidget()
        self.layers_container.setStyleSheet("background-color: #1e1e1e;")
        self.layers_layout = QVBoxLayout(self.layers_container)
        self.layers_layout.setContentsMargins(0, 0, 0, 0)
        self.layers_layout.setSpacing(0)
        self.layers_layout.addStretch()
        
        self.scroll_area.setWidget(self.layers_container)
        main_layout.addWidget(self.scroll_area, 1)
        
        # Apply widget style from styles library (must be the end)
        self._apply_style()
    
    def _create_header(self):
        """Create header with title and add button"""
        header = QWidget()
        header.setFixedHeight(32)
        header.setStyleSheet("background-color: #252525; border-bottom: 1px solid #333333;")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Title label
        title = QLabel("图层")
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet("color: #ffffff; border: none;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Add button
        add_btn = QPushButton("+")
        add_btn.setFixedSize(24, 24)
        add_btn.setToolTip("添加图层")
        add_btn.clicked.connect(self._show_add_menu)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #666666;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        layout.addWidget(add_btn)
        
        return header
    
    def _apply_style(self):
        """Apply widget style from styles library"""
        from app.ui.styles import LAYERS_WIDGET_STYLE
        self.setStyleSheet(LAYERS_WIDGET_STYLE)
    
    def on_timeline_switch(self, timeline_item: TimelineItem):
        """Set the timeline item and load its layers"""
        # Disconnect from previous layer manager if exists
        self.timeline_item = timeline_item
        if timeline_item:
            self.layer_manager = timeline_item.get_layer_manager()
            self._reload_layers(self.layer_manager)
        else:
            self.layer_manager = None

    def on_task_finished(self,result:TaskResult):
        self._reload_layers(self.layer_manager)

    def on_layer_changed(self, layer_manager: LayerManager, layer: Layer, change_type: str):
        self._reload_layers(layer_manager)

    def _reload_layers(self, layer_manager):
        """Reload all layers from the layer manager"""
        # Clear existing layer widgets
        for widget in self.layer_widgets:
            self.layers_layout.removeWidget(widget)
            widget.deleteLater()
        self.layer_widgets.clear()
        
        # Get layers (from top to bottom as they appear in the list)
        layers = layer_manager.get_layers()
        
        if not layers:
            return
        
        # Create widgets for each layer (reverse order for top-to-bottom display)
        for layer in reversed(layers):
            self._add_layer_widget(layer)
    
    def _add_layer_widget(self, layer: Layer):
        """Add a layer widget to the list"""
        widget = LayerItemWidget(layer, self.workspace)
        
        # Connect signals
        widget.visibility_toggled.connect(self._on_visibility_toggled)
        widget.lock_toggled.connect(self._on_lock_toggled)
        widget.drag_started.connect(self._on_drag_started)
        
        # Add context menu for delete
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(lambda pos, w=widget: self._show_context_menu(pos, w))
        
        # Insert before the stretch (at the end of the list)
        insert_index = self.layers_layout.count() - 1
        self.layers_layout.insertWidget(insert_index, widget)
        self.layer_widgets.append(widget)
    
    def _show_add_menu(self):
        """Show menu to select layer type to add"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                color: white;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #4a4a4a;
            }
        """)
        
        # Add menu items for each layer type
        for layer_type in LayerType:
            action = menu.addAction(f"{layer_type.icon} {layer_type.value.capitalize()}")
            action.triggered.connect(lambda checked=False, lt=layer_type: self._add_layer(lt))
        
        # Show menu at button position
        menu.exec(self.mapToGlobal(self.rect().topRight()))
    
    def _add_layer(self, layer_type: LayerType):
        """Add a new layer of the specified type"""
        if not self.layer_manager:
            return
        
        try:
            layer = self.layer_manager.add_layer(layer_type)
            self._reload_layers(self.layer_manager)
        except ValueError as e:
            logger.error(f"Error adding layer: {e}")
            # 可以在这里添加用户提示，例如弹出消息框
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Cannot add layer: {str(e)}")
    
    def _on_layer_added(self, layer: Layer):
        """Handle layer added from external source (e.g. CanvasWidget)"""
        self._add_layer_widget(layer)
        self.layer_changed.emit()
    
    def _show_context_menu(self, pos, widget: LayerItemWidget):
        """Show context menu for layer item"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                color: white;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #4a4a4a;
            }
        """)
        
        delete_action = menu.addAction("删除图层")
        delete_action.triggered.connect(lambda: self._delete_layer(widget))
        
        menu.exec(widget.mapToGlobal(pos))
    
    def _delete_layer(self, widget: LayerItemWidget):
        """Delete a layer"""
        if not self.layer_manager:
            return
        layer_id = widget.layer.id
        self.layer_manager.remove_layer(layer_id)
        self._reload_layers(self.layer_manager)
    
    def _on_layer_removed(self, layer_id: int):
        """Handle layer removed from external source (e.g. CanvasWidget)"""
        # Find and remove the widget
        widget_to_remove = None
        for widget in self.layer_widgets:
            if widget.layer.id == layer_id:
                widget_to_remove = widget
                break
        
        if widget_to_remove:
            self.layers_layout.removeWidget(widget_to_remove)
            self.layer_widgets.remove(widget_to_remove)
            widget_to_remove.deleteLater()
        
        self.layer_changed.emit()
    
    def _on_visibility_toggled(self, layer_id: int, visible: bool):
        """Handle visibility toggle"""
        if self.layer_manager:
            self.layer_manager.toggle_visibility(layer_id)
            # The layer_changed signal will be emitted by LayerManager callback
    
    def _on_lock_toggled(self, layer_id: int, locked: bool):
        """Handle lock toggle"""
        if self.layer_manager:
            self.layer_manager.toggle_lock(layer_id)
            # The layer_changed signal will be emitted by LayerManager callback
    
    def _on_drag_started(self, layer_id: int):
        """Handle drag start for layer reordering"""
        # TODO: Implement drag and drop reordering
        # For now, this is a placeholder
        logger.info(f"Drag started for layer {layer_id}")
    
    def refresh(self):
        """Refresh the layer list"""
        self._reload_layers(self.layer_manager)