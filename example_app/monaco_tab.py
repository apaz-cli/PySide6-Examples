"""
Monaco Editor Widget for PySide6
A reusable widget that embeds the Monaco Editor (VS Code editor) in a PySide6 application.

Usage:
    from monaco_widget import MonacoEditorWidget
    
    widget = MonacoEditorWidget()
    widget.set_content("print('Hello World')")
    widget.set_language("python")
"""

import os
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QObject, Slot, Signal
from PySide6.QtWebChannel import QWebChannel


class MonacoInterface(QObject):
    """Interface between Python and Monaco Editor JavaScript"""
    
    content_changed = Signal(str)
    editor_ready = Signal()
    
    def __init__(self):
        super().__init__()
        self.current_content = ""
        self._editor_ready = False
    
    @Slot(str)
    def update_content(self, content):
        """Called from JavaScript when editor content changes"""
        self.current_content = content
        self.content_changed.emit(content)
    
    @Slot()
    def editor_initialized(self):
        """Called from JavaScript when editor is ready"""
        self._editor_ready = True
        self.editor_ready.emit()
    
    @property
    def is_ready(self):
        """Check if the editor is ready to receive commands"""
        return self._editor_ready


class MonacoEditorWidget(QWidget):
    """
    A reusable Monaco Editor widget for PySide6 applications.
    
    Signals:
        content_changed(str): Emitted when the editor content changes
        editor_ready(): Emitted when the editor is fully loaded and ready
    
    Example:
        editor = MonacoEditorWidget()
        editor.content_changed.connect(lambda text: print(f"Content: {text}"))
        editor.set_language("python")
        editor.set_content("def hello():\n    print('Hello World')")
    """
    
    # Expose signals from the interface
    content_changed = Signal(str)
    editor_ready = Signal()
    
    def __init__(self, parent=None, monaco_path=None):
        """
        Initialize the Monaco Editor widget.
        
        Args:
            parent: Parent widget
            monaco_path: Path to monaco-editor folder (auto-detected if None)
        """
        super().__init__(parent)
        
        # Find Monaco Editor path
        if monaco_path:
            self.monaco_path = Path(monaco_path)
        else:
            # Look for monaco-editor in same directory as this file
            self.monaco_path = Path(__file__).parent / "monaco-editor"
        
        # Verify Monaco Editor exists
        if not self._verify_monaco_installation():
            return
        
        # Create the Monaco interface
        self.monaco_interface = MonacoInterface()
        
        # Connect signals
        self.monaco_interface.content_changed.connect(self.content_changed.emit)
        self.monaco_interface.editor_ready.connect(self.editor_ready.emit)
        
        # Set up the widget
        self._setup_ui()
        self._create_monaco_html()
    
    def _verify_monaco_installation(self):
        """Verify that Monaco Editor is properly installed"""
        if not self.monaco_path.exists():
            self._show_setup_error("Monaco Editor folder not found", 
                                 f"Expected location: {self.monaco_path}")
            return False
        
        loader_path = self.monaco_path / "min" / "vs" / "loader.js"
        if not loader_path.exists():
            self._show_setup_error("Monaco Editor files incomplete", 
                                 f"Missing: {loader_path}")
            return False
        
        return True
    
    def _show_setup_error(self, title, message):
        """Show setup error message"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText("Monaco Editor setup required!")
        msg.setInformativeText(
            f"{message}\n\n"
            "To fix this:\n"
            "1. Download Monaco Editor from: https://github.com/microsoft/monaco-editor/releases\n"
            "2. Extract to 'monaco-editor' folder\n"
            "3. Ensure structure: monaco-editor/min/vs/loader.js"
        )
        msg.exec()
    
    def _setup_ui(self):
        """Set up the widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Web view for Monaco Editor
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
    
    def _create_monaco_html(self):
        """Create and load the Monaco Editor HTML"""
        html_file = self._create_html_file()
        
        # Set up web channel
        self.web_channel = QWebChannel()
        self.web_channel.registerObject("monaco_interface", self.monaco_interface)
        self.web_view.page().setWebChannel(self.web_channel)
        
        # Load the HTML file
        self.web_view.load(QUrl.fromLocalFile(str(html_file.resolve())))
    
    def _create_html_file(self):
        """Create the HTML file for Monaco Editor"""
        html_file = Path(__file__).parent / "monaco_editor_widget.html"
        monaco_abs_path = self.monaco_path.resolve().as_posix()
        
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Monaco Editor Widget</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        #container {{
            width: 100vw;
            height: 100vh;
        }}
        .loading {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: #666;
            gap: 20px;
        }}
        .spinner {{
            width: 30px;
            height: 30px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #007acc;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div id="container">
        <div class="loading">
            <div class="spinner"></div>
            <div>Loading Monaco Editor...</div>
        </div>
    </div>
    
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
        let editor;
        let monacoInterface;
        
        // Initialize Qt Web Channel
        new QWebChannel(qt.webChannelTransport, function(channel) {{
            monacoInterface = channel.objects.monaco_interface;
        }});
        
        // Load Monaco Editor
        async function initMonaco() {{
            try {{
                // Load Monaco loader
                await loadScript('file:///{monaco_abs_path}/min/vs/loader.js');
                
                // Configure require paths
                require.config({{ 
                    paths: {{ 
                        'vs': 'file:///{monaco_abs_path}/min/vs' 
                    }}
                }});
                
                // Load Monaco editor
                require(['vs/editor/editor.main'], function() {{
                    // Clear loading message
                    document.getElementById('container').innerHTML = '';
                    
                    // Create editor
                    editor = monaco.editor.create(document.getElementById('container'), {{
                        value: '',
                        language: 'javascript',
                        theme: 'vs-dark',
                        automaticLayout: true,
                        fontSize: 14,
                        minimap: {{ enabled: true }},
                        scrollBeyondLastLine: false,
                        wordWrap: 'on',
                        lineNumbers: 'on',
                        folding: true,
                        formatOnPaste: true,
                        formatOnType: true,
                        renderWhitespace: 'selection',
                        mouseWheelZoom: true
                    }});
                    
                    // Listen for content changes
                    editor.onDidChangeModelContent(function() {{
                        if (monacoInterface) {{
                            const content = editor.getValue();
                            monacoInterface.update_content(content);
                        }}
                    }});
                    
                    // Notify that editor is ready
                    if (monacoInterface) {{
                        monacoInterface.editor_initialized();
                    }}
                    
                    // Focus the editor
                    editor.focus();
                }});
                
            }} catch (error) {{
                showError('Failed to load Monaco Editor', error.message);
            }}
        }}
        
        function loadScript(src) {{
            return new Promise((resolve, reject) => {{
                const script = document.createElement('script');
                script.src = src;
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            }});
        }}
        
        function showError(title, message) {{
            document.getElementById('container').innerHTML = `
                <div class="loading">
                    <div style="color: #d32f2f;">${{title}}</div>
                    <div style="font-size: 12px; margin-top: 10px;">${{message}}</div>
                </div>`;
        }}
        
        // API functions called from Python
        function setEditorContent(content) {{
            if (editor) {{
                editor.setValue(content);
            }}
        }}
        
        function getEditorContent() {{
            return editor ? editor.getValue() : '';
        }}
        
        function setEditorLanguage(language) {{
            if (editor) {{
                const model = editor.getModel();
                monaco.editor.setModelLanguage(model, language);
            }}
        }}
        
        function setEditorTheme(theme) {{
            if (editor) {{
                monaco.editor.setTheme(theme);
            }}
        }}
        
        function setEditorOptions(options) {{
            if (editor) {{
                editor.updateOptions(options);
            }}
        }}
        
        function formatDocument() {{
            if (editor) {{
                editor.getAction('editor.action.formatDocument').run();
            }}
        }}
        
        function focusEditor() {{
            if (editor) {{
                editor.focus();
            }}
        }}
        
        function insertText(text) {{
            if (editor) {{
                const position = editor.getPosition();
                const range = new monaco.Range(
                    position.lineNumber, 
                    position.column, 
                    position.lineNumber, 
                    position.column
                );
                editor.executeEdits('insert-text', [{{
                    range: range,
                    text: text
                }}]);
            }}
        }}
        
        // Start initialization
        initMonaco();
    </script>
</body>
</html>'''
        
        # Write HTML file
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file
    
    # Public API methods
    
    def set_content(self, content):
        """
        Set the content of the editor.
        
        Args:
            content (str): The text content to set
        """
        if content is None:
            content = ""
        
        # Escape content for JavaScript
        escaped_content = content.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
        self.web_view.page().runJavaScript(f"setEditorContent(`{escaped_content}`);")
    
    def get_content(self):
        """
        Get the current content of the editor.
        
        Returns:
            str: The current editor content
        """
        return self.monaco_interface.current_content
    
    def set_language(self, language):
        """
        Set the programming language for syntax highlighting.
        
        Args:
            language (str): Language identifier (e.g., 'python', 'javascript', 'html')
        """
        self.web_view.page().runJavaScript(f"setEditorLanguage('{language}');")
    
    def set_theme(self, theme):
        """
        Set the editor theme.
        
        Args:
            theme (str): Theme name ('vs', 'vs-dark', 'hc-black')
        """
        self.web_view.page().runJavaScript(f"setEditorTheme('{theme}');")
    
    def format_document(self):
        """Format the entire document using Monaco's formatter."""
        self.web_view.page().runJavaScript("formatDocument();")
    
    def focus(self):
        """Focus the editor."""
        self.web_view.page().runJavaScript("focusEditor();")
    
    def insert_text(self, text):
        """
        Insert text at the current cursor position.
        
        Args:
            text (str): Text to insert
        """
        escaped_text = text.replace('\\', '\\\\').replace("'", "\\'")
        self.web_view.page().runJavaScript(f"insertText('{escaped_text}');")
    
    def set_editor_options(self, **options):
        """
        Set editor options.
        
        Args:
            **options: Monaco editor options (fontSize, wordWrap, etc.)
        """
        import json
        options_json = json.dumps(options)
        self.web_view.page().runJavaScript(f"setEditorOptions({options_json});")
    
    def is_ready(self):
        """
        Check if the editor is ready to receive commands.
        
        Returns:
            bool: True if editor is ready
        """
        return self.monaco_interface.is_ready
    
    def detect_language_from_filename(self, filename):
        """
        Detect and set language based on file extension.
        
        Args:
            filename (str): Filename to detect language from
        """
        ext = Path(filename).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.json': 'json',
            '.xml': 'xml',
            '.md': 'markdown',
            '.sql': 'sql',
            '.cpp': 'cpp',
            '.c': 'cpp',
            '.h': 'cpp',
            '.java': 'java',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.txt': 'plaintext'
        }
        
        language = language_map.get(ext, 'plaintext')
        self.set_language(language)
        return language
    
    def cleanup(self):
        """Clean up temporary files (call when widget is destroyed)"""
        html_file = Path(__file__).parent / "monaco_editor_widget.html"
        if html_file.exists():
            try:
                html_file.unlink()
            except:
                pass  # Ignore cleanup errors
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self.cleanup()
        super().closeEvent(event)