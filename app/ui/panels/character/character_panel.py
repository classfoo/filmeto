"""Character panel for role/character management."""

from typing import List, Optional
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QFrame, QLabel, 
    QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint
from PySide6.QtGui import QFont, QCursor
from app.ui.panels.base_panel import BasePanel
from app.ui.layout.flow_layout import FlowLayout
from app.data.workspace import Workspace
from utils.i18n_utils import tr


class CharacterCard(QFrame):
    """Individual character card in the grid"""
    
    delete_requested = Signal(str)  # character_id
    clicked = Signal(str)  # character_id
    
    def __init__(self, character_id: str, character_name: str, parent=None):
        super().__init__(parent)
        self.character_id = character_id
        self.character_name = character_name
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the card UI"""
        self.setFixedSize(120, 120)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Top layout for delete button (spacer + delete button)
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addStretch()
        
        # Delete button
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(20, 20)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.character_id))
        top_layout.addWidget(self.delete_btn)
        layout.addLayout(top_layout)
        
        # Icon label (using character icon)
        icon_label = QLabel("\ue60c")  # Character icon
        icon_font = QFont()
        icon_font.setFamily("iconfont")
        icon_font.setPointSize(36)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #3498db; border: none;")
        layout.addWidget(icon_label)
        
        # Name label
        name_label = QLabel(self.character_name)
        name_font = QFont()
        name_font.setPointSize(11)
        name_label.setFont(name_font)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: #ffffff; border: none;")
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(40)
        layout.addWidget(name_label)
        
        # Apply card style
        self._apply_style()
    
    def _apply_style(self):
        """Apply styling to the card"""
        self.setStyleSheet("""
            CharacterCard {
                background-color: #2d2d2d;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
            }
            CharacterCard:hover {
                background-color: #3a3a3a;
                border: 2px solid #3498db;
            }
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.character_id)
        super().mousePressEvent(event)


class CharacterPanel(BasePanel):
    """Panel for role/character management."""
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the character panel."""
        super().__init__(workspace, parent)
        self._character_cards = []
        self._character_counter = 0  # For generating unique IDs
    
    def setup_ui(self):
        """Set up the UI components with grid layout."""
        # Main vertical layout - no margins
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area for character grid
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QScrollBar:vertical {
                background: #3c3f41;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #606060;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #707070;
            }
        """)
        
        # Container for flow layout
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: #1e1e1e;")
        self.flow_layout = FlowLayout(self.grid_container)
        self.flow_layout.setContentsMargins(15, 15, 15, 15)
        self.flow_layout.setSpacing(12)
        
        # Add button card (first card)
        self.add_card = self._create_add_card()
        self.flow_layout.addWidget(self.add_card)
        
        scroll_area.setWidget(self.grid_container)
        layout.addWidget(scroll_area, 1)
        
        # Load initial characters (if any)
        self._load_characters()
    
    def _create_add_card(self) -> QFrame:
        """Create the add character card"""
        add_card = QFrame()
        add_card.setFixedSize(120, 120)
        add_card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        layout = QVBoxLayout(add_card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Plus icon
        plus_label = QLabel("+")
        plus_font = QFont()
        plus_font.setPointSize(48)
        plus_font.setBold(True)
        plus_label.setFont(plus_font)
        plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plus_label.setStyleSheet("color: #7f8c8d; border: none;")
        layout.addWidget(plus_label)
        
        # Add text
        add_label = QLabel(tr("添加角色"))
        add_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        add_label.setStyleSheet("color: #7f8c8d; border: none; font-size: 11px;")
        layout.addWidget(add_label)
        
        add_card.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 2px dashed #3a3a3a;
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: #3a3a3a;
                border: 2px dashed #3498db;
            }
        """)
        
        add_card.mousePressEvent = lambda e: self._on_add_character() if e.button() == Qt.MouseButton.LeftButton else None
        
        return add_card
    
    def _on_add_character(self):
        """Handle add character button click"""
        self._character_counter += 1
        character_id = f"character_{self._character_counter}"
        character_name = tr("角色") + f" {self._character_counter}"
        
        # Create new character card
        card = CharacterCard(character_id, character_name, self)
        card.delete_requested.connect(self._on_delete_character)
        card.clicked.connect(self._on_character_clicked)
        
        # Insert before add card
        self.flow_layout.insertWidget(len(self._character_cards), card)
        self._character_cards.append(card)
    
    def _on_delete_character(self, character_id: str):
        """Handle delete character request"""
        # Find and remove the card
        for i, card in enumerate(self._character_cards):
            if card.character_id == character_id:
                self.flow_layout.removeWidget(card)
                card.deleteLater()
                self._character_cards.pop(i)
                break
    
    def _on_character_clicked(self, character_id: str):
        """Handle character card click"""
        print(f"Character clicked: {character_id}")
        # TODO: Open character editor or details panel
    
    def _load_characters(self):
        """Load characters from storage (placeholder for now)"""
        # TODO: Load from project data or config file
        pass
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        print("✅ Character panel activated")
    
    def on_deactivated(self):
        """Called when panel is hidden."""
        super().on_deactivated()
        print("⏸️ Character panel deactivated")
