import asyncio
import os
import sys
import logging
import traceback
from datetime import datetime

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from app.app import App
from app.ui.main_window import MainWindow


def setup_crash_logging():
    """Setup logging to capture crash information"""
    # Create logs directory
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"filmeto_{timestamp}.log")
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info(f"Filmeto Application Started - Log file: {log_file}")
    logger.info("=" * 80)
    
    return logger, log_file


def exception_hook(exc_type, exc_value, exc_traceback):
    """Global exception handler to log uncaught exceptions"""
    logger = logging.getLogger(__name__)
    
    # Log the exception
    logger.critical("=" * 80)
    logger.critical("UNCAUGHT EXCEPTION - APPLICATION CRASH")
    logger.critical("=" * 80)
    logger.critical(f"Exception Type: {exc_type.__name__}")
    logger.critical(f"Exception Value: {exc_value}")
    logger.critical("Stack Trace:")
    
    # Format and log the full traceback
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    for line in tb_lines:
        logger.critical(line.rstrip())
    
    logger.critical("=" * 80)
    
    # Also print to stderr for immediate visibility
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


if __name__ == "__main__":
    # Setup crash logging
    logger, log_file = setup_crash_logging()
    
    # Install global exception hook
    sys.excepthook = exception_hook
    
    try:
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        main_path = os.path.abspath(os.path.dirname(__file__))
        logger.info(f"Main path: {main_path}")
        
        app = App(main_path)
        logger.info("App instance created")
        
        app.start()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user (Ctrl+C)")
        sys.exit(0)
    
    except Exception as e:
        logger.critical("=" * 80)
        logger.critical("FATAL ERROR IN MAIN")
        logger.critical("=" * 80)
        logger.critical(f"Exception: {e}")
        logger.critical("Stack trace:", exc_info=True)
        logger.critical("=" * 80)
        
        # Re-raise to trigger sys.excepthook
        raise
    
    finally:
        logger.info("Application terminated")
        logger.info(f"Full log saved to: {log_file}")
