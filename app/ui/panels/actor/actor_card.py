"""Actor card widget for displaying individual actor information."""

import os
import logging
from typing import Optional
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QMenu, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QCursor, QPixmap
from app.data.character import Character
from utils.i18n_utils import tr


class ActorCard(QFrame):
    """Individual actor card in the grid"""

    edit_requested = Signal(str)  # character_name
    clicked = Signal(str)  # character_name
    selection_changed = Signal(str, bool)  # character_name, is_selected

    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self.character = character
        self._is_selected = False
        self._image_loaded = False
        self._init_ui()

    def _init_ui(self):
        """Initialize the card UI"""
        # Fixed card size: 9:16 aspect ratio
        # Total panel width: 240px
        # Left/right margins: 10px each = 20px
        # Card spacing: 10px
        # Available width: 240 - 20 - 10 = 210px
        # Card width: 210 / 2 = 105px
        # Card height: 105 * 16 / 9 ≈ 187px
        card_width = 105
        card_height = int(card_width * 16 / 9)
        self.setFixedSize(card_width, card_height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Top layout for checkbox
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addStretch()

        # Icon for selection indicator
        self.selection_icon = QLabel()
        self.selection_icon.setFixedSize(18, 18)
        self.selection_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set font for icon
        icon_font = QFont("iconfont", 10)
        self.selection_icon.setFont(icon_font)

        # Initially show unselected icon
        self._update_selection_icon()

        # Make the icon clickable
        self.selection_icon.mousePressEvent = self._on_selection_icon_clicked
        self.selection_icon.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        top_layout.addWidget(self.selection_icon)
        layout.addLayout(top_layout)
        
        # Character image or icon - use placeholder first, load image asynchronously
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setScaledContents(False)
        # Start with placeholder icon (fast - no file I/O)
        self._set_icon_label(self.icon_label)
        
        layout.addWidget(self.icon_label, 1)  # Stretch factor 1

        # Name label
        name_label = QLabel(self.character.name)
        name_font = QFont()
        name_font.setPointSize(10)
        name_label.setFont(name_font)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: #ffffff; border: none;")
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(20)
        layout.addWidget(name_label)

        # Apply card style
        self._apply_style()
        
        # Load image asynchronously after UI is created
        self._load_image_async()

    def _on_selection_icon_clicked(self, event):
        """Handle selection icon click"""
        self._is_selected = not self._is_selected
        self._update_selection_icon()
        self.selection_changed.emit(self.character.name, self._is_selected)
        # Update card style based on selection
        self._update_selection_style()

    def set_selected(self, selected: bool):
        """Set the selection state of the card"""
        self._is_selected = selected
        self._update_selection_icon()
        self._update_selection_style()

    def _update_selection_icon(self):
        """Update the selection icon based on selection state"""
        if self._is_selected:
            self.selection_icon.setText("\ue675")  # Selected icon
            self.selection_icon.setStyleSheet("color: #3498db;")  # Blue color for selected
        else:
            self.selection_icon.setText("\ue673")  # Unselected icon
            self.selection_icon.setStyleSheet("color: #9e9e9e;")  # Gray color for unselected

    def _update_selection_style(self):
        """Update the card style based on selection state"""
        if self._is_selected:
            self.setStyleSheet("""
                CharacterCard {
                    background-color: #3a3a3a;
                    border: 2px solid #3498db;
                    border-radius: 8px;
                }
                CharacterCard:hover {
                    background-color: #4a4a4a;
                    border: 2px solid #3498db;
                }
            """)
        else:
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

    def _set_icon_label(self, icon_label: QLabel):
        """Set icon label with actor icon"""
        icon_label.setText("\ue60c")  # Character icon
        icon_font = QFont()
        icon_font.setFamily("iconfont")
        # Adjust icon size for taller card (9:16 ratio, height ~187px)
        icon_font.setPointSize(40)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #3498db; border: none;")

    def _load_image_async(self):
        """Load actor image asynchronously to avoid blocking UI"""
        if self._image_loaded:
            return
        
        # Get resource path without checking existence (fast)
        main_view_path = self.character.get_resource_path('main_view')
        if not main_view_path:
            return
        
        # Defer image loading to avoid blocking card creation
        # Use a small delay to ensure card UI is fully rendered first
        QTimer.singleShot(50, lambda: self._load_image_sync(main_view_path))
    
    def _load_image_sync(self, rel_path: str):
        """Load image synchronously (called after card is created)"""
        if self._image_loaded:
            return
        
        try:
            abs_path = self.character.get_absolute_resource_path('main_view')
            if not abs_path:
                return
            
            # Check file existence first (fast check)
            if not os.path.exists(abs_path):
                return
            
            # Load pixmap - this can be slow for large images
            # Use QPixmap.load() which is more efficient than constructor
            pixmap = QPixmap()
            if pixmap.load(abs_path):
                # Scale pixmap to fit card size before setting (reduces memory and rendering cost)
                card_width = 105  # Match card width
                card_height = int(card_width * 16 / 9)
                scaled_pixmap = pixmap.scaled(
                    card_width, card_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.icon_label.setPixmap(scaled_pixmap)
                self.icon_label.setScaledContents(False)  # Already scaled
                self._image_loaded = True
        except Exception:
            # Keep placeholder icon on error
            pass

    def _apply_style(self):
        """Apply styling to the card"""
        self._update_selection_style()
    
    def mousePressEvent(self, event):
        """Handle mouse press - single click for selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Toggle selection when card is clicked
            self._is_selected = not self._is_selected
            self._update_selection_icon()
            self.selection_changed.emit(self.character.name, self._is_selected)
            self._update_selection_style()
            self.clicked.emit(self.character.name)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle mouse double click - open edit dialog"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_requested.emit(self.character.name)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        """Handle context menu"""
        menu = QMenu(self)

        edit_action = menu.addAction(tr("编辑"))
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.character.name))

        menu.exec(event.globalPos())
