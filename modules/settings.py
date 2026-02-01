import json
import os
from pathlib import Path

class Settings:
    """Settings manager for Kiwiyd Antivirus"""
    
    DEFAULT_SETTINGS = {
        "scan": {
            "default_mode": "Fast Scan",
            "enable_auto_scan": False,
            "auto_scan_time": "00:00",  # HH:MM format
            "auto_scan_path": "C:\\",
            "auto_scan_mode": "Fast Scan",
            "thread_count": 4,  # Number of threads for scanning
            "last_directory": "C:\\",
        },
        "quarantine": {
            "auto_quarantine": True,
            "auto_delete_after_days": 30,
        },
        "updates": {
            "auto_update": True,
            "update_check_interval": 24,  # hours
        },
        "notifications": {
            "enable_notifications": True,
            "show_scan_results": True,
        }
    }
    
    def __init__(self, settings_file: str = "data/settings.json"):
        """Initialize settings manager"""
        self.settings_file = settings_file
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """Load settings from file or create defaults"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}. Using defaults.")
                return self.DEFAULT_SETTINGS.copy()
        else:
            # Create settings file with defaults
            self._save_settings(self.DEFAULT_SETTINGS.copy())
            return self.DEFAULT_SETTINGS.copy()
    
    def _save_settings(self, settings: dict) -> bool:
        """Save settings to file"""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Get setting value by dot notation (e.g., 'scan.default_mode')"""
        keys = key.split('.')
        value = self.settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set(self, key: str, value) -> bool:
        """Set setting value by dot notation (e.g., 'scan.default_mode')"""
        keys = key.split('.')
        settings = self.settings
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        
        # Set the value
        settings[keys[-1]] = value
        
        # Save to file
        return self._save_settings(self.settings)
    
    def get_all(self) -> dict:
        """Get all settings"""
        return self.settings.copy()
    
    def reset_to_defaults(self) -> bool:
        """Reset settings to defaults"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        return self._save_settings(self.settings)
    
    def update_section(self, section: str, data: dict) -> bool:
        """Update entire section"""
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section].update(data)
        return self._save_settings(self.settings)
