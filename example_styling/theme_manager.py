"""
Theme Manager for PySide6 Applications
Provides centralized styling and theme management.
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor


class ThemeManager(QObject):
    """Centralized theme management for consistent styling"""
    
    theme_changed = Signal(bool)  # dark_mode
    
    def __init__(self):
        super().__init__()
        self.dark_mode = False
    
    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.theme_changed.emit(self.dark_mode)
    
    def set_dark_mode(self, enabled):
        """Set dark mode state"""
        if self.dark_mode != enabled:
            self.dark_mode = enabled
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
    
    def get_group_box_style(self, border_color_key='primary'):
        """Get group box stylesheet"""
        colors = self.get_colors()
        return f"""
            QGroupBox {{
                background-color: {colors['background']};
                border: 2px solid {colors[border_color_key]};
                border-radius: 10px;
                padding-top: 20px;
                font-size: 14px;
                font-weight: bold;
                color: {colors['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                padding: 0 10px;
                color: {colors['text']};
            }}
        """
    
    def get_button_style(self):
        """Get button stylesheet"""
        colors = self.get_colors()
        return f"""
            QPushButton {{
                background-color: {colors['button_bg']};
                color: white;
                border: {'1px solid ' + colors['border'] if self.dark_mode else 'none'};
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
                {('border-color: ' + colors['text_secondary'] + ';') if self.dark_mode else ''}
            }}
            QPushButton:pressed {{
                background-color: {colors['button_pressed']};
            }}
        """
    
    def get_slider_style(self):
        """Get slider stylesheet"""
        colors = self.get_colors()
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
    
    def get_label_style(self, background_alpha=80):
        """Get label stylesheet"""
        colors = self.get_colors()
        bg_color = colors['background'].replace('120', str(background_alpha))
        return f"""
            QLabel {{
                color: {colors['text']};
                font-size: 13px;
                padding: 10px;
                background-color: {bg_color};
                border-radius: 5px;
            }}
        """
    
    def get_combo_box_style(self):
        """Get combo box stylesheet"""
        colors = self.get_colors()
        return f"""
            QComboBox {{
                background-color: {colors['input_bg']};
                border: 1px solid {colors['border']};
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
                color: {colors['text']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
        """
    
    def get_tree_view_style(self):
        """Get tree view stylesheet"""
        colors = self.get_colors()
        return f"""
            QTreeView {{
                background-color: {colors['background'].replace('120', '80')};
                border: 1px solid {colors['border']};
                border-radius: 5px;
                font-size: 12px;
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
    
    def get_small_label_style(self, background_alpha=60):
        """Get small label stylesheet"""
        colors = self.get_colors()
        bg_color = colors['background'].replace('120', str(background_alpha))
        return f"""
            QLabel {{
                color: {colors['text']};
                font-size: 11px;
                padding: 5px;
                background-color: {bg_color};
                border-radius: 3px;
            }}
        """
    
    def get_text_label_style(self):
        """Get text label stylesheet (for slider labels, etc.)"""
        colors = self.get_colors()
        return f"color: {colors['text']}; font-weight: bold;"
    
    def get_monaco_theme(self):
        """Get Monaco editor theme name"""
        return 'transparent-dark' if self.dark_mode else 'transparent-light'
    
    def get_placeholder_content_style(self):
        """Get placeholder content stylesheet"""
        colors = self.get_colors()
        return f"""
            QLabel {{
                color: {colors['text_secondary']};
                font-size: 12px;
                font-style: italic;
                padding: 20px;
                background-color: {colors['background'].replace('120', '50')};
                border: 2px dashed {colors['border']};
                border-radius: 5px;
            }}
        """


# Global theme manager instance
theme_manager = ThemeManager()
