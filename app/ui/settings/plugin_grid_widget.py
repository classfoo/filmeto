"""
Plugin Grid Widget

Displays service plugins in a grid layout with status indicators.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor

from app.plugins.service_registry import ServiceInfo
from app.ui.layout.flow_layout import FlowLayout


class PluginCardWidget(QFrame):
    """Individual plugin card in the grid"""
    
    clicked = Signal(str)  # service_id
    
    def __init__(self, service_info: ServiceInfo, parent=None):
        super().__init__(parent)
        self.service_info = service_info
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the card UI"""
        self.setFixedSize(180, 180)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon label
        icon_label = QLabel(self.service_info.icon)
        icon_font = QFont()
        icon_font.setFamily("iconfont")
        icon_font.setPointSize(48)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #3498db; border: none;")
        layout.addWidget(icon_label)
        
        # Name label
        name_label = QLabel(self.service_info.name)
        name_font = QFont()
        name_font.setPointSize(13)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: #ffffff; border: none;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Status badge
        status_text = "Active" if self.service_info.enabled else "Disabled"
        status_color = "#27ae60" if self.service_info.enabled else "#7f8c8d"
        
        status_label = QLabel(status_text)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {status_color};
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 4px 12px;
                font-size: 10px;
            }}
        """)
        layout.addWidget(status_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Capabilities count
        cap_count = len(self.service_info.capabilities)
        cap_label = QLabel(f"{cap_count} {'capability' if cap_count == 1 else 'capabilities'}")
        cap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cap_label.setStyleSheet("color: #95a5a6; font-size: 10px; border: none;")
        layout.addWidget(cap_label)
        
        # Apply card style
        self._apply_style()
    
    def _apply_style(self):
        """Apply styling to the card"""
        self.setStyleSheet("""
            PluginCardWidget {
                background-color: #2d2d2d;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
            }
            PluginCardWidget:hover {
                background-color: #3a3a3a;
                border: 2px solid #3498db;
            }
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.service_info.service_id)
        super().mousePressEvent(event)


class PluginGridWidget(QWidget):
    """Grid view of service plugins"""
    
    plugin_selected = Signal(str)  # service_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._plugin_cards = []
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Title section
        title_widget = QWidget()
        title_widget.setStyleSheet("background-color: #252525; border-bottom: 1px solid #333333;")
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel("Service Plugins")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff; border: none;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        main_layout.addWidget(title_widget)
        
        # Scroll area for plugin grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
        """)
        
        # Container for flow layout
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: #1e1e1e;")
        self.flow_layout = FlowLayout(self.grid_container)
        self.flow_layout.setContentsMargins(20, 20, 20, 20)
        self.flow_layout.setSpacing(15)
        
        scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(scroll_area)
    
    def set_services(self, services: List[ServiceInfo]):
        """Set the list of services to display"""
        # Clear existing cards
        for card in self._plugin_cards:
            self.flow_layout.removeWidget(card)
            card.deleteLater()
        self._plugin_cards.clear()
        
        # Create cards for each service
        for service_info in services:
            card = PluginCardWidget(service_info)
            card.clicked.connect(self._on_card_clicked)
            self.flow_layout.addWidget(card)
            self._plugin_cards.append(card)
    
    def _on_card_clicked(self, service_id: str):
        """Handle card click"""
        self.plugin_selected.emit(service_id)
    
    def refresh(self, services: List[ServiceInfo]):
        """Refresh the grid with updated service list"""
        self.set_services(services)
