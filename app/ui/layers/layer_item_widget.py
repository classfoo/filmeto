"""
Layer Item Widget

Represents a single layer in the layer list with visibility toggle,
type icon, name, and lock status controls.
"""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QFont

from app.data.layer import Layer, LayerType
from app.ui.base_widget import BaseWidget
from app.data.workspace import Workspace


class LayerItemWidget(BaseWidget):
    """
    Single layer item widget displaying layer controls and information.
    
    Layout: [Visibility Icon] [Type Icon] [Name Label] [Lock Icon]
    """
    
    # Signals
    visibility_toggled = Signal(int, bool)  # layer_id, visible
    lock_toggled = Signal(int, bool)  # layer_id, locked
    delete_requested = Signal(int)  # layer_id
    drag_started = Signal(int)  # layer_id
    
    def __init__(self, layer: Layer, workspace: Workspace, parent=None):
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        self.layer = layer
        self._is_dragging = False
        self._drag_start_pos = QPoint()  # Initialize drag start position
        
        # Enable mouse tracking for drag detection
        self.setMouseTracking(True)
        
        # Fixed height for consistent layout
        self.setFixedHeight(32)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Main horizontal layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)
        
        # Visibility toggle button (left icon)
        self.visibility_btn = QPushButton()
        self.visibility_btn.setFixedSize(20, 20)
        self.visibility_btn.setCheckable(True)
        self.visibility_btn.setChecked(layer.visible)
        self._update_visibility_icon()
        self.visibility_btn.clicked.connect(self._on_visibility_clicked)
        self.visibility_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #cccccc;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.visibility_btn)
        
        # Type icon (middle left)
        self.type_icon = QLabel(layer.type.icon)
        self.type_icon.setFixedSize(20, 20)
        self.type_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setFamily("iconfont")
        font.setPointSize(12)
        self.type_icon.setFont(font)
        self.type_icon.setStyleSheet("color: #888888;")
        layout.addWidget(self.type_icon)
        
        # Layer name label (center, expandable)
        self.name_label = QLabel(layer.name)
        self.name_label.setStyleSheet("color: #ffffff; padding-left: 4px;")
        font = QFont()
        font.setPointSize(9)
        self.name_label.setFont(font)
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.name_label, 1)
        
        # Lock toggle button (right icon)
        self.lock_btn = QPushButton()
        self.lock_btn.setFixedSize(20, 20)
        self.lock_btn.setCheckable(True)
        self.lock_btn.setChecked(layer.locked)
        self._update_lock_icon()
        self.lock_btn.clicked.connect(self._on_lock_clicked)
        self.lock_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #cccccc;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.lock_btn)
        
        # Apply widget style from styles library
        self._apply_style()
    
    def _apply_style(self):
        """Apply widget style from styles library"""
        from app.ui.styles import LAYER_ITEM_STYLE
        self.setStyleSheet(LAYER_ITEM_STYLE)
    
    def _update_visibility_icon(self):
        """Update visibility button icon based on state"""
        if self.visibility_btn.isChecked():
            self.visibility_btn.setText("\uE8D4")  # 眼睛打开图标
        else:
            self.visibility_btn.setText("\uE8D5")  # 眼睛关闭图标
    
    def _update_lock_icon(self):
        """Update lock button icon based on state"""
        if self.lock_btn.isChecked():
            self.lock_btn.setText("\uE666")  # 锁定图标
        else:
            self.lock_btn.setText("\uE668")  # 解锁图标
    
    def _on_visibility_clicked(self):
        """Handle visibility button click"""
        #self.layer.visible = self.visibility_btn.isChecked()
        self._update_visibility_icon()
        self.visibility_toggled.emit(self.layer.id, self.layer.visible)
    
    def _on_lock_clicked(self):
        """Handle lock button click"""
        self.layer.locked = self.lock_btn.isChecked()
        self._update_lock_icon()
        self.lock_toggled.emit(self.layer.id, self.layer.locked)
    
    def update_display(self):
        """Update the display based on current layer properties"""
        # Update visibility icon
        self.visibility_btn.setChecked(self.layer.visible)
        self._update_visibility_icon()
        
        # Update lock icon
        self.lock_btn.setChecked(self.layer.locked)
        self._update_lock_icon()
        
        # Update layer name
        self.name_label.setText(self.layer.name)
        
        # Update layer type icon
        self.type_icon.setText(self.layer.type.icon)
    
    def update_layer(self, layer: Layer):
        """Update widget to reflect layer changes"""
        self.layer = layer
        self.name_label.setText(layer.name)
        self.visibility_btn.setChecked(layer.visible)
        self.lock_btn.setChecked(layer.locked)
        self.type_icon.setText(layer.type.icon)
        self._update_visibility_icon()
        self._update_lock_icon()
    
    def mousePressEvent(self, event):
        """Handle mouse press for drag detection"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for drag operation"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            if not self._is_dragging and (event.pos() - self._drag_start_pos).manhattanLength() > 5:
                self._is_dragging = True
                self.drag_started.emit(self.layer.id)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self._is_dragging = False
        super().mouseReleaseEvent(event)
