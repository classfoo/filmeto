from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPoint

class DraggableScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("draggable_scroll_area")
        self.setWidgetResizable(True)
        self.drag_start_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drag_start_position is not None:
            delta = event.pos() - self.drag_start_position
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.drag_start_position = event.pos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = None
        super().mouseReleaseEvent(event)

# 使用示例
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # 创建一个主窗口
    main_window = QWidget()
    main_layout = QVBoxLayout(main_window)

    # 创建一个可拖拽滚动的 QScrollArea
    scroll_area = DraggableScrollArea()
    scroll_area.setWidget(QWidget())  # 设置一个空的 QWidget 作为滚动区域的内容

    # 在滚动区域的内容中添加一些标签
    content_layout = QVBoxLayout(scroll_area.widget())
    for i in range(50):
        label = QLabel(f"Label {i}")
        content_layout.addWidget(label)

    main_layout.addWidget(scroll_area)
    main_window.show()

    sys.exit(app.exec())