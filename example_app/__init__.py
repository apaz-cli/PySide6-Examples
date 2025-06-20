"""
Tabs package for PySide6 Multi-Tab Application
Contains all individual tab implementations
"""

__version__ = "1.0.0"
__author__ = "PySide6 Multi-Tab Example"

# Import all tab classes for easy access
from .calculator_tab import CalculatorTab
from .todo_tab import TodoTab
from .drawing_tab import DrawingTab
from .data_visualization_tab import DataVisualizationTab
from .settings_tab import SettingsTab
from .html_render_tab import HTMLRenderTab
from .text_editor_tab import TextEditorTab
from .image_viewer_tab import ImageViewerTab
from .media_player_tab import MediaPlayerTab
from .notification_tab import NotificationTab

__all__ = [
    'CalculatorTab',
    'TodoTab', 
    'DrawingTab',
    'DataVisualizationTab',
    'SettingsTab',
    'HTMLRenderTab',
    'TextEditorTab',
    'ImageViewerTab',
    'MediaPlayerTab',
    'NotificationTab'
]