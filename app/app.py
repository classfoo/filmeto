import asyncio
import os
import sys
import logging
import traceback

from qasync import QEventLoop
from PySide6.QtGui import QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler, QtMsgType

from app.data.workspace import Workspace
from app.ui.main_window import MainWindow
from server.server import Server, ServerManager
from utils.i18n_utils import translation_manager

logger = logging.getLogger(__name__)

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
        self._setup_qt_message_handler()
    
    def _setup_qt_message_handler(self):
        """Setup Qt message handler to log Qt warnings and errors"""
        def qt_message_handler(msg_type, context, message):
            """Custom Qt message handler"""
            # Map Qt message types to logging levels
            if msg_type == QtMsgType.QtDebugMsg:
                logger.debug(f"Qt: {message}")
            elif msg_type == QtMsgType.QtInfoMsg:
                logger.info(f"Qt: {message}")
            elif msg_type == QtMsgType.QtWarningMsg:
                logger.warning(f"Qt Warning: {message}")
                if context.file:
                    logger.warning(f"  File: {context.file}:{context.line}")
                if context.function:
                    logger.warning(f"  Function: {context.function}")
            elif msg_type == QtMsgType.QtCriticalMsg:
                logger.error(f"Qt Critical: {message}")
                if context.file:
                    logger.error(f"  File: {context.file}:{context.line}")
                if context.function:
                    logger.error(f"  Function: {context.function}")
                # Log stack trace for critical messages
                logger.error("Stack trace:", exc_info=True)
            elif msg_type == QtMsgType.QtFatalMsg:
                logger.critical(f"Qt Fatal: {message}")
                if context.file:
                    logger.critical(f"  File: {context.file}:{context.line}")
                if context.function:
                    logger.critical(f"  Function: {context.function}")
                # Log full stack trace for fatal errors
                logger.critical("Stack trace:", exc_info=True)
        
        qInstallMessageHandler(qt_message_handler)

    def start(self):
        try:
            logger.info("Creating QApplication...")
            app = QApplication(sys.argv)
            
            # Set application icon for all platforms
            icon_path = os.path.join(self.main_path, "textures", "filmeto.png")
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
                logger.info(f"Application icon set from {icon_path}")
            else:
                logger.warning(f"Application icon not found at {icon_path}")
            
            # Initialize translation system
            logger.info("Initializing translation system...")
            translation_manager.set_app(app)
            # Set default language (can be loaded from config later)
            translation_manager.switch_language("zh_CN")
            
            # 启动消费者
            logger.info("Setting up event loop...")
            loop = QEventLoop(app)
            asyncio.set_event_loop(loop)
            
            logger.info("Loading custom font...")
            load_custom_font(self.main_path)
            
            logger.info("Loading stylesheet...")
            app.setStyleSheet(load_stylesheet(self.main_path))
            
            # load main window
            logger.info("Initializing workspace...")
            workspacePath = os.path.join(self.main_path, "workspace")
            self.workspace = Workspace(workspacePath,"demo")
            
            logger.info("Initializing server...")
            # Use ServerManager instead of trying to instantiate Server directly
            self.server_manager = ServerManager(workspacePath)
            # Get the default/local server from the manager
            self.server = self.server_manager.get_server("local")
            
            logger.info("Creating main window...")
            self.window = MainWindow(self.workspace)
            self.window.showMaximized()
            
            logger.info("Starting workspace...")
            asyncio.ensure_future(self.workspace.start())
            
            # Register cleanup on application exit
            logger.info("Registering cleanup handlers...")
            app.aboutToQuit.connect(self._cleanup_on_exit)
            
            # 运行主循环
            logger.info("Starting main event loop...")
            with loop:
                sys.exit(loop.run_forever())
        
        except Exception as e:
            logger.critical("="*80)
            logger.critical("CRITICAL ERROR IN APP.START()")
            logger.critical("="*80)
            logger.critical(f"Exception: {e}")
            logger.critical("Full stack trace:", exc_info=True)
            logger.critical("="*80)
            raise
    
    def _cleanup_on_exit(self):
        """Clean up resources when application is about to quit."""
        logger.info("="*80)
        logger.info("Application shutting down, cleaning up resources...")
        logger.info("="*80)
        try:
            # Shutdown the layer composition task manager
            logger.info("Shutting down LayerComposeTaskManager...")
            from app.data.layer import get_compose_task_manager
            task_manager = get_compose_task_manager()
            task_manager.shutdown()
            logger.info("LayerComposeTaskManager shutdown complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
        
        logger.info("Cleanup complete")

    def workspace(self):
        return self.workspace

    def server(self):
        return self.server
if __name__ == "__main__":
    App()