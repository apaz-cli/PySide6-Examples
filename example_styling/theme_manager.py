"""
Theme Manager for PySide6 Applications
Provides centralized styling and theme management.
"""

import os
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class ThemeManager(QObject):
    """Centralized theme management for consistent styling"""
    
    theme_changed = Signal(bool)  # dark_mode
    font_changed = Signal(str, float)  # font_family, font_size
    
    def __init__(self):
        super().__init__()
        self.dark_mode = self._detect_system_theme()
        self.current_font_family = 'lemon'
        self.current_font_size = 15.0
    
    def _detect_system_theme(self):
        """Detect if the system is using dark theme"""
        import platform
        import subprocess
        
        system = platform.system()
        
        try:
            if system == "Darwin":  # macOS
                result = subprocess.run([
                    "defaults", "read", "-g", "AppleInterfaceStyle"
                ], capture_output=True, text=True, timeout=2)
                return result.returncode == 0 and "Dark" in result.stdout
            
            elif system == "Windows":
                try:
                    import winreg
                    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                    key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    winreg.CloseKey(key)
                    return value == 0  # 0 = dark theme, 1 = light theme
                except (ImportError, OSError):
                    pass
            
            elif system == "Linux":
                # Try GNOME/GTK settings
                try:
                    result = subprocess.run([
                        "gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"
                    ], capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        theme_name = result.stdout.strip().strip("'\"").lower()
                        return "dark" in theme_name
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                
                # Try KDE settings
                try:
                    result = subprocess.run([
                        "kreadconfig5", "--group", "General", "--key", "ColorScheme"
                    ], capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        scheme = result.stdout.strip().lower()
                        return "dark" in scheme or "breeze dark" in scheme
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                
                # Check environment variables
                if "DESKTOP_SESSION" in os.environ:
                    session = os.environ["DESKTOP_SESSION"].lower()
                    if "dark" in session:
                        return True
        
        except Exception:
            pass
        
        # Fallback to light theme if detection fails
        return False
    
    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.theme_changed.emit(self.dark_mode)
    
    def set_dark_mode(self, enabled):
        """Set dark mode state"""
        if self.dark_mode != enabled:
            self.dark_mode = enabled
            self.theme_changed.emit(self.dark_mode)
    
    def set_font(self, font_family, font_size=None):
        """Set global font family and optionally size"""
        if font_size is None:
            font_size = self.current_font_size
        
        if self.current_font_family != font_family or self.current_font_size != font_size:
            self.current_font_family = font_family
            self.current_font_size = font_size
            self.font_changed.emit(font_family, font_size)
            # Also emit theme changed to trigger style updates
            self.theme_changed.emit(self.dark_mode)
    
    def get_colors(self):
        """Get color palette for current theme"""
        if self.dark_mode:
            return {
                'primary': '#3498db',
                'secondary': '#2ecc71',
                'accent': '#e74c3c',
                'purple': '#9b59b6',
                'background': 'rgba(44, 62, 80, 120)',
                'background_strong': 'rgba(44, 62, 80, 150)',
                'text': '#ecf0f1',
                'text_secondary': '#bdc3c7',
                'border': '#7f8c8d',
                'hover': 'rgba(52, 152, 219, 0.3)',
                'hover_light': 'rgba(52, 152, 219, 0.1)',
                'button_bg': '#34495e',
                'button_hover': '#2c3e50',
                'button_pressed': '#1a252f',
                'input_bg': 'rgba(52, 73, 94, 100)',
                'slider_groove': '#34495e',
                'overlay': 'rgba(30, 30, 30, 0.7)'
            }
        else:
            return {
                'primary': '#4a90e2',
                'secondary': '#27ae60',
                'accent': '#e74c3c',
                'purple': '#9b59b6',
                'background': 'rgba(255, 255, 255, 120)',
                'background_strong': 'rgba(255, 255, 255, 150)',
                'text': '#2c3e50',
                'text_secondary': '#7f8c8d',
                'border': '#bdc3c7',
                'hover': 'rgba(74, 144, 226, 0.3)',
                'hover_light': 'rgba(74, 144, 226, 0.1)',
                'button_bg': '#4a90e2',
                'button_hover': '#357abd',
                'button_pressed': '#2968a3',
                'input_bg': 'rgba(255, 255, 255, 100)',
                'slider_groove': '#ddd',
                'overlay': 'rgba(255, 255, 255, 0.7)'
            }
    
    def get_widget_style(self, widget_type, **options):
        """Unified widget styling method"""
        colors = self.get_colors()
        
        if widget_type == 'group_box':
            border_color = colors.get(options.get('border_color', 'primary'), colors['primary'])
            return f"""
                QGroupBox {{
                    background-color: {colors['background']};
                    border: 2px solid {border_color};
                    border-radius: 10px;
                    padding-top: 20px;
                    font-family: '{self.current_font_family}';
                    font-size: {self.current_font_size}pt;
                    font-weight: normal;
                    color: {colors['text']};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    padding: 0 10px;
                    color: {colors['text']};
                }}
            """
        
        elif widget_type == 'button':
            return f"""
                QPushButton {{
                    background-color: {colors['button_bg']};
                    color: white;
                    border: {'1px solid ' + colors['border'] if self.dark_mode else 'none'};
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-family: '{self.current_font_family}';
                    font-size: {max(7.5, self.current_font_size * 0.83)}pt;
                    font-weight: normal;
                }}
                QPushButton:hover {{
                    background-color: {colors['button_hover']};
                    {('border-color: ' + colors['text_secondary'] + ';') if self.dark_mode else ''}
                }}
                QPushButton:pressed {{
                    background-color: {colors['button_pressed']};
                }}
            """
        
        elif widget_type == 'slider':
            return f"""
                QSlider::groove:horizontal {{
                    height: 8px;
                    background: {colors['slider_groove']};
                    border-radius: 4px;
                }}
                QSlider::handle:horizontal {{
                    background: {colors['primary']};
                    width: 20px;
                    margin: -6px 0;
                    border-radius: 10px;
                }}
            """
        
        elif widget_type == 'label':
            alpha = options.get('background_alpha', 80)
            size = options.get('font_size', 12.5)
            padding = options.get('padding', 10)
            bg_color = colors['background'].replace('120', str(alpha))
            return f"""
                QLabel {{
                    color: {colors['text']};
                    font-family: '{self.current_font_family}';
                    font-size: {max(7.5, size if size != 12.5 else self.current_font_size * 0.83)}pt;
                    padding: {padding}px;
                    background-color: {bg_color};
                    border-radius: 5px;
                }}
            """
        
        elif widget_type == 'input':
            return f"""
                QComboBox, QLineEdit {{
                    background-color: {colors['input_bg']};
                    border: 1px solid {colors['border']};
                    border-radius: 5px;
                    padding: 5px;
                    font-family: '{self.current_font_family}';
                    font-size: {max(7.5, self.current_font_size * 0.83)}pt;
                    color: {colors['text']};
                }}
                QComboBox::drop-down {{
                    border: none;
                }}
            """
        
        elif widget_type == 'tree':
            return f"""
                QTreeView {{
                    background-color: {colors['background'].replace('120', '80')};
                    border: 1px solid {colors['border']};
                    border-radius: 5px;
                    font-family: '{self.current_font_family}';
                    font-size: {max(7.5, self.current_font_size * 0.83)}pt;
                    color: {colors['text']};
                }}
                QTreeView::item {{
                    padding: 2px;
                }}
                QTreeView::item:selected {{
                    background-color: {colors['hover']};
                }}
                QTreeView::item:hover {{
                    background-color: {colors['hover_light']};
                }}
            """
        
        elif widget_type == 'text':
            return f"color: {colors['text']}; font-family: '{self.current_font_family}'; font-size: {max(7.5, self.current_font_size * 0.83)}pt; font-weight: normal;"
        
        elif widget_type == 'placeholder':
            return f"""
                QLabel {{
                    color: {colors['text_secondary']};
                    font-family: '{self.current_font_family}';
                    font-size: {max(7.5, self.current_font_size * 0.83)}pt;
                    font-style: normal;
                    padding: 20px;
                    background-color: {colors['background'].replace('120', '50')};
                    border: 2px dashed {colors['border']};
                    border-radius: 5px;
                }}
            """
        
        return ""
    
    def get_monaco_theme(self):
        """Get Monaco editor theme name"""
        return 'transparent-dark' if self.dark_mode else 'transparent-light'


# Global theme manager instance
theme_manager = ThemeManager()
