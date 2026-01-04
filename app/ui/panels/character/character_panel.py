"""Character panel for role/character management."""

from typing import List, Optional
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QFrame, QLabel,
    QPushButton, QMessageBox, QMenu, QGridLayout, QSizePolicy, QToolButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor, QPixmap
from app.ui.panels.base_panel import BasePanel
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
        # Fixed card size: 9:16 aspect ratio
        # Width: 85px (calculated for 2 cards in 200px width)
        # Height: 85 * 16 / 9 ≈ 151px
        card_width = 85
        card_height = int(card_width * 16 / 9)
        self.setFixedSize(card_width, card_height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        # Top layout for menu button (spacer + menu button)
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addStretch()
        
        # Menu button with dropdown (replaces delete button)
        self.menu_btn = QToolButton()
        self.menu_btn.setFixedSize(18, 18)
        self.menu_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_btn.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                color: #9e9e9e;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
            QToolButton:hover {
                color: #ffffff;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
        # Set menu icon (three dots)
        self.menu_btn.setText("⋮")  # Three dots (vertical ellipsis)
        
        # Create dropdown menu
        menu = QMenu(self.menu_btn)
        delete_action = menu.addAction(tr("删除"))
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.character.name))
        self.menu_btn.setMenu(menu)
        
        top_layout.addWidget(self.menu_btn)
        layout.addLayout(top_layout)
        
        # Character image or icon
        # Try to load main_view image if available
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setScaledContents(False)
        main_view_path = self.character.get_absolute_resource_path('main_view')
        if main_view_path and self.character.resource_exists('main_view'):
            try:
                pixmap = QPixmap(main_view_path)
                if not pixmap.isNull():
                    # Scale pixmap to fit (will be adjusted based on card width)
                    icon_label.setPixmap(pixmap)
                    icon_label.setScaledContents(True)
                else:
                    # Fallback to icon if image load failed
                    self._set_icon_label(icon_label)
            except Exception:
                # Fallback to icon if image load failed
                self._set_icon_label(icon_label)
        else:
            # Use icon if no image
            self._set_icon_label(icon_label)
        
        layout.addWidget(icon_label, 1)  # Stretch factor 1
        
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
    
    def _set_icon_label(self, icon_label: QLabel):
        """Set icon label with character icon"""
        icon_label.setText("\ue60c")  # Character icon
        icon_font = QFont()
        icon_font.setFamily("iconfont")
        # Adjust icon size for taller card (9:16 ratio, height ~151px)
        icon_font.setPointSize(32)
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
        # Main vertical layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Scroll area for character grid (like file manager)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # Allow container to resize based on content
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Ensure content aligns to top-left
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
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
        
        # Container for grid layout (2 columns)
        # Similar to file manager icon view: fixed icon size, uniform spacing, auto-wrap
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: #1e1e1e;")
        # Size policy: preferred horizontally (fit content), minimum vertically (content-based height)
        # This ensures container doesn't stretch unnecessarily
        self.grid_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        
        self.grid_layout = QGridLayout(self.grid_container)
        # Margins: 10px on all sides for consistent spacing (like file manager)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        # Spacing: 10px between cards (both horizontal and vertical, uniform like file manager)
        self.grid_layout.setSpacing(10)
        # Don't stretch columns - columns size based on fixed card width (85px + spacing)
        self.grid_layout.setColumnStretch(0, 0)
        self.grid_layout.setColumnStretch(1, 0)
        # Set column minimum width to ensure proper spacing
        self.grid_layout.setColumnMinimumWidth(0, 0)
        self.grid_layout.setColumnMinimumWidth(1, 0)
        # Don't stretch rows - rows size based on fixed card height (85px + spacing)
        # Alignment: top-left, like file manager icon view
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll_area.setWidget(self.grid_container)
        layout.addWidget(scroll_area, 1)
        
        # Load character manager (without connecting signals yet)
        project = self.workspace.get_project()
        if project:
            self.character_manager = project.get_character_manager()
        
        # Load initial characters first
        self._load_characters()
        
        # Connect signals after UI is fully initialized
        self._connect_signals()
    
    def _create_toolbar(self) -> QFrame:
        """Create top toolbar with title and icon action buttons"""
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border-bottom: 1px solid #3a3a3a;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        
        # Title label on the left
        title_label = QLabel("character")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(title_label)
        
        # Spacer to push buttons to the right
        layout.addStretch()
        
        # Icon font for buttons (smaller for 16x16 buttons)
        icon_font = QFont("iconfont", 10)
        
        # New button (新建) - add-role icon
        # Icon-only button style: transparent background, icon color changes on hover
        new_btn = QPushButton("\ue610", self)  # add-role icon
        new_btn.setFont(icon_font)
        new_btn.setFixedSize(16, 16)
        new_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        new_btn.setToolTip(tr("新建角色"))
        new_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4080ff;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: transparent;
                color: #5090ff;
            }
            QPushButton:pressed {
                background-color: transparent;
                color: #3070cc;
            }
        """)
        new_btn.clicked.connect(self._on_add_character)
        layout.addWidget(new_btn)
        
        # Draw button (抽卡) - coupon icon (card-like)
        draw_btn = QPushButton("\ue6a7", self)  # coupon icon
        draw_btn.setFont(icon_font)
        draw_btn.setFixedSize(16, 16)
        draw_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        draw_btn.setToolTip(tr("抽卡"))
        draw_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #9e9e9e;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: transparent;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: transparent;
                color: #757575;
            }
        """)
        draw_btn.clicked.connect(self._on_draw_character)
        layout.addWidget(draw_btn)
        
        # Extract button (提取) - export icon
        extract_btn = QPushButton("\ue653", self)  # icexport icon
        extract_btn.setFont(icon_font)
        extract_btn.setFixedSize(16, 16)
        extract_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        extract_btn.setToolTip(tr("提取"))
        extract_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #9e9e9e;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: transparent;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: transparent;
                color: #757575;
            }
        """)
        extract_btn.clicked.connect(self._on_extract_character)
        layout.addWidget(extract_btn)
        
        return toolbar
    
    def resizeEvent(self, event):
        """Handle resize event - update layout like file manager"""
        super().resizeEvent(event)
        # Cards are fixed size, container adjusts naturally
        if hasattr(self, 'grid_container'):
            self.grid_container.adjustSize()
    
    def _connect_signals(self):
        """Connect character manager signals"""
        if self.character_manager:
            # Disconnect first to avoid duplicate connections
            try:
                self.character_manager.character_added.disconnect(self._on_character_added)
                self.character_manager.character_updated.disconnect(self._on_character_updated)
                self.character_manager.character_deleted.disconnect(self._on_character_deleted)
            except:
                pass  # Ignore if not connected
            
            # Connect signals
            self.character_manager.character_added.connect(self._on_character_added)
            self.character_manager.character_updated.connect(self._on_character_updated)
            self.character_manager.character_deleted.connect(self._on_character_deleted)
    
    def _load_character_manager(self):
        """Load character manager from project (for use in on_activated)"""
        project = self.workspace.get_project()
        if project:
            self.character_manager = project.get_character_manager()
    
    def _on_add_character(self):
        """Handle add character button click"""
        if not self.character_manager:
            QMessageBox.warning(self, tr("错误"), tr("角色管理器未初始化"))
            return
        
        dialog = CharacterEditDialog(self.character_manager, parent=self)
        dialog.character_saved.connect(self._on_character_saved)
        dialog.exec()
    
    def _on_draw_character(self):
        """Handle draw character button click (抽卡)"""
        # TODO: Implement character drawing feature
        QMessageBox.information(self, tr("提示"), tr("抽卡功能开发中..."))
    
    def _on_extract_character(self):
        """Handle extract character button click (提取)"""
        # TODO: Implement character extraction feature
        QMessageBox.information(self, tr("提示"), tr("提取功能开发中..."))
    
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
        
        # Ensure UI components are initialized
        if not hasattr(self, 'grid_layout'):
            return
        
        # Ensure _character_cards is initialized
        if not hasattr(self, '_character_cards'):
            self._character_cards = []
        if not hasattr(self, '_character_dict'):
            self._character_dict = {}
        
        # Load all characters
        characters = self.character_manager.list_characters()
        
        # Clear existing cards
        for card in self._character_cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self._character_cards.clear()
        self._character_dict.clear()
        
        # Add character cards in 2-column grid (like file manager icon view)
        row = 0
        col = 0
        for character in characters:
            card = CharacterCard(character, self)
            card.delete_requested.connect(self._on_delete_character)
            card.edit_requested.connect(self._on_edit_character)
            card.clicked.connect(self._on_character_clicked)
            
            # Add widget to grid with top-left alignment (like file manager icons)
            # No stretch, fixed size widgets
            self.grid_layout.addWidget(
                card, 
                row, 
                col,
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
            )
            # Ensure row doesn't stretch vertically
            self.grid_layout.setRowStretch(row, 0)
            # Ensure column doesn't stretch horizontally
            self.grid_layout.setColumnMinimumWidth(col, 0)
            
            self._character_cards.append(card)
            self._character_dict[character.name] = card
            
            # Move to next position (2 columns, auto-wrap)
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        # Update container size to fit content (like file manager)
        self.grid_container.adjustSize()
    
    def _on_character_saved(self, character_name: str):
        """Handle character saved signal"""
        self._load_characters()
    
    def _on_character_added(self, character: Character):
        """Handle character added signal"""
        self._load_characters()
    
    def _on_character_updated(self, character: Character):
        """Handle character updated signal"""
        # Reload all characters to ensure consistency
        self._load_characters()
    
    def _on_character_deleted(self, character_name: str):
        """Handle character deleted signal"""
        # Reload all characters
        self._load_characters()
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        # Reload characters when panel is activated
        self._load_character_manager()
        self._connect_signals()
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
        self._connect_signals()
        self._load_characters()
