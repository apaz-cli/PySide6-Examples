"""
Python Code Analysis Sandbox
Provides AST parsing and bytecode disassembly for Python files.
"""

import ast
import dis
import io
import sys
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QTextEdit, 
                               QLabel, QScrollArea)
from theme_manager import theme_manager
from bytecode_parser import BytecodeParser


class PythonAnalyzer(QObject):
    """Analyzes Python code using AST and disassembly"""
    
    analysis_ready = Signal(str, str, str, str)  # ast_dump, disassembly, bytecode_summary, errors
    
    def __init__(self):
        super().__init__()
        self.bytecode_parser = BytecodeParser()
    
    def analyze_file(self, file_path):
        """Analyze a Python file and emit results"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            ast_result, dis_result, bytecode_summary, errors = self.analyze_code(source_code, file_path)
            self.analysis_ready.emit(ast_result, dis_result, bytecode_summary, errors)
            
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            self.analysis_ready.emit("", "", "", error_msg)
    
    def analyze_code(self, source_code, filename="<string>"):
        """Analyze Python source code"""
        ast_result = ""
        dis_result = ""
        bytecode_summary = ""
        errors = ""
        
        try:
            # Parse AST
            tree = ast.parse(source_code, filename=filename)
            ast_result = self.format_ast_dump(tree)
            
            # Compile and disassemble
            try:
                compiled_code = compile(tree, filename, 'exec')
                
                # Capture disassembly output
                old_stdout = sys.stdout
                sys.stdout = dis_output = io.StringIO()
                
                dis.dis(compiled_code)
                
                sys.stdout = old_stdout
                dis_result = dis_output.getvalue()
                
                # Parse bytecode for analysis
                try:
                    bytecode_analysis = self.bytecode_parser.parse_disassembly(dis_result)
                    bytecode_summary = self.bytecode_parser.format_analysis_summary(bytecode_analysis)
                except Exception as e:
                    bytecode_summary = f"Bytecode analysis error: {str(e)}"
                
            except Exception as e:
                dis_result = f"Compilation error: {str(e)}"
                bytecode_summary = "Cannot analyze bytecode due to compilation error"
                
        except SyntaxError as e:
            errors = f"Syntax Error: {e.msg} (line {e.lineno})"
            ast_result = "Cannot parse due to syntax error"
            dis_result = "Cannot disassemble due to syntax error"
            bytecode_summary = "Cannot analyze bytecode due to syntax error"
            
        except Exception as e:
            errors = f"Analysis error: {str(e)}"
            
        return ast_result, dis_result, bytecode_summary, errors
    
    def format_ast_dump(self, tree):
        """Format AST dump with better readability"""
        dump = ast.dump(tree, indent=2)
        
        # Add some formatting for better readability
        lines = dump.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Count leading spaces for indentation level
            indent_level = len(line) - len(line.lstrip())
            
            # Add visual indicators for different AST node types
            if 'FunctionDef(' in line:
                line = line.replace('FunctionDef(', '🔧 FunctionDef(')
            elif 'ClassDef(' in line:
                line = line.replace('ClassDef(', '🏗️  ClassDef(')
            elif 'Import(' in line or 'ImportFrom(' in line:
                line = line.replace('Import(', '📦 Import(').replace('ImportFrom(', '📦 ImportFrom(')
            elif 'If(' in line:
                line = line.replace('If(', '🔀 If(')
            elif 'For(' in line or 'While(' in line:
                line = line.replace('For(', '🔄 For(').replace('While(', '🔄 While(')
            
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)


class SandboxWidget(QWidget):
    """Sandbox panel for Python code analysis"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.analyzer = PythonAnalyzer()
        self.setup_ui()
        self.connect_signals()
        self.apply_theme()
    
    def setup_ui(self):
        """Setup the sandbox UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status label
        self.status_label = QLabel("No Python file selected")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Tab widget for different analysis views
        self.tab_widget = QTabWidget()
        
        # AST tab
        self.ast_text = QTextEdit()
        self.ast_text.setReadOnly(True)
        self.ast_text.setPlainText("Select a Python file to see its AST representation")
        self.tab_widget.addTab(self.ast_text, "🌳 AST")
        
        # Disassembly tab
        self.dis_text = QTextEdit()
        self.dis_text.setReadOnly(True)
        self.dis_text.setPlainText("Select a Python file to see its bytecode disassembly")
        self.tab_widget.addTab(self.dis_text, "⚙️ Bytecode")
        
        # Analysis tab
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setPlainText("Select a Python file to see bytecode analysis")
        self.tab_widget.addTab(self.analysis_text, "📊 Analysis")
        
        # Errors tab
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setPlainText("No errors")
        self.tab_widget.addTab(self.error_text, "⚠️ Errors")
        
        layout.addWidget(self.tab_widget)
    
    def connect_signals(self):
        """Connect signals"""
        self.analyzer.analysis_ready.connect(self.display_analysis)
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def analyze_file(self, file_path):
        """Analyze a file if it's a Python file"""
        if not file_path:
            self.clear_analysis()
            return
        
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.py':
            self.current_file = file_path
            self.status_label.setText(f"Analyzing: {file_path.name}")
            self.analyzer.analyze_file(str(file_path))
        else:
            self.clear_analysis()
            self.status_label.setText(f"Not a Python file: {file_path.name}")
    
    def display_analysis(self, ast_result, dis_result, bytecode_summary, errors):
        """Display analysis results in tabs"""
        # Update AST tab
        if ast_result:
            self.ast_text.setPlainText(ast_result)
        else:
            self.ast_text.setPlainText("No AST data available")
        
        # Update disassembly tab
        if dis_result:
            self.dis_text.setPlainText(dis_result)
        else:
            self.dis_text.setPlainText("No disassembly data available")
        
        # Update analysis tab
        if bytecode_summary:
            self.analysis_text.setPlainText(bytecode_summary)
        else:
            self.analysis_text.setPlainText("No bytecode analysis available")
        
        # Update errors tab
        if errors:
            self.error_text.setPlainText(errors)
            # Switch to errors tab if there are errors
            self.tab_widget.setCurrentIndex(3)
        else:
            self.error_text.setPlainText("No errors detected")
        
        # Update status
        if self.current_file:
            self.status_label.setText(f"Analysis complete: {self.current_file.name}")
    
    def clear_analysis(self):
        """Clear all analysis results"""
        self.current_file = None
        self.ast_text.setPlainText("Select a Python file to see its AST representation")
        self.dis_text.setPlainText("Select a Python file to see its bytecode disassembly")
        self.analysis_text.setPlainText("Select a Python file to see bytecode analysis")
        self.error_text.setPlainText("No errors")
        self.status_label.setText("No Python file selected")
    
    def apply_theme(self):
        """Apply current theme to the widget"""
        # Apply text edit styles
        text_style = f"""
            QTextEdit {{
                background-color: {theme_manager.get_colors()['input_bg']};
                border: 1px solid {theme_manager.get_colors()['border']};
                border-radius: 5px;
                padding: 5px;
                font-family: '{theme_manager.current_font_family}', monospace;
                font-size: {max(7.5, theme_manager.current_font_size * 0.8)}pt;
                color: {theme_manager.get_colors()['text']};
            }}
        """
        
        for text_widget in [self.ast_text, self.dis_text, self.analysis_text, self.error_text]:
            text_widget.setStyleSheet(text_style)
        
        # Apply tab widget style
        tab_style = f"""
            QTabWidget::pane {{
                border: 1px solid {theme_manager.get_colors()['border']};
                border-radius: 5px;
                background-color: {theme_manager.get_colors()['background']};
            }}
            QTabBar::tab {{
                background-color: {theme_manager.get_colors()['button_bg']};
                color: white;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-family: '{theme_manager.current_font_family}';
                font-size: {max(7.5, theme_manager.current_font_size * 0.7)}pt;
            }}
            QTabBar::tab:selected {{
                background-color: {theme_manager.get_colors()['primary']};
            }}
            QTabBar::tab:hover {{
                background-color: {theme_manager.get_colors()['button_hover']};
            }}
        """
        
        self.tab_widget.setStyleSheet(tab_style)
        
        # Apply status label style
        self.status_label.setStyleSheet(theme_manager.get_widget_style('label', font_size=7.5, padding=5))
