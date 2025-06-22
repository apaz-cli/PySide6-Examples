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
        
        # Disassembly tab - custom rich bytecode display
        self.dis_text = QTextEdit()
        self.dis_text.setReadOnly(True)
        self.dis_text.setPlainText("Select a Python file to see its bytecode disassembly")
        self.dis_text.setOpenExternalLinks(False)
        self.dis_text.anchorClicked.connect(self.handle_bytecode_link)
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
        
        # Update disassembly tab with custom rich formatting
        if dis_result:
            try:
                # Parse and format the bytecode with our custom display
                self.bytecode_analysis = self.analyzer.bytecode_parser.parse_disassembly(dis_result)
                formatted_html = self.create_rich_bytecode_display(self.bytecode_analysis)
                self.dis_text.setHtml(formatted_html)
            except Exception as e:
                # Fallback to plain text if formatting fails
                self.dis_text.setPlainText(f"Error parsing bytecode: {str(e)}\n\nRaw output:\n{dis_result}")
        else:
            self.dis_text.setPlainText("No disassembly data available")
            self.bytecode_analysis = None
        
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
        self.bytecode_analysis = None
        self.ast_text.setPlainText("Select a Python file to see its AST representation")
        self.dis_text.setPlainText("Select a Python file to see its bytecode disassembly")
        self.analysis_text.setPlainText("Select a Python file to see bytecode analysis")
        self.error_text.setPlainText("No errors")
        self.status_label.setText("No Python file selected")
    
    def create_rich_bytecode_display(self, bytecode_analysis):
        """Create rich HTML display of bytecode with navigation links"""
        colors = theme_manager.get_colors()
        font_family = theme_manager.current_font_family
        font_size = max(7.5, theme_manager.current_font_size * 0.8)
        
        # Color scheme for different instruction types
        type_colors = {
            'LOAD': colors['primary'],
            'STORE': colors['accent'], 
            'CALL': colors['secondary'],
            'JUMP': '#f39c12',
            'COMPARE': '#9b59b6',
            'BINARY_OP': '#e67e22',
            'BUILD': '#1abc9c',
            'RETURN': '#e74c3c',
            'LOOP': '#f1c40f',
            'OTHER': colors['text_secondary']
        }
        
        # Build navigation links section
        nav_links = self._build_navigation_links(bytecode_analysis, type_colors)
        
        # Build instruction display
        instruction_lines = []
        
        for i, instruction in enumerate(bytecode_analysis.instructions):
            # Create anchor for this instruction
            anchor = f'<a name="instr_{i}"></a>'
            
            # Jump target marker
            target_marker = "&gt;&gt;" if instruction.is_jump_target else "&nbsp;&nbsp;"
            if instruction.is_jump_target:
                anchor += f'<a name="offset_{instruction.offset}"></a>'
            
            # Line number
            line_info = f"({instruction.line_number:3d})" if instruction.line_number else "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            
            # Instruction color
            instr_color = type_colors.get(instruction.instruction_type.name, type_colors['OTHER'])
            
            # Format instruction parts
            offset_part = f'<span style="color: {colors["text_secondary"]};">{instruction.offset:4d}</span>'
            opname_part = f'<span style="color: {instr_color}; font-weight: bold;">{instruction.opname}</span>'
            
            # Argument and representation
            arg_part = ""
            if instruction.arg is not None:
                arg_part = f'<span style="color: {colors["text"]};">{instruction.arg:4d}</span>'
            
            argrepr_part = ""
            if instruction.argrepr:
                argrepr_text = instruction.argrepr
                
                # Make variable names clickable
                if instruction.instruction_type.name in ['LOAD', 'STORE'] and instruction.argval:
                    var_name = instruction.argval
                    argrepr_text = argrepr_text.replace(
                        var_name,
                        f'<a href="#var_{var_name}" style="color: {instr_color}; text-decoration: underline;" title="Find all uses of {var_name}">{var_name}</a>'
                    )
                
                # Make jump targets clickable
                elif instruction.instruction_type.name == 'JUMP':
                    import re
                    target_match = re.search(r'(\d+)', instruction.argrepr)
                    if target_match:
                        target_offset = target_match.group(1)
                        if int(target_offset) in bytecode_analysis.jump_targets:
                            argrepr_text = argrepr_text.replace(
                                target_offset,
                                f'<a href="#offset_{target_offset}" style="color: {instr_color}; text-decoration: underline;" title="Jump to offset {target_offset}">{target_offset}</a>'
                            )
                
                # Make function calls clickable
                elif instruction.instruction_type.name == 'CALL' and instruction.argval:
                    func_name = instruction.argval
                    argrepr_text = argrepr_text.replace(
                        func_name,
                        f'<a href="#call_{func_name}" style="color: {instr_color}; text-decoration: underline;" title="Find all calls to {func_name}">{func_name}</a>'
                    )
                
                argrepr_part = f'<span style="color: {colors["text"]};">({argrepr_text})</span>'
            
            # Combine parts
            line_content = f"{target_marker} {line_info} {offset_part} {opname_part:<20}"
            if arg_part:
                line_content += f" {arg_part}"
            if argrepr_part:
                line_content += f" {argrepr_part}"
            
            # Add hover tooltip with instruction details
            tooltip = self._create_instruction_tooltip(instruction)
            
            # Highlight jump targets
            line_style = ""
            if instruction.is_jump_target:
                line_style = f'background-color: {colors["hover"]}; padding: 2px; border-radius: 3px;'
            
            formatted_line = f'<div style="{line_style}" title="{tooltip}">{anchor}{line_content}</div>'
            instruction_lines.append(formatted_line)
        
        # Combine navigation and instructions
        html = f'''
        <div style="font-family: '{font_family}', monospace; font-size: {font_size}pt; 
                    line-height: 1.4; color: {colors['text']}; background: transparent;">
            {nav_links}
            <hr style="border: 1px solid {colors['border']}; margin: 15px 0;">
            <div style="white-space: pre-wrap;">
                {''.join(instruction_lines)}
            </div>
        </div>
        '''
        
        return html
    
    def _build_navigation_links(self, analysis, type_colors):
        """Build navigation links section"""
        colors = theme_manager.get_colors()
        links = []
        
        # Quick stats
        stats = f'''
        <div style="margin-bottom: 10px; padding: 8px; background-color: {colors['background'].replace('120', '60')}; border-radius: 5px;">
            <strong>📊 Quick Stats:</strong> 
            {len(analysis.instructions)} instructions, 
            {len(analysis.jump_targets)} jump targets, 
            {len(analysis.local_vars)} locals, 
            {len(analysis.global_vars)} globals
        </div>
        '''
        links.append(stats)
        
        # Jump targets
        if analysis.jump_targets:
            jump_links = []
            for target in sorted(analysis.jump_targets):
                jump_links.append(f'<a href="#offset_{target}" style="color: {type_colors["JUMP"]}; text-decoration: none; margin-right: 8px;" title="Jump to offset {target}">@{target}</a>')
            
            jumps_section = f'''
            <div style="margin-bottom: 8px;">
                <strong style="color: {type_colors['JUMP']};">🔀 Jump Targets:</strong> 
                {' '.join(jump_links)}
            </div>
            '''
            links.append(jumps_section)
        
        # Variables
        if analysis.local_vars or analysis.global_vars:
            var_links = []
            
            for var in sorted(analysis.local_vars):
                var_links.append(f'<a href="#var_{var}" style="color: {type_colors["LOAD"]}; text-decoration: none; margin-right: 8px;" title="Find uses of local variable {var}">🔵{var}</a>')
            
            for var in sorted(analysis.global_vars):
                var_links.append(f'<a href="#var_{var}" style="color: {type_colors["STORE"]}; text-decoration: none; margin-right: 8px;" title="Find uses of global variable {var}">🔴{var}</a>')
            
            if var_links:
                vars_section = f'''
                <div style="margin-bottom: 8px;">
                    <strong style="color: {colors['text']};">📦 Variables:</strong> 
                    {' '.join(var_links)}
                </div>
                '''
                links.append(vars_section)
        
        # Function calls
        unique_calls = list(set(analysis.function_calls))
        if unique_calls:
            call_links = []
            for call in sorted(unique_calls)[:10]:  # Limit to first 10
                call_links.append(f'<a href="#call_{call}" style="color: {type_colors["CALL"]}; text-decoration: none; margin-right: 8px;" title="Find calls to {call}">📞{call}</a>')
            
            calls_section = f'''
            <div style="margin-bottom: 8px;">
                <strong style="color: {type_colors['CALL']};">📞 Function Calls:</strong> 
                {' '.join(call_links)}
            </div>
            '''
            links.append(calls_section)
        
        return ''.join(links)
    
    def _create_instruction_tooltip(self, instruction):
        """Create tooltip text for an instruction"""
        tooltip_parts = [
            f"Offset: {instruction.offset}",
            f"Opcode: {instruction.opname}",
            f"Type: {instruction.instruction_type.value.title()}"
        ]
        
        if instruction.line_number:
            tooltip_parts.append(f"Source Line: {instruction.line_number}")
        
        if instruction.arg is not None:
            tooltip_parts.append(f"Argument: {instruction.arg}")
        
        if instruction.argval:
            tooltip_parts.append(f"Value: {instruction.argval}")
        
        if instruction.is_jump_target:
            tooltip_parts.append("🎯 Jump Target")
        
        return " | ".join(tooltip_parts)
    
    def handle_bytecode_link(self, url):
        """Handle clicking on bytecode navigation links"""
        url_str = url.toString()
        
        if url_str.startswith('#offset_'):
            # Jump to specific offset
            self._scroll_to_anchor(url_str)
        
        elif url_str.startswith('#var_'):
            # Highlight all uses of a variable
            var_name = url_str[5:]  # Remove '#var_'
            self._highlight_variable_uses(var_name)
        
        elif url_str.startswith('#call_'):
            # Highlight all calls to a function
            func_name = url_str[6:]  # Remove '#call_'
            self._highlight_function_calls(func_name)
        
        elif url_str.startswith('#instr_'):
            # Jump to specific instruction
            self._scroll_to_anchor(url_str)
    
    def _scroll_to_anchor(self, anchor):
        """Scroll to a specific anchor in the text"""
        cursor = self.dis_text.textCursor()
        cursor.movePosition(cursor.Start)
        
        if self.dis_text.find(anchor.replace('#', '')):
            self.dis_text.ensureCursorVisible()
    
    def _highlight_variable_uses(self, var_name):
        """Highlight all uses of a variable"""
        if not self.bytecode_analysis:
            return
        
        # Find all instructions that use this variable
        matching_instructions = []
        for i, instr in enumerate(self.bytecode_analysis.instructions):
            if (instr.argval == var_name and 
                instr.instruction_type.name in ['LOAD', 'STORE']):
                matching_instructions.append(i)
        
        # Scroll to first occurrence
        if matching_instructions:
            self._scroll_to_anchor(f'#instr_{matching_instructions[0]}')
    
    def _highlight_function_calls(self, func_name):
        """Highlight all calls to a function"""
        if not self.bytecode_analysis:
            return
        
        # Find all call instructions for this function
        matching_instructions = []
        for i, instr in enumerate(self.bytecode_analysis.instructions):
            if (instr.argval == func_name and 
                instr.instruction_type.name == 'CALL'):
                matching_instructions.append(i)
        
        # Scroll to first occurrence
        if matching_instructions:
            self._scroll_to_anchor(f'#instr_{matching_instructions[0]}')
    
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
