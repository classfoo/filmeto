import asyncio
import os
import sys
import logging
import traceback
import time

from qasync import QEventLoop
from PySide6.QtGui import QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler, QtMsgType

from app.data.workspace import Workspace
from app.ui.window import WindowManager
from server.server import Server, ServerManager
from utils.i18n_utils import translation_manager

logger = logging.getLogger(__name__)

# Performance timing helper
class TimingContext:
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (time.time() - self.start_time) * 1000
        logger.info(f"⏱️  {self.name}: {elapsed:.2f}ms")

def load_stylesheet(main_path):
    """loading QSS style files"""
    import os

    # Load the main dark style
    main_style_file = "style/dark_style.qss"
    combined_stylesheet = ""

    if os.path.exists(main_style_file):
        with open(main_style_file, "r", encoding="utf-8") as f:
            combined_stylesheet = f.read()
    else:
        logger.warning(f"Warning: style file '{main_style_file}' not found, use default.")

    # Load the panel styles
    panel_style_file = "style/panel_styles.qss"
    if os.path.exists(panel_style_file):
        with open(panel_style_file, "r", encoding="utf-8") as f:
            panel_styles = f.read()
            combined_stylesheet += "\n" + panel_styles
    else:
        logger.warning(f"Warning: panel style file '{panel_style_file}' not found.")

    # Load the startup styles
    startup_style_file = "style/startup_styles.qss"
    if os.path.exists(startup_style_file):
        with open(startup_style_file, "r", encoding="utf-8") as f:
            startup_styles = f.read()
            combined_stylesheet += "\n" + startup_styles
    else:
        logger.warning(f"Warning: startup style file '{startup_style_file}' not found.")

    return combined_stylesheet

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
        # Don't log error if font doesn't exist - it's optional
        return None, success_msg, error_msg

    # 检查文件扩展名
    _, ext = os.path.splitext(font_path)
    if ext.lower() not in ['.ttf', '.otf']:
        error_msg += f"警告：字体文件 '{font_path}' 的扩展名 '{ext}' 可能不受支持。请使用 .ttf 或 .otf 格式。\n"
        return None, success_msg, error_msg

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
            startup_start = time.time()
            
            with TimingContext("QApplication creation"):
                logger.info("Creating QApplication...")
                app = QApplication(sys.argv)
            
            with TimingContext("Application icon"):
                icon_path = os.path.join(self.main_path, "textures", "filmeto.png")
                if os.path.exists(icon_path):
                    app.setWindowIcon(QIcon(icon_path))
                    logger.info(f"Application icon set from {icon_path}")
                else:
                    logger.warning(f"Application icon not found at {icon_path}")
            
            with TimingContext("Translation system"):
                logger.info("Initializing translation system...")
                translation_manager.set_app(app)
                translation_manager.switch_language("zh_CN")
            
            with TimingContext("Event loop setup"):
                logger.info("Setting up event loop...")
                loop = QEventLoop(app)
                asyncio.set_event_loop(loop)
            
            with TimingContext("Custom font loading"):
                logger.info("Loading custom font...")
                load_custom_font(self.main_path)
            
            with TimingContext("Stylesheet loading"):
                logger.info("Loading stylesheet...")
                app.setStyleSheet(load_stylesheet(self.main_path))
            
            # Initialize workspace (minimal - defer heavy operations)
            with TimingContext("Workspace initialization"):
                logger.info("Initializing workspace...")
                workspacePath = os.path.join(self.main_path, "workspace")
                self.workspace = Workspace(workspacePath, "demo", load_data=False, defer_heavy_init=True)
            
            # Initialize server manager (defer plugin discovery)
            with TimingContext("Server manager initialization"):
                logger.info("Initializing server manager...")
                workspacePath = os.path.join(self.main_path, "workspace")
                self.server_manager = ServerManager(workspacePath, defer_plugin_discovery=True)
                self.server = self.server_manager.get_server("local")
            
            # Complete deferred initializations synchronously
            with TimingContext("Deferred initializations"):
                logger.info("Completing deferred workspace initializations...")
                self._complete_deferred_init()
            
            # Load project data synchronously
            with TimingContext("Project data loading"):
                logger.info("Loading project data...")
                self._load_project_tasks()
            
            # Pre-load actor and resource managers
            with TimingContext("Managers pre-loading"):
                logger.info("Pre-loading managers...")
                self.workspace.project.character_manager.list_characters()
                self.workspace.project.resource_manager.get_all()
            
            # Complete server plugin discovery
            with TimingContext("Server plugin discovery"):
                logger.info("Completing server plugin discovery...")
                if hasattr(self.server_manager, '_complete_plugin_discovery'):
                    self.server_manager._complete_plugin_discovery()
            
            # Create window manager and show startup window
            with TimingContext("Window manager creation"):
                logger.info("Creating window manager...")
                self.window_manager = WindowManager(self.workspace)
                self.window_manager.show_startup_window()
            
            # Refresh the startup page project list
            with TimingContext("Project list refresh"):
                logger.info("Refreshing startup page project list...")
                self.window_manager.refresh_projects()
            
            # Register cleanup on application exit
            logger.info("Registering cleanup handlers...")
            app.aboutToQuit.connect(self._cleanup_on_exit)
            
            total_startup_time = (time.time() - startup_start) * 1000
            logger.info(f"🚀 Startup complete in {total_startup_time:.2f}ms")
            
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
    

    
    def _load_project_tasks(self):
        """Load all tasks from all timeline items"""
        logger.info("⏱️  [BackgroundInit] Loading all project tasks...")
        start_time = time.time()

        # Get all timeline items and load their tasks
        timeline = self.workspace.project.get_timeline()
        item_count = timeline.get_item_count()

        loaded_task_count = 0
        for i in range(1, item_count + 1):  # Timeline items start from index 1
            try:
                item = timeline.get_item(i)
                task_manager = item.get_task_manager()  # This will load tasks automatically
                task_count = task_manager.get_task_count()
                loaded_task_count += task_count
                logger.info(f"⏱️  [BackgroundInit] Loaded {task_count} tasks for timeline item {i}")
            except Exception as e:
                logger.error(f"⏱️  [BackgroundInit] Error loading tasks for timeline item {i}: {e}")

        total_time = (time.time() - start_time) * 1000
        logger.info(f"⏱️  [BackgroundInit] Loaded {loaded_task_count} tasks from {item_count} timeline items in {total_time:.2f}ms")

    def _complete_deferred_init(self):
        """Complete deferred initializations synchronously (runs in executor)"""
        init_start = time.time()
        logger.info(f"⏱️  [DeferredInit] Starting deferred workspace initializations...")

        # Complete ProjectManager scan
        if hasattr(self.workspace.project_manager, 'ensure_projects_loaded'):
            pm_start = time.time()
            logger.info(f"⏱️  [DeferredInit] Completing ProjectManager scan...")
            self.workspace.project_manager.ensure_projects_loaded()
            pm_time = (time.time() - pm_start) * 1000
            logger.info(f"⏱️  [DeferredInit] ProjectManager scan completed in {pm_time:.2f}ms")

        # Complete Settings loading
        if hasattr(self.workspace.settings, '_ensure_loaded'):
            settings_start = time.time()
            logger.info(f"⏱️  [DeferredInit] Loading Settings...")
            self.workspace.settings._ensure_loaded()
            settings_time = (time.time() - settings_start) * 1000
            logger.info(f"⏱️  [DeferredInit] Settings loaded in {settings_time:.2f}ms")

        # Complete Plugins discovery
        if hasattr(self.workspace.plugins, 'ensure_discovery'):
            plugins_start = time.time()
            logger.info(f"⏱️  [DeferredInit] Discovering Plugins...")
            self.workspace.plugins.ensure_discovery()
            plugins_time = (time.time() - plugins_start) * 1000
            logger.info(f"⏱️  [DeferredInit] Plugins discovery completed in {plugins_time:.2f}ms")

        total_time = (time.time() - init_start) * 1000
        logger.info(f"⏱️  [DeferredInit] All deferred initializations completed in {total_time:.2f}ms")
    
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