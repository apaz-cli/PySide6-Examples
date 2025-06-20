#!/usr/bin/env python3
"""
PySide6 Multi-Tab Example Application
Main entry point and application window
"""

import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
)
from PySide6.QtCore import Qt

# Import all tab modules
from calculator_tab import CalculatorTab
from todo_tab import TodoTab
from drawing_tab import DrawingTab
from data_visualization_tab import DataVisualizationTab
from settings_tab import SettingsTab
from html_render_tab import HTMLRenderTab
from text_editor_tab import TextEditorTab
from image_viewer_tab import ImageViewerTab
from media_player_tab import MediaPlayerTab
from notification_tab import NotificationTab
from monaco_tab import MonacoEditorWidget


class MultiTabApp(QMainWindow):
    """Main application window with multiple tabs"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("PySide6 Multi-Tab Example Application")
        self.setGeometry(100, 100, 900, 700)

        # Create central widget and tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Add all tabs
        self.add_tabs()

        # Status bar
        self.statusBar().showMessage("Ready")

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.tab_changed)

    def add_tabs(self):
        """Add all tabs to the tab widget"""
        tabs = [
            (CalculatorTab(), "Calculator"),
            (TodoTab(), "Todo List"),
            (DrawingTab(), "Drawing"),
            (DataVisualizationTab(), "Charts"),
            (SettingsTab(), "Settings"),
            (HTMLRenderTab(), "HTML Renderer"),
            (TextEditorTab(), "Text Editor"),
            (ImageViewerTab(), "Image Viewer"),
            (MediaPlayerTab(), "Media Player"),
            (NotificationTab(), "Notifications"),
            (MonacoEditorWidget(), "Monaco Editor"),
        ]

        for tab_widget, tab_name in tabs:
            self.tab_widget.addTab(tab_widget, tab_name)

    def tab_changed(self, index):
        """Handle tab change events"""
        tab_names = [
            "Calculator",
            "Todo List",
            "Drawing",
            "Charts",
            "Settings",
            "HTML Renderer",
            "Text Editor",
            "Image Viewer",
            "Media Player",
            "Notifications",
            "Monaco Editor",
        ]
        if index < len(tab_names):
            self.statusBar().showMessage(f"Current tab: {tab_names[index]}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("PySide6 Multi-Tab Example")

    # Create and show the main window
    window = MultiTabApp()
    window.show()

    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
