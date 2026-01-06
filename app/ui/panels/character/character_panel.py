"""Character panel for role/character management."""

import os
from typing import List, Optional
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QFrame, QLabel,
    QPushButton, QMessageBox, QMenu, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QCursor, QPixmap
from app.ui.panels.base_panel import BasePanel
from app.ui.panels.character.character_edit_dialog import CharacterEditDialog
from app.data.character import Character, CharacterManager
from app.data.workspace import Workspace
from app.ui.worker.worker import run_in_background
from utils.i18n_utils import tr


class CharacterCard(QFrame):
    """Individual character card in the grid"""

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
        """Set icon label with character icon"""
        icon_label.setText("\ue60c")  # Character icon
        icon_font = QFont()
        icon_font.setFamily("iconfont")
        # Adjust icon size for taller card (9:16 ratio, height ~187px)
        icon_font.setPointSize(40)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #3498db; border: none;")

    def _load_image_async(self):
        """Load character image asynchronously to avoid blocking UI"""
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


class CharacterPanel(BasePanel):
    """Panel for role/character management."""
    
    character_selected = Signal(str)  # character_name
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the character panel."""
        import time
        init_start = time.time()
        super().__init__(workspace, parent)
        self.character_manager: Optional[CharacterManager] = None
        self._character_cards: List[CharacterCard] = []
        self._character_dict: dict[str, CharacterCard] = {}  # character_name -> card
        init_time = (time.time() - init_start) * 1000
        print(f"⏱️  [CharacterPanel] __init__ completed in {init_time:.2f}ms")
    
    def setup_ui(self):
        """Set up the UI components with grid layout."""
        import time
        setup_start = time.time()
        self.set_panel_title(tr("Roles"))
        
        # Add buttons to unified toolbar
        self.add_toolbar_button("\ue610", self._on_add_character, tr("新建角色"))
        self.add_toolbar_button("\ue6a7", self._on_draw_character, tr("抽卡"))
        self.add_toolbar_button("\ue653", self._on_extract_character, tr("提取"))
        
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
        self.content_layout.addWidget(scroll_area, 1)
        
        setup_time = (time.time() - setup_start) * 1000
        print(f"⏱️  [CharacterPanel] setup_ui completed in {setup_time:.2f}ms")
        
        # Character manager will be loaded in load_data()
        # Data loading is deferred until panel activation
    
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
        """Handle character card click - for selection only"""
        self.character_selected.emit(character_name)

    def _on_character_selection_changed(self, character_name: str, is_selected: bool):
        """Handle character selection state change"""
        # This can be used to maintain selection state or perform other actions
        # For now, we just emit the selection signal
        if is_selected:
            self.character_selected.emit(character_name)
    
    def _on_edit_character(self, character_name: str):
        """Handle edit character request"""
        if not self.character_manager:
            return
        
        dialog = CharacterEditDialog(self.character_manager, character_name, parent=self)
        dialog.character_saved.connect(self._on_character_saved)
        dialog.exec()
    
    
    def _load_characters(self):
        """Load characters from CharacterManager asynchronously"""
        if not self.character_manager:
            return
        
        # Ensure UI components are initialized
        if not hasattr(self, 'grid_layout'):
            return
        
        # Stop any ongoing batch process
        if hasattr(self, '_pending_characters'):
            self._pending_characters = []
        
        # Ensure _character_cards is initialized
        if not hasattr(self, '_character_cards'):
            self._character_cards = []
        if not hasattr(self, '_character_dict'):
            self._character_dict = {}
            
        # Show loading state
        self.show_loading(tr("正在加载角色..."))
            
        # Run loading in background thread to avoid blocking UI
        run_in_background(
            self.character_manager.list_characters,
            on_finished=self._on_characters_loaded,
            on_error=self._on_load_error
        )

    def _on_characters_loaded(self, characters: List[Character]):
        """Callback when characters are loaded from background thread"""
        # Ensure UI components are still valid (panel might have been closed/switched)
        if not hasattr(self, 'grid_layout'):
            self.hide_loading()
            return
            
        # Clear existing cards asynchronously to avoid blocking
        if self._character_cards:
            for card in self._character_cards:
                self.grid_layout.removeWidget(card)
                card.deleteLater()
            self._character_cards.clear()
            self._character_dict.clear()
            # Process events to allow deletion to complete before creating new cards
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
        
        if not characters:
            self.hide_loading()
            return

        # Start batch creation of cards to avoid blocking UI thread
        # Process one card at a time with minimal delay between cards
        self._pending_characters = characters.copy()
        self._batch_row = 0
        self._batch_col = 0
        # Start processing with a small delay to ensure UI is ready
        QTimer.singleShot(10, self._process_next_batch)

    def _process_next_batch(self):
        """Process a batch of character cards to keep UI responsive"""
        if not hasattr(self, '_pending_characters') or not self._pending_characters:
            self.grid_container.adjustSize()
            self.hide_loading() # Hide loading once all cards are created
            return

        # Process only 1 card at a time to ensure UI stays responsive
        # This prevents any blocking from card creation or layout operations
        character = self._pending_characters.pop(0)
        
        # Create card (fast - no image loading in __init__)
        card = CharacterCard(character, self)
        card.edit_requested.connect(self._on_edit_character)
        card.clicked.connect(self._on_character_clicked)
        card.selection_changed.connect(self._on_character_selection_changed)

        self.grid_layout.addWidget(
            card,
            self._batch_row,
            self._batch_col,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.grid_layout.setRowStretch(self._batch_row, 0)
        self.grid_layout.setColumnMinimumWidth(self._batch_col, 0)

        self._character_cards.append(card)
        self._character_dict[character.name] = card

        # Move to next position (2 columns)
        self._batch_col += 1
        if self._batch_col >= 2:
            self._batch_col = 0
            self._batch_row += 1

        # Schedule next card with a small delay to allow UI event loop to process
        # This ensures mouse/keyboard events are handled and UI stays responsive
        # Using 10ms delay balances responsiveness with loading speed
        QTimer.singleShot(10, self._process_next_batch)

    def _on_load_error(self, error_msg: str, exception: Exception):
        """Handle loading error"""
        print(f"❌ Error loading characters: {error_msg}")

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
    
    def load_data(self):
        """Load character data when panel is first activated."""
        super().load_data()
        
        # Get project - this should be fast if workspace is already initialized
        # But if workspace initialization is deferred, this might trigger it
        # So we defer this to background thread
        from app.ui.worker.worker import run_in_background
        
        def _load_character_manager():
            """Load character manager in background to avoid blocking"""
            project = self.workspace.get_project()
            if project:
                return project.get_character_manager()
            return None
        
        run_in_background(
            _load_character_manager,
            on_finished=self._on_character_manager_loaded,
            on_error=self._on_load_error
        )
    
    def _on_character_manager_loaded(self, character_manager):
        """Callback when character manager is loaded"""
        if character_manager:
            self.character_manager = character_manager
            # Connect signals after manager is loaded
            self._connect_signals()
            # Load characters
            self._load_characters()
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        # Reload characters when panel is activated (refresh data)
        if self._data_loaded:
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
