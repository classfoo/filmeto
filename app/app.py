import asyncio
import os
import sys

from qasync import QEventLoop
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from app.data.workspace import Workspace
from app.ui.main_window import MainWindow
from server.server import Server
from utils.i18n_utils import translation_manager

def load_stylesheet(main_path):
    """loading QSS style files"""
    style_file = "style/dark_style.qss"
    if os.path.exists(style_file):
        with open(style_file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        print(f"Warning: style file '{style_file}' not found, use default.")
        return ""

def load_custom_font(main_path):
    """
    尝试加载自定义字体。
    优先查找与脚本同目录的文件，提供详细的错误信息。
    返回 (font_family_name, success_message, error_message)
    """
    error_msg = ""
    success_msg = ""
    font_path = os.path.join(main_path, "textures","iconfont.ttf")
    if not os.path.exists(font_path):
        error_msg += f"错误：在脚本目录下找不到字体文件  (路径: {font_path})\n"
        # 可选：回退到当前工作目录查找
        # font_path = font_file_name
        # print(f"[调试] 回退到当前工作目录查找: {font_path}")
        # if not os.path.exists(font_path):
        #     error_msg += f"错误：在当前工作目录下也找不到字体文件 '{font_file_name}'\n"
        #     return None, success_msg, error_msg
        # else:
        #     success_msg += f"注意：在当前工作目录找到字体文件，建议将字体文件放在脚本同目录。\n"
    else:
        success_msg += f"找到字体文件: {font_path}\n"

    # 检查文件扩展名
    _, ext = os.path.splitext(font_path)
    if ext.lower() not in ['.ttf', '.otf']:
        error_msg += f"警告：字体文件 '{font_path}' 的扩展名 '{ext}' 可能不受支持。请使用 .ttf 或 .otf 格式。\n"


    # 尝试加载字体
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id == -1:
        error_msg += f"失败：PySide6 无法加载字体文件 '{font_path}'。文件可能已损坏、格式不受支持或权限不足。\n"
        return None, success_msg, error_msg
    else:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            family_name = font_families[0]
            success_msg += f"成功：加载了字体族 '{family_name}' (来自 {font_path})\n"
            return family_name, success_msg, error_msg
        else:
            error_msg += f"失败：字体文件 '{font_path}' 已加载，但未找到有效的字体族名称。\n"
            return None, success_msg, error_msg

class App():

    def __init__(self,main_path):
        self.main_path = main_path
        #sys.exit(app.exec())

    def start(self):
        app = QApplication(sys.argv)
        
        # Initialize translation system
        translation_manager.set_app(app)
        # Set default language (can be loaded from config later)
        translation_manager.switch_language("zh_CN")
        
        # 启动消费者
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        load_custom_font(self.main_path)
        app.setStyleSheet(load_stylesheet(self.main_path))
        # load main window
        workspacePath = os.path.join(self.main_path, "workspace")
        self.workspace = Workspace(workspacePath,"demo")
        self.server = Server()
        self.window = MainWindow(self.workspace)
        self.window.show()
        asyncio.ensure_future(self.workspace.start())
        # 运行主循环
        with loop:
            sys.exit(loop.run_forever())

    def workspace(self):
        return self.workspace

    def server(self):
        return self.server
if __name__ == "__main__":
    App()