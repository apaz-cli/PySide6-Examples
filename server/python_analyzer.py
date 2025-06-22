"""
Python Code Analyzer
Provides AST parsing and bytecode disassembly for Python files.
"""

import ast
import dis
import io
import sys
import inspect
from pathlib import Path
from typing import List
from analyzer_base import AnalyzerBase, AnalysisResult
from bytecode_parser import BytecodeParser


class PythonAnalyzer(AnalyzerBase):
    """Analyzes Python code using AST and disassembly"""
    
    def __init__(self):
        self.bytecode_parser = BytecodeParser()
    
    @property
    def name(self) -> str:
        return "Python Analyzer"
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.py']
    
    @property
    def analysis_types(self) -> List[str]:
        return ['ast', 'bytecode', 'disassembly', 'analysis']
    
    def analyze_file(self, file_path: str) -> AnalysisResult:
        """Analyze a Python file and return results"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            return self.analyze_code(source_code, file_path)
            
        except Exception as e:
            return AnalysisResult(
                analyzer_type="python",
                file_path=file_path,
                success=False,
                data={},
                errors=[f"Error reading file: {str(e)}"]
            )
    
    def analyze_code(self, source_code: str, filename: str = "<string>") -> AnalysisResult:
        """Analyze Python source code"""
        errors = []
        data = {}
        
        try:
            # Parse AST
            tree = ast.parse(source_code, filename=filename)
            data['ast'] = self.format_ast_dump(tree)
            
            # Extract function objects
            function_objects = self._extract_function_objects(source_code, filename)
            
            try:
                # Compile and disassemble
                compiled_code = compile(tree, filename, 'exec')
                
                old_stdout = sys.stdout
                sys.stdout = dis_output = io.StringIO()
                dis.dis(compiled_code)
                sys.stdout = old_stdout
                data['disassembly'] = dis_output.getvalue()
                
                try:
                    # Detailed bytecode analysis
                    bytecode_analysis = self.bytecode_parser.analyze_code_object(
                        compiled_code, source_code, function_objects
                    )
                    data['bytecode_analysis'] = self._serialize_bytecode_analysis(bytecode_analysis)
                    data['analysis_summary'] = self.bytecode_parser.format_analysis_summary(bytecode_analysis)
                except Exception as e:
                    # Fallback analysis
                    bytecode_analysis = self.bytecode_parser.parse_disassembly(data['disassembly'])
                    data['bytecode_analysis'] = self._serialize_bytecode_analysis(bytecode_analysis)
                    data['analysis_summary'] = f"Using fallback analysis: {str(e)}\n\n" + \
                                             self.bytecode_parser.format_analysis_summary(bytecode_analysis)
                
            except Exception as e:
                errors.append(f"Compilation error: {str(e)}")
                data['disassembly'] = ""
                data['analysis_summary'] = "Cannot analyze bytecode due to compilation error"
                
        except SyntaxError as e:
            errors.append(f"Syntax Error: {e.msg} (line {e.lineno})")
            data['ast'] = "Cannot parse due to syntax error"
            data['disassembly'] = "Cannot disassemble due to syntax error"
            data['analysis_summary'] = "Cannot analyze bytecode due to syntax error"
            
        except Exception as e:
            errors.append(f"Analysis error: {str(e)}")
        
        return AnalysisResult(
            analyzer_type="python",
            file_path=filename,
            success=len(errors) == 0,
            data=data,
            errors=errors
        )
    
    def _extract_function_objects(self, source_code: str, filename: str):
        """Extract function objects by executing the code"""
        try:
            namespace = {}
            exec(compile(source_code, filename, 'exec'), namespace)
            return {name: obj for name, obj in namespace.items() if inspect.isfunction(obj)}
        except Exception:
            return {}
    
    def format_ast_dump(self, tree):
        """Format AST dump with better readability"""
        dump = ast.dump(tree, indent=2)
        
        replacements = {
            'FunctionDef(': '🔧 FunctionDef(',
            'ClassDef(': '🏗️  ClassDef(',
            'Import(': '📦 Import(',
            'ImportFrom(': '📦 ImportFrom(',
            'If(': '🔀 If(',
            'For(': '🔄 For(',
            'While(': '🔄 While('
        }
        
        for old, new in replacements.items():
            dump = dump.replace(old, new)
        
        return dump
    
    def _serialize_bytecode_analysis(self, analysis):
        """Convert bytecode analysis to JSON-serializable format"""
        def serialize_value(value):
            """Convert non-serializable values to strings"""
            if hasattr(value, '__code__') or str(type(value)) == "<class 'code'>":
                return f"<code object {getattr(value, 'co_name', 'unknown')}>"
            elif callable(value):
                return f"<function {getattr(value, '__name__', 'unknown')}>"
            elif isinstance(value, (frozenset, set)):
                return list(value)
            elif isinstance(value, tuple):
                return [serialize_value(item) for item in value]
            elif hasattr(value, '__dict__'):
                return str(value)
            else:
                return value
        
        def serialize_collection(collection):
            """Convert collections to lists, handling nested structures"""
            if isinstance(collection, (frozenset, set)):
                return [serialize_value(item) for item in collection]
            elif hasattr(collection, '__iter__') and not isinstance(collection, (str, bytes)):
                return [serialize_value(item) for item in collection]
            else:
                return serialize_value(collection)
        
        return {
            'instructions': [
                {
                    'offset': instr.offset,
                    'opname': instr.opname,
                    'arg': instr.arg,
                    'argval': serialize_value(instr.argval),
                    'argrepr': instr.argrepr,
                    'line_number': instr.line_number,
                    'is_jump_target': instr.is_jump_target,
                    'instruction_type': instr.instruction_type.value if hasattr(instr.instruction_type, 'value') else str(instr.instruction_type)
                }
                for instr in analysis.instructions
            ],
            'jump_targets': serialize_collection(analysis.jump_targets),
            'local_vars': serialize_collection(analysis.local_vars),
            'global_vars': serialize_collection(analysis.global_vars),
            'constants': serialize_collection(analysis.constants),
            'function_calls': serialize_collection(analysis.function_calls),
            'functions': [
                {
                    'name': func.name,
                    'start_offset': func.start_offset,
                    'varnames': serialize_collection(func.varnames),
                    'names': serialize_collection(func.names),
                    'freevars': serialize_collection(func.freevars),
                    'cellvars': serialize_collection(func.cellvars),
                    'argcount': func.argcount,
                    'kwonlyargcount': func.kwonlyargcount
                }
                for func in analysis.functions
            ]
        }
