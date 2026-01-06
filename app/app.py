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
from app.ui.main_window import MainWindow
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
            
            # Create main window (critical path - show immediately)
            with TimingContext("Main window creation"):
                logger.info("Creating main window...")
                self.window = MainWindow(self.workspace)
                self.window.showMaximized()
            
            # Process events to ensure window is rendered before heavy operations
            app.processEvents()
            
            # Defer non-critical initialization to background
            logger.info("Starting background initialization...")
            asyncio.ensure_future(self._background_init(loop))
            
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
    
    async def _background_init(self, loop):
        """Initialize non-critical components in background after UI is shown"""
        bg_init_start = time.time()
        logger.info(f"⏱️  [BackgroundInit] Starting background initialization...")
        try:
            # Complete deferred initializations
            logger.info("⏱️  [BackgroundInit] Completing deferred workspace initializations...")
            deferred_start = time.time()
            await loop.run_in_executor(None, self._complete_deferred_init)
            deferred_time = (time.time() - deferred_start) * 1000
            logger.info(f"⏱️  [BackgroundInit] Deferred initializations completed in {deferred_time:.2f}ms")
            
            # Load project data asynchronously
            project_data_start = time.time()
            logger.info("⏱️  [BackgroundInit] Loading project data...")
            # Use executor to avoid blocking the main thread
            await loop.run_in_executor(None, self.workspace.project.load_all_tasks)
            project_data_time = (time.time() - project_data_start) * 1000
            logger.info(f"⏱️  [BackgroundInit] Project data loaded in {project_data_time:.2f}ms")
            
            # Pre-load character and resource managers to avoid blocking UI later
            preload_start = time.time()
            logger.info("⏱️  [BackgroundInit] Pre-loading managers...")
            char_start = time.time()
            await loop.run_in_executor(None, self.workspace.project.character_manager.list_characters)
            char_time = (time.time() - char_start) * 1000
            logger.info(f"⏱️  [BackgroundInit] CharacterManager pre-loaded in {char_time:.2f}ms")
            
            resource_start = time.time()
            await loop.run_in_executor(None, self.workspace.project.resource_manager.get_all)
            resource_time = (time.time() - resource_start) * 1000
            logger.info(f"⏱️  [BackgroundInit] ResourceManager pre-loaded in {resource_time:.2f}ms")
            preload_time = (time.time() - preload_start) * 1000
            logger.info(f"⏱️  [BackgroundInit] Managers pre-loading completed in {preload_time:.2f}ms")
            
            # Start workspace async operations
            workspace_start_start = time.time()
            logger.info("⏱️  [BackgroundInit] Starting workspace...")
            await self.workspace.start()
            workspace_start_time = (time.time() - workspace_start_start) * 1000
            logger.info(f"⏱️  [BackgroundInit] Workspace started in {workspace_start_time:.2f}ms")
            
            # Complete server plugin discovery in background
            server_plugins_start = time.time()
            logger.info("⏱️  [BackgroundInit] Completing server plugin discovery...")
            if hasattr(self.server_manager, '_complete_plugin_discovery'):
                self.server_manager._complete_plugin_discovery()
            server_plugins_time = (time.time() - server_plugins_start) * 1000
            logger.info(f"⏱️  [BackgroundInit] Server plugin discovery completed in {server_plugins_time:.2f}ms")
            
            total_bg_time = (time.time() - bg_init_start) * 1000
            logger.info(f"⏱️  [BackgroundInit] Background initialization complete in {total_bg_time:.2f}ms")
        except Exception as e:
            logger.error(f"Error in background initialization: {e}", exc_info=True)
    
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