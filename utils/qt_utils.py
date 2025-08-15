from PySide6 import QtWidgets


def remove_last_stretch(layout):
    """移除最后一个 addStretch 添加的 spacer"""
    if layout is not None:
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if isinstance(item, QtWidgets.QSpacerItem):
                layout.removeItem(item)
                break  # 只移除最后一个