"""
Simple example application demonstrating the Monaco Editor Widget
"""

import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                               QHBoxLayout, QWidget, QPushButton, 
                               QFileDialog, QMessageBox, QComboBox, QLabel)

# Import the Monaco Editor Widget
from monaco_widget import MonacoEditorWidget


class MonacoEditorApp(QMainWindow):
    """Simple example application using the Monaco Editor Widget"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monaco Editor - PySide6")
        self.setGeometry(100, 100, 1200, 800)
        
        self.current_file_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        
        # File operations
        self.new_btn = QPushButton("New")
        self.open_btn = QPushButton("Open File")
        self.save_btn = QPushButton("Save File")
        
        # Language selector
        self.language_label = QLabel("Language:")
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            "javascript", "python", "html", "css", "json", 
            "xml", "markdown", "sql", "cpp", "java", "csharp"
        ])
        
        # Add widgets to toolbar
        toolbar_layout.addWidget(self.new_btn)
        toolbar_layout.addWidget(self.open_btn)
        toolbar_layout.addWidget(self.save_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.language_label)
        toolbar_layout.addWidget(self.language_combo)
        
        layout.addLayout(toolbar_layout)
        
        # Monaco Editor Widget
        self.monaco_editor = MonacoEditorWidget()
        layout.addWidget(self.monaco_editor)
        
        # Connect signals
        self.new_btn.clicked.connect(self.new_file)
        self.open_btn.clicked.connect(self.open_file)
        self.save_btn.clicked.connect(self.save_file)
        self.language_combo.currentTextChanged.connect(self.change_language)
        self.monaco_editor.content_changed.connect(self.on_content_changed)
    
    def on_content_changed(self, content):
        """Called when editor content changes"""
        # Update window title if file is open
        if self.current_file_path:
            filename = os.path.basename(self.current_file_path)
            self.setWindowTitle(f"Monaco Editor - {filename} *")
    
    def new_file(self):
        """Create a new file"""
        self.monaco_editor.set_content("")
        self.current_file_path = None
        self.setWindowTitle("Monaco Editor - New File")
    
    def open_file(self):
        """Open a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Files (*);;Text Files (*.txt);;Python Files (*.py);;JavaScript Files (*.js);;HTML Files (*.html)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                self.monaco_editor.set_content(content)
                
                # Auto-detect and set language
                language = self.monaco_editor.detect_language_from_filename(file_path)
                
                # Update language combo
                index = self.language_combo.findText(language)
                if index >= 0:
                    self.language_combo.setCurrentIndex(index)
                
                self.current_file_path = file_path
                filename = os.path.basename(file_path)
                self.setWindowTitle(f"Monaco Editor - {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {str(e)}")
    
    def save_file(self):
        """Save the file"""
        if self.current_file_path:
            self.save_to_file(self.current_file_path)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """Save file as"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "All Files (*);;Text Files (*.txt);;Python Files (*.py);;JavaScript Files (*.js);;HTML Files (*.html)"
        )
        
        if file_path:
            self.save_to_file(file_path)
            self.current_file_path = file_path
            filename = os.path.basename(file_path)
            self.setWindowTitle(f"Monaco Editor - {filename}")
    
    def save_to_file(self, file_path):
        """Save content to file"""
        try:
            content = self.monaco_editor.get_content()
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            filename = os.path.basename(file_path)
            self.setWindowTitle(f"Monaco Editor - {filename}")
            QMessageBox.information(self, "Success", "File saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {str(e)}")
    
    def change_language(self, language):
        """Change the programming language"""
        self.monaco_editor.set_language(language)
    
    def closeEvent(self, event):
        """Handle application close"""
        self.monaco_editor.cleanup()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    window = MonacoEditorApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()