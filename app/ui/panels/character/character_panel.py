"""Character panel for role/character management."""

from typing import List, Optional
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QFrame, QLabel,
    QPushButton, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor, QPixmap
from app.ui.panels.base_panel import BasePanel
from app.ui.layout.flow_layout import FlowLayout
from app.ui.panels.character.character_edit_dialog import CharacterEditDialog
from app.data.character import Character, CharacterManager
from app.data.workspace import Workspace
from utils.i18n_utils import tr


class CharacterCard(QFrame):
    """Individual character card in the grid"""
    
    delete_requested = Signal(str)  # character_name
    edit_requested = Signal(str)  # character_name
    clicked = Signal(str)  # character_name
    
    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self.character = character
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
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.character.name))
        top_layout.addWidget(self.delete_btn)
        layout.addLayout(top_layout)
        
        # Character image or icon
        # Try to load main_view image if available
        icon_label = QLabel()
        main_view_path = self.character.get_absolute_resource_path('main_view')
        if main_view_path and self.character.resource_exists('main_view'):
            try:
                pixmap = QPixmap(main_view_path)
                if not pixmap.isNull():
                    # Scale pixmap to fit (80x80 max)
                    scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    icon_label.setPixmap(scaled_pixmap)
                    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    # Fallback to icon if image load failed
                    self._set_icon_label(icon_label)
            except Exception:
                # Fallback to icon if image load failed
                self._set_icon_label(icon_label)
        else:
            # Use icon if no image
            self._set_icon_label(icon_label)
        
        layout.addWidget(icon_label)
        
        # Name label
        name_label = QLabel(self.character.name)
        name_font = QFont()
        name_font.setPointSize(11)
        name_label.setFont(name_font)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: #ffffff; border: none;")
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(30)
        layout.addWidget(name_label)
        
        # Apply card style
        self._apply_style()
    
    def _set_icon_label(self, icon_label: QLabel):
        """Set icon label with character icon"""
        icon_label.setText("\ue60c")  # Character icon
        icon_font = QFont()
        icon_font.setFamily("iconfont")
        icon_font.setPointSize(36)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #3498db; border: none;")
    
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
            self.clicked.emit(self.character.name)
        super().mousePressEvent(event)
    
    def contextMenuEvent(self, event):
        """Handle context menu"""
        menu = QMenu(self)
        
        edit_action = menu.addAction(tr("编辑"))
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.character.name))
        
        delete_action = menu.addAction(tr("删除"))
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.character.name))
        
        menu.exec(event.globalPos())


class CharacterPanel(BasePanel):
    """Panel for role/character management."""
    
    character_selected = Signal(str)  # character_name
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the character panel."""
        super().__init__(workspace, parent)
        self.character_manager: Optional[CharacterManager] = None
        self._character_cards: List[CharacterCard] = []
        self._character_dict: dict[str, CharacterCard] = {}  # character_name -> card
    
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
        
        # Load character manager
        self._load_character_manager()
        
        # Load initial characters
        self._load_characters()
    
    def _load_character_manager(self):
        """Load character manager from project"""
        project = self.workspace.get_project()
        if project:
            self.character_manager = project.get_character_manager()
            
            # Connect signals
            if self.character_manager:
                self.character_manager.character_added.connect(self._on_character_added)
                self.character_manager.character_updated.connect(self._on_character_updated)
                self.character_manager.character_deleted.connect(self._on_character_deleted)
    
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
        if not self.character_manager:
            QMessageBox.warning(self, tr("错误"), tr("角色管理器未初始化"))
            return
        
        dialog = CharacterEditDialog(self.character_manager, parent=self)
        dialog.character_saved.connect(self._on_character_saved)
        dialog.exec()
    
    def _on_character_clicked(self, character_name: str):
        """Handle character card click"""
        self.character_selected.emit(character_name)
        # Open edit dialog on click
        self._on_edit_character(character_name)
    
    def _on_edit_character(self, character_name: str):
        """Handle edit character request"""
        if not self.character_manager:
            return
        
        dialog = CharacterEditDialog(self.character_manager, character_name, parent=self)
        dialog.character_saved.connect(self._on_character_saved)
        dialog.exec()
    
    def _on_delete_character(self, character_name: str):
        """Handle delete character request"""
        if not self.character_manager:
            return
        
        reply = QMessageBox.question(
            self,
            tr("确认删除"),
            tr(f"确定要删除角色 '{character_name}' 吗？此操作不可撤销。"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.character_manager.delete_character(character_name):
                # Card will be removed by signal handler
                pass
            else:
                QMessageBox.warning(self, tr("错误"), tr("删除角色失败"))
    
    def _load_characters(self):
        """Load characters from CharacterManager"""
        if not self.character_manager:
            return
        
        characters = self.character_manager.list_characters()
        
        # Remove add card temporarily
        self.flow_layout.removeWidget(self.add_card)
        
        # Clear existing cards
        for card in self._character_cards:
            self.flow_layout.removeWidget(card)
            card.deleteLater()
        self._character_cards.clear()
        self._character_dict.clear()
        
        # Add character cards
        for character in characters:
            card = CharacterCard(character, self)
            card.delete_requested.connect(self._on_delete_character)
            card.edit_requested.connect(self._on_edit_character)
            card.clicked.connect(self._on_character_clicked)
            
            self.flow_layout.addWidget(card)
            self._character_cards.append(card)
            self._character_dict[character.name] = card
        
        # Re-add add card at the end
        self.flow_layout.addWidget(self.add_card)
    
    def _on_character_saved(self, character_name: str):
        """Handle character saved signal"""
        self._load_characters()
    
    def _on_character_added(self, character: Character):
        """Handle character added signal"""
        self._load_characters()
    
    def _on_character_updated(self, character: Character):
        """Handle character updated signal"""
        # Update existing card or reload all
        if character.name in self._character_dict:
            # Remove old card
            old_card = self._character_dict[character.name]
            self.flow_layout.removeWidget(old_card)
            old_card.deleteLater()
            self._character_cards.remove(old_card)
            del self._character_dict[character.name]
        
        # Add updated card
        card = CharacterCard(character, self)
        card.delete_requested.connect(self._on_delete_character)
        card.edit_requested.connect(self._on_edit_character)
        card.clicked.connect(self._on_character_clicked)
        
        # Insert before add card
        self.flow_layout.removeWidget(self.add_card)
        self.flow_layout.addWidget(card)
        self.flow_layout.addWidget(self.add_card)
        
        self._character_cards.append(card)
        self._character_dict[character.name] = card
    
    def _on_character_deleted(self, character_name: str):
        """Handle character deleted signal"""
        if character_name in self._character_dict:
            card = self._character_dict[character_name]
            self.flow_layout.removeWidget(card)
            card.deleteLater()
            self._character_cards.remove(card)
            del self._character_dict[character_name]
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        # Reload characters when panel is activated
        self._load_character_manager()
        self._load_characters()
        print("✅ Character panel activated")
    
    def on_deactivated(self):
        """Called when panel is hidden."""
        super().on_deactivated()
        print("⏸️ Character panel deactivated")
    
    def on_project_switched(self, project_name: str):
        """Handle project switch"""
        super().on_project_switched(project_name)
        self._load_character_manager()
        self._load_characters()
