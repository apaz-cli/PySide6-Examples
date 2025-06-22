"""
Settings persistence for the application
Handles loading and saving user preferences to platform-appropriate locations.
"""

import json
import os
from pathlib import Path
from PySide6.QtCore import QObject, Signal


class SettingsManager(QObject):
    """Manages application settings persistence"""
    
    settings_loaded = Signal()
    
    def __init__(self):
        super().__init__()
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.default_settings = {
            "theme": {
                "dark_mode": None,  # None means auto-detect
                "font_family": "lemon",
                "font_size": 15.0
            },
            "ui": {
                "background_opacity": 0.7,
                "background_image": None,
                "window_geometry": None
            },
            "editor": {
                "minimap_enabled": True,
                "word_wrap": True,
                "line_numbers": True
            }
        }
        self.settings = self.default_settings.copy()
        self._ensure_config_dir()
    
    def _get_config_dir(self):
        """Get platform-appropriate config directory"""
        import platform
        
        system = platform.system()
        
        if system == "Windows":
            # Use AppData/Roaming
            base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
            return Path(base_dir) / "PerfWizard"
        
        elif system == "Darwin":  # macOS
            # Use ~/Library/Application Support
            return Path.home() / "Library" / "Application Support" / "PerfWizard"
        
        else:  # Linux and others
            # Use XDG_CONFIG_HOME or ~/.config
            config_home = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            return Path(config_home) / "perfwizard"
    
    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_settings(self):
        """Load settings from config file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Merge with defaults to handle new settings
                self.settings = self._merge_settings(self.default_settings, loaded_settings)
                
            except Exception as e:
                print(f"Error loading settings: {e}")
                self.settings = self.default_settings.copy()
        else:
            self.settings = self.default_settings.copy()
        
        self.settings_loaded.emit()
        return self.settings
    
    def save_settings(self):
        """Save current settings to config file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def _merge_settings(self, defaults, loaded):
        """Recursively merge loaded settings with defaults"""
        result = defaults.copy()
        
        for key, value in loaded.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = self._merge_settings(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def get(self, section, key, default=None):
        """Get a setting value"""
        return self.settings.get(section, {}).get(key, default)
    
    def set(self, section, key, value):
        """Set a setting value"""
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value
    
    def get_theme_settings(self):
        """Get theme-related settings"""
        return self.settings.get("theme", {})
    
    def set_theme_settings(self, dark_mode, font_family, font_size):
        """Set theme-related settings"""
        self.settings["theme"] = {
            "dark_mode": dark_mode,
            "font_family": font_family,
            "font_size": font_size
        }
    
    def get_ui_settings(self):
        """Get UI-related settings"""
        return self.settings.get("ui", {})
    
    def set_ui_settings(self, background_opacity, background_image=None, window_geometry=None):
        """Set UI-related settings"""
        ui_settings = self.settings.get("ui", {})
        ui_settings["background_opacity"] = background_opacity
        if background_image is not None:
            ui_settings["background_image"] = background_image
        if window_geometry is not None:
            ui_settings["window_geometry"] = window_geometry
        self.settings["ui"] = ui_settings
    
    def get_editor_settings(self):
        """Get editor-related settings"""
        return self.settings.get("editor", {})
    
    def set_editor_settings(self, **kwargs):
        """Set editor-related settings"""
        editor_settings = self.settings.get("editor", {})
        editor_settings.update(kwargs)
        self.settings["editor"] = editor_settings


# Global settings manager instance
settings_manager = SettingsManager()
