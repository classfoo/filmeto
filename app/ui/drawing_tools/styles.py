"""
CSS styling for DrawingToolsWidget
"""
from PyQt5.QtCore import Qt


def get_drawing_tools_styles():
    """Return CSS styles for drawing tools."""
    return """
    /* Tool buttons */
    QToolButton[objectName^="tool_"] {
        background-color: #f0f0f0;
        border: 1px solid #cccccc;
        border-radius: 6px;
        width: 32px;
        height: 32px;
        margin: 2px;
    }
    
    QToolButton[objectName^="tool_"]:hover {
        background-color: #e0e0e0;
        border: 1px solid #999999;
    }
    
    QToolButton[objectName^="tool_"]:checked {
        background-color: #c0c0c0;
        border: 1px solid #666666;
        font-weight: bold;
    }
    
    QToolButton[objectName^="tool_"]:pressed {
        background-color: #a0a0a0;
    }
    
    /* Floating panel for tool configurations */
    QFrame {
        background-color: white;
        border: 1px solid #cccccc;
        border-radius: 8px;
        padding: 10px;
        min-width: 200px;
    }
    
    /* Labels in the configuration panel */
    QLabel {
        font-size: 12px;
        color: #333333;
        padding: 2px;
    }
    
    /* Comboboxes in the configuration panel */
    QComboBox {
        padding: 4px;
        border: 1px solid #cccccc;
        border-radius: 4px;
        min-width: 120px;
    }
    
    /* Spin boxes in the configuration panel */
    QSpinBox {
        padding: 4px;
        border: 1px solid #cccccc;
        border-radius: 4px;
        min-width: 80px;
    }
    
    /* Buttons in the configuration panel */
    QToolButton {
        background-color: #f0f0f0;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 5px;
        min-width: 80px;
    }
    
    QToolButton:hover {
        background-color: #e0e0e0;
    }
    
    QToolButton:pressed {
        background-color: #d0d0d0;
    }
    """