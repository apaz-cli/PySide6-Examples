import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QLabel, QTextEdit, QFileDialog, QMessageBox,
                                QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class TextEditorTab(QWidget):
    """Text editor with formatting options"""
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # File operations
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self.new_file)
        
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_file)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_file)
        
        save_as_btn = QPushButton("Save As")
        save_as_btn.clicked.connect(self.save_as_file)
        
        # Font controls
        font_combo = QComboBox()
        font_combo.addItems(["Arial", "Times New Roman", "Courier New", "Helvetica"])
        font_combo.currentTextChanged.connect(self.change_font_family)
        
        font_size_combo = QComboBox()
        font_size_combo.addItems(["8", "10", "12", "14", "16", "18", "20", "24", "28", "32"])
        font_size_combo.setCurrentText("12")
        font_size_combo.currentTextChanged.connect(self.change_font_size)
        
        toolbar_layout.addWidget(new_btn)
        toolbar_layout.addWidget(open_btn)
        toolbar_layout.addWidget(save_btn)
        toolbar_layout.addWidget(save_as_btn)
        toolbar_layout.addWidget(QLabel("Font:"))
        toolbar_layout.addWidget(font_combo)
        toolbar_layout.addWidget(QLabel("Size:"))
        toolbar_layout.addWidget(font_size_combo)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("Welcome to the Text Editor!\n\nStart typing your content here...")
        layout.addWidget(self.text_edit)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Connect text change signal
        self.text_edit.textChanged.connect(self.text_changed)
        
    def new_file(self):
        if self.text_edit.document().isModified():
            reply = QMessageBox.question(self, "Unsaved Changes", 
                                       "Do you want to save your changes?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Yes:
                self.save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
                
        self.text_edit.clear()
        self.current_file = None
        self.status_label.setText("New document")
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.text_edit.setPlainText(content)
                    self.current_file = file_path
                    self.status_label.setText(f"Opened: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open file: {str(e)}")
                
    def save_file(self):
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_as_file()
            
    def save_as_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.save_to_file(file_path)
            self.current_file = file_path
            
    def save_to_file(self, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.text_edit.toPlainText())
                self.text_edit.document().setModified(False)
                self.status_label.setText(f"Saved: {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save file: {str(e)}")
            
    def change_font_family(self, family):
        font = self.text_edit.font()
        font.setFamily(family)
        self.text_edit.setFont(font)
        
    def change_font_size(self, size):
        font = self.text_edit.font()
        font.setPointSize(int(size))
        self.text_edit.setFont(font)
        
    def text_changed(self):
        if self.current_file:
            status = f"Modified: {os.path.basename(self.current_file)}"
        else:
            status = "Modified"
        self.status_label.setText(status)