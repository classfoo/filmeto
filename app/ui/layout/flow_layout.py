"""
Flow Layout Implementation
This module provides a flow layout that arranges widgets in a flowing manner,
similar to how text flows in a paragraph.
"""
from PySide6.QtWidgets import QLayout, QSizePolicy
from PySide6.QtCore import Qt, QRect, QSize, QPoint


class FlowLayout(QLayout):
    """
    A custom layout that arranges widgets in multiple rows based on available space.
    Widgets flow from left to right and wrap to the next row when needed.
    """
    
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        
        if margin != 0:
            self.setContentsMargins(margin, margin, margin, margin)
            
        self.m_spacing = spacing
        self.item_list = []
    
    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
    
    def addItem(self, item):
        self.item_list.append(item)
    
    def horizontalSpacing(self):
        if self.m_spacing >= 0:
            return self.m_spacing
        else:
            return self.smartSpacing(Qt.Horizontal)
    
    def verticalSpacing(self):
        if self.m_spacing >= 0:
            return self.m_spacing
        else:
            return self.smartSpacing(Qt.Vertical)
    
    def count(self):
        return len(self.item_list)
    
    def itemAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None
    
    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))
    
    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height
    
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QSize()
        
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
            
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size
    
    def doLayout(self, rect, test_only):
        margins = self.contentsMargins()
        effective_rect = rect.adjusted(+margins.left(), +margins.top(), -margins.right(), -margins.bottom())
        
        # If no items, return base height
        if not self.item_list:
            return effective_rect.height()
        
        spacing_x = self.horizontalSpacing()
        spacing_y = self.verticalSpacing()
        
        # Layout items line by line
        current_y = effective_rect.y()
        line_items = []
        current_line_width = 0
        line_height = 0
        
        for item in self.item_list:
            wid = item.widget()
            if spacing_x == -1:
                space_x = wid.style().layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            else:
                space_x = spacing_x
            
            item_width = item.sizeHint().width()
            item_height = item.sizeHint().height()
            
            # For the first item in a line, no spacing is needed
            additional_spacing = space_x if current_line_width > 0 else 0
            next_width = current_line_width + additional_spacing + item_width
            
            # Check if we need to start a new line
            if line_items and next_width > effective_rect.width():
                # Layout the current line
                self._layoutLine(line_items, effective_rect, current_y, line_height, spacing_x, test_only)
                
                # Move to next line
                current_y += line_height + (spacing_y if spacing_y >= 0 else 0)
                line_items = [(item, item_width, item_height)]
                current_line_width = item_width
                line_height = item_height
            else:
                # Add to current line
                line_items.append((item, item_width, item_height))
                current_line_width = next_width
                line_height = max(line_height, item_height)
        
        # Layout the last line
        if line_items:
            self._layoutLine(line_items, effective_rect, current_y, line_height, spacing_x, test_only)
            current_y += line_height + (spacing_y if spacing_y >= 0 else 0)
        
        return current_y - rect.y() + margins.bottom()
    
    def _layoutLine(self, line_items, effective_rect, y, line_height, spacing_x, test_only):
        # If there are no items, nothing to do
        if not line_items:
            return
            
        # Position items with fixed spacing from the left
        x = effective_rect.x()  # Always start from the left
        for i, (item, item_width, item_height) in enumerate(line_items):
            if not test_only:
                # Vertically center item in the line
                item_y = y + (line_height - item_height) // 2
                item.setGeometry(QRect(QPoint(x, item_y), QSize(item_width, item_height)))
            
            # Move x position for next item
            x += item_width
            if i < len(line_items) - 1:  # Don't add spacing after the last item
                x += spacing_x if spacing_x >= 0 else 0
    def smartSpacing(self, mode):
        parent = self.parent()
        if not parent:
            return -1
            
        if parent.isWidgetType():
            return parent.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, mode)
        else:
            return parent.spacing()