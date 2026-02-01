"""
Internationalization (i18n) module for language support.
Manages translations for the application UI.
"""

import json
import os
from pathlib import Path


class Translator:
    """Manages translations and language switching."""
    
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "ru": "Русский",
    }
    
    def __init__(self, translations_file: str = None):
        """Initialize translator with translations file.
        
        Args:
            translations_file: Path to translations.json file
        """
        self.current_language = "en"
        self.translations = {}
        
        if translations_file is None:
            # Default to data/translations.json
            translations_file = Path(__file__).parent.parent / "data" / "translations.json"
        
        self.translations_file = Path(translations_file)
        self._load_translations()
    
    def _load_translations(self):
        """Load translations from JSON file."""
        if not self.translations_file.exists():
            print(f"Warning: translations file not found at {self.translations_file}")
            return
        
        try:
            with open(self.translations_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except Exception as e:
            print(f"Error loading translations: {e}")
            self.translations = {}
    
    def set_language(self, language_code: str) -> bool:
        """Set the active language.
        
        Args:
            language_code: Language code (e.g., 'en', 'ru')
            
        Returns:
            True if language was set successfully, False otherwise
        """
        if language_code not in self.SUPPORTED_LANGUAGES:
            print(f"Unsupported language: {language_code}")
            return False
        
        self.current_language = language_code
        return True
    
    def get_language(self) -> str:
        """Get current language code."""
        return self.current_language
    
    def get_language_name(self, language_code: str = None) -> str:
        """Get display name for a language.
        
        Args:
            language_code: Language code (uses current if None)
            
        Returns:
            Display name for the language
        """
        if language_code is None:
            language_code = self.current_language
        
        return self.SUPPORTED_LANGUAGES.get(language_code, language_code)
    
    def get_supported_languages(self) -> dict:
        """Get all supported languages.
        
        Returns:
            Dictionary of {code: name} pairs
        """
        return self.SUPPORTED_LANGUAGES.copy()
    
    def translate(self, key: str, default: str = None) -> str:
        """Translate a key to the current language.
        
        Args:
            key: Translation key (dot-separated path, e.g., 'ui.button.scan')
            default: Default value if translation not found
            
        Returns:
            Translated string or default value or key itself
        """
        # Navigate through nested dictionary using dot notation
        keys = key.split('.')
        current = self.translations
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                # Key not found, return default or key itself
                return default if default is not None else key
        
        # Check if we have a language-specific translation
        if isinstance(current, dict) and self.current_language in current:
            return current[self.current_language]
        elif isinstance(current, str):
            return current
        else:
            return default if default is not None else key
    
    def t(self, key: str, default: str = None) -> str:
        """Shorthand for translate().
        
        Args:
            key: Translation key
            default: Default value if translation not found
            
        Returns:
            Translated string
        """
        return self.translate(key, default)


# Global translator instance
_translator = None


def init_translator(translations_file: str = None) -> Translator:
    """Initialize the global translator instance.
    
    Args:
        translations_file: Path to translations.json file
        
    Returns:
        Global translator instance
    """
    global _translator
    _translator = Translator(translations_file)
    return _translator


def get_translator() -> Translator:
    """Get the global translator instance.
    
    Returns:
        Global translator instance
    """
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def t(key: str, default: str = None) -> str:
    """Convenience function for translation.
    
    Args:
        key: Translation key
        default: Default value if translation not found
        
    Returns:
        Translated string
    """
    return get_translator().t(key, default)


def set_language(language_code: str) -> bool:
    """Set the application language.
    
    Args:
        language_code: Language code (e.g., 'en', 'ru')
        
    Returns:
        True if language was set successfully
    """
    return get_translator().set_language(language_code)
