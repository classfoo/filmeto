"""
Internationalization utility for managing translations
"""
import os
import logging
from pathlib import Path
from PySide6.QtCore import QTranslator, QCoreApplication, QLocale, QObject, Signal
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class TranslationManager(QObject):
    """Manages application translations"""
    
    # Signal emitted when language changes
    language_changed = Signal(str)
    
    _instance = None
    _current_language = "zh_CN"  # Default to Chinese
    _translators = []
    _app = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TranslationManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self._initialized = True
            self.translations_dir = Path(__file__).parent.parent / "i18n"
            self.available_languages = {
                "zh_CN": "中文",
                "en_US": "English"
            }
    
    def set_app(self, app):
        """Set the QApplication instance"""
        self._app = app
    
    def get_available_languages(self):
        """Get list of available languages"""
        return self.available_languages
    
    def get_current_language(self):
        """Get current language code"""
        return self._current_language
    
    def switch_language(self, language_code):
        """Switch to a different language"""
        if language_code not in self.available_languages:
            logger.warning(f"Language {language_code} not available")
            return False
        
        if not self._app:
            logger.error("Application instance not set")
            return False
        
        # Remove existing translators
        for translator in self._translators:
            self._app.removeTranslator(translator)
        self._translators.clear()
        
        # Load new translator
        if language_code != "zh_CN":  # Chinese is the source language
            translator = QTranslator(self._app)
            qm_file = self.translations_dir / f"filmeto_{language_code}.qm"
            
            if qm_file.exists():
                if translator.load(str(qm_file)):
                    self._app.installTranslator(translator)
                    self._translators.append(translator)
                    self._current_language = language_code
                    logger.info(f"✅ Switched to language: {language_code}")
                    # Emit signal to notify all widgets
                    self.language_changed.emit(language_code)
                    return True
                else:
                    logger.error(f"⚠️ Failed to load translation file: {qm_file}")
            else:
                logger.warning(f"⚠️ Translation file not found: {qm_file}")
        else:
            self._current_language = language_code
            logger.info(f"✅ Switched to language: {language_code}")
            # Emit signal to notify all widgets
            self.language_changed.emit(language_code)
            return True
        
        return False
    
    def get_language_name(self, language_code):
        """Get the display name for a language code"""
        return self.available_languages.get(language_code, language_code)


# Global instance
translation_manager = TranslationManager()


def tr(text):
    """Translate text using Qt's translation system"""
    return QCoreApplication.translate("@default", text)
