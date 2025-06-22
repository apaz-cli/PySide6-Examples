"""
Styled Monaco Editor Widget
A Monaco Editor widget that integrates with the theme system.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from monaco_widget import MonacoEditorWidget
from theme_manager import theme_manager


class StyledMonacoWidget(QWidget):
    """Monaco Editor widget with integrated theming"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_theme()
    
    def setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create Monaco editor
        self.monaco_editor = MonacoEditorWidget()
        
        # Check if Monaco is available
        if hasattr(self.monaco_editor, 'monaco_interface'):
            layout.addWidget(self.monaco_editor)
            self.editor_available = True
            # Wait for editor to be ready before applying theme
            self.monaco_editor.editor_ready.connect(self.on_editor_ready)
        else:
            # Fallback if Monaco is not available
            self.create_fallback_ui(layout)
            self.editor_available = False
            self.apply_theme()
    
    def create_fallback_ui(self, layout):
        """Create fallback UI when Monaco is not available"""
        fallback_label = QLabel("Monaco Editor not available")
        fallback_label.setAlignment(Qt.AlignCenter)
        fallback_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 14px;
                font-weight: bold;
                padding: 20px;
                background-color: rgba(255, 255, 255, 100);
                border: 2px dashed #e74c3c;
                border-radius: 10px;
            }
        """)
        
        info_label = QLabel(
            "To use Monaco Editor:\n"
            "1. Download from: https://github.com/microsoft/monaco-editor/releases\n"
            "2. Extract to 'monaco-editor' folder\n"
            "3. Ensure structure: monaco-editor/min/vs/loader.js"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 12px;
                padding: 10px;
                background-color: rgba(255, 255, 255, 80);
                border-radius: 5px;
            }
        """)
        
        layout.addWidget(fallback_label)
        layout.addWidget(info_label)
        layout.addStretch()
    
    def connect_theme(self):
        """Connect to theme manager"""
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def on_editor_ready(self):
        """Called when Monaco editor is ready"""
        self.apply_theme()
        
        # Apply any pending content or language
        if hasattr(self, '_pending_content'):
            self.monaco_editor.set_content(self._pending_content)
            delattr(self, '_pending_content')
        
        if hasattr(self, '_pending_language'):
            self.monaco_editor.set_language(self._pending_language)
            delattr(self, '_pending_language')
    
    def apply_theme(self):
        """Apply current theme to the widget"""
        if self.editor_available and self.monaco_editor.is_ready():
            # Apply Monaco theme
            monaco_theme = theme_manager.get_monaco_theme()
            self.monaco_editor.set_theme(monaco_theme)
        elif not self.editor_available:
            # Update fallback UI styling
            colors = theme_manager.get_colors()
            fallback_style = f"""
                QLabel {{
                    color: {colors['accent']};
                    font-size: 14px;
                    font-weight: bold;
                    padding: 20px;
                    background-color: {colors['input_bg']};
                    border: 2px dashed {colors['accent']};
                    border-radius: 10px;
                }}
            """
            
            info_style = f"""
                QLabel {{
                    color: {colors['text_secondary']};
                    font-size: 12px;
                    padding: 10px;
                    background-color: {colors['background'].replace('120', '80')};
                    border-radius: 5px;
                }}
            """
            
            # Apply styles to fallback widgets
            for child in self.findChildren(QLabel):
                if "Monaco Editor not available" in child.text():
                    child.setStyleSheet(fallback_style)
                elif "To use Monaco Editor" in child.text():
                    child.setStyleSheet(info_style)
    
    # Proxy methods to Monaco editor
    def set_content(self, content):
        """Set editor content"""
        if self.editor_available and self.monaco_editor.is_ready():
            self.monaco_editor.set_content(content)
        elif self.editor_available:
            # Store content to set when ready
            self._pending_content = content
    
    def get_content(self):
        """Get editor content"""
        if self.editor_available:
            return self.monaco_editor.get_content()
        return ""
    
    def set_language(self, language):
        """Set editor language"""
        if self.editor_available and self.monaco_editor.is_ready():
            self.monaco_editor.set_language(language)
        elif self.editor_available:
            # Store language to set when ready
            self._pending_language = language
    
    def detect_language_from_filename(self, filename):
        """Detect and set language from filename"""
        if self.editor_available:
            return self.monaco_editor.detect_language_from_filename(filename)
        return "plaintext"
    
    def format_document(self):
        """Format the document"""
        if self.editor_available:
            self.monaco_editor.format_document()
    
    def focus(self):
        """Focus the editor"""
        if self.editor_available:
            self.monaco_editor.focus()
    
    def insert_text(self, text):
        """Insert text at cursor"""
        if self.editor_available:
            self.monaco_editor.insert_text(text)
    
    def is_ready(self):
        """Check if editor is ready"""
        if self.editor_available:
            return self.monaco_editor.is_ready()
        return False
    
    @property
    def content_changed(self):
        """Content changed signal"""
        if self.editor_available:
            return self.monaco_editor.content_changed
        # Return a dummy signal for fallback
        from PySide6.QtCore import Signal
        return Signal(str)
    
    @property
    def editor_ready(self):
        """Editor ready signal"""
        if self.editor_available:
            return self.monaco_editor.editor_ready
        # Return a dummy signal for fallback
        from PySide6.QtCore import Signal
        return Signal()
