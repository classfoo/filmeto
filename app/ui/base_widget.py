from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget, QStyleOption, QStyle

class BaseWidget(QWidget):

    def __init__(self):
        super(BaseWidget, self).__init__()

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        p=QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget,option,p,self)
        super().paintEvent(event)