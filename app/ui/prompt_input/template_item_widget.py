from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QPixmap, QCursor

from app.data.workspace import PromptTemplate


class TemplateItemWidget(QWidget):
    """Widget for displaying a single template item in the dropdown list"""
    
    clicked = Signal(PromptTemplate)
    
    def __init__(self, template: PromptTemplate, parent=None):
        super().__init__(parent)
        self.template = template
        self._is_hovered = False
        self._is_selected = False
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Initialize UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Icon label
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setScaledContents(True)
        self.icon_label.setObjectName("template_item_icon")
        
        # Load icon if available
        if self.template.icon:
            pixmap = QPixmap(self.template.icon)
            if not pixmap.isNull():
                self.icon_label.setPixmap(pixmap)
        
        # Text label
        self.text_label = QLabel(self.template.text)
        self.text_label.setObjectName("template_item_text")
        self.text_label.setWordWrap(False)
        
        # Set elide mode for long text
        self.text_label.setTextInteractionFlags(Qt.NoTextInteraction)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label, 1)
        
        self.setLayout(layout)
        self.setFixedHeight(40)
        self.setCursor(QCursor(Qt.PointingHandCursor))
    
    def _apply_style(self):
        """Apply widget styling"""
        self.setProperty("class", "template_item")
        self._update_style()
    
    def _update_style(self):
        """Update style based on state"""
        if self._is_selected:
            self.setStyleSheet("""
                TemplateItemWidget[class="template_item"] {
                    background-color: #4080ff;
                    border-radius: 4px;
                }
                #template_item_text {
                    color: #FFFFFF;
                }
            """)
        elif self._is_hovered:
            self.setStyleSheet("""
                TemplateItemWidget[class="template_item"] {
                    background-color: #3a3c3f;
                    border-radius: 4px;
                }
                #template_item_text {
                    color: #E1E1E1;
                }
            """)
        else:
            self.setStyleSheet("""
                TemplateItemWidget[class="template_item"] {
                    background-color: transparent;
                    border-radius: 4px;
                }
                #template_item_text {
                    color: #E1E1E1;
                }
            """)
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self._is_selected = selected
        self._update_style()
    
    def enterEvent(self, event):
        """Handle mouse enter event"""
        self._is_hovered = True
        self._update_style()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self._is_hovered = False
        self._update_style()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.template)
        super().mousePressEvent(event)
