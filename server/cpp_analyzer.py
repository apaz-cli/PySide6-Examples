"""
C/C++ Code Analyzer
Provides AST parsing and assembly disassembly for C/C++ files.
"""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import List
from analyzer_base import AnalyzerBase, AnalysisResult


class CppAnalyzer(AnalyzerBase):
    """Analyzes C/C++ code using clang and objdump"""
    
    def __init__(self):
        self.clang_available = self._check_clang()
        self.objdump_available = self._check_objdump()
    
    def _check_clang(self) -> bool:
        """Check if clang is available"""
        try:
            subprocess.run(['clang', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_objdump(self) -> bool:
        """Check if objdump is available"""
        try:
            subprocess.run(['objdump', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    @property
    def name(self) -> str:
        return "C/C++ Analyzer"
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.c', '.cpp', '.cxx', '.cc', '.h', '.hpp', '.hxx']
    
    @property
    def analysis_types(self) -> List[str]:
        return ['ast', 'assembly', 'analysis']
    
    def analyze_file(self, file_path: str) -> AnalysisResult:
        """Analyze a C/C++ file and return results"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            return self.analyze_code(source_code, file_path)
            
        except Exception as e:
            return AnalysisResult(
                analyzer_type="cpp",
                file_path=file_path,
                success=False,
                data={},
                errors=[f"Error reading file: {str(e)}"]
            )
    
    def analyze_code(self, source_code: str, filename: str = "<string>") -> AnalysisResult:
        """Analyze C/C++ source code"""
        errors = []
        data = {}
        
        # Check tool availability
        if not self.clang_available:
            errors.append("clang not available - install clang for full analysis")
        if not self.objdump_available:
            errors.append("objdump not available - install binutils for assembly analysis")
        
        if not self.clang_available and not self.objdump_available:
            return AnalysisResult(
                analyzer_type="cpp",
                file_path=filename,
                success=False,
                data={},
                errors=errors
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix=self._get_suffix(filename), delete=False) as temp_file:
            temp_file.write(source_code)
            temp_path = temp_file.name
        
        try:
            # Generate AST if clang is available
            if self.clang_available:
                ast_result = self._generate_ast(temp_path)
                data['ast'] = ast_result
            else:
                data['ast'] = "AST generation requires clang"
            
            # Compile and generate assembly if tools are available
            if self.clang_available and self.objdump_available:
                assembly_result = self._generate_assembly(temp_path)
                data['assembly'] = assembly_result
                data['analysis_summary'] = self._generate_analysis_summary(assembly_result)
            else:
                data['assembly'] = "Assembly generation requires clang and objdump"
                data['analysis_summary'] = "Analysis requires clang and objdump"
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        
        return AnalysisResult(
            analyzer_type="cpp",
            file_path=filename,
            success=len(errors) == 0,
            data=data,
            errors=errors
        )
    
    def _get_suffix(self, filename: str) -> str:
        """Get appropriate file suffix"""
        path = Path(filename)
        suffix = path.suffix.lower()
        if suffix in ['.cpp', '.cxx', '.cc']:
            return '.cpp'
        elif suffix in ['.h', '.hpp', '.hxx']:
            return '.hpp'
        else:
            return '.c'
    
    def _generate_ast(self, file_path: str) -> str:
        """Generate AST using clang"""
        try:
            result = subprocess.run([
                'clang', '-Xclang', '-ast-dump', '-fsyntax-only', file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"AST generation failed:\n{result.stderr}"
        
        except subprocess.TimeoutExpired:
            return "AST generation timed out"
        except Exception as e:
            return f"AST generation error: {str(e)}"
    
    def _generate_assembly(self, file_path: str) -> str:
        """Generate assembly using clang and objdump"""
        try:
            # Compile to object file
            with tempfile.NamedTemporaryFile(suffix='.o', delete=False) as obj_file:
                obj_path = obj_file.name
            
            try:
                # Compile with debug info
                compile_result = subprocess.run([
                    'clang', '-c', '-g', '-O0', file_path, '-o', obj_path
                ], capture_output=True, text=True, timeout=30)
                
                if compile_result.returncode != 0:
                    return f"Compilation failed:\n{compile_result.stderr}"
                
                # Disassemble with objdump
                objdump_result = subprocess.run([
                    'objdump', '-d', '-S', '--no-show-raw-insn', obj_path
                ], capture_output=True, text=True, timeout=30)
                
                if objdump_result.returncode == 0:
                    return self._format_objdump_output(objdump_result.stdout)
                else:
                    return f"Disassembly failed:\n{objdump_result.stderr}"
            
            finally:
                # Clean up object file
                try:
                    os.unlink(obj_path)
                except OSError:
                    pass
        
        except subprocess.TimeoutExpired:
            return "Assembly generation timed out"
        except Exception as e:
            return f"Assembly generation error: {str(e)}"
    
    def _format_objdump_output(self, output: str) -> str:
        """Format objdump output for better readability"""
        lines = output.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Add section headers
            if line.endswith(':') and not line.startswith(' '):
                formatted_lines.append(f"\n🔧 {line}")
                formatted_lines.append("=" * (len(line) + 3))
            
            # Format function headers
            elif '<' in line and '>:' in line:
                formatted_lines.append(f"\n📍 {line}")
                formatted_lines.append("-" * len(line))
            
            # Format assembly instructions
            elif ':' in line and any(x in line for x in ['mov', 'add', 'sub', 'call', 'ret', 'jmp', 'cmp']):
                # Split address and instruction
                parts = line.split(':', 1)
                if len(parts) == 2:
                    addr = parts[0].strip()
                    instr = parts[1].strip()
                    formatted_lines.append(f"  {addr:>8}: {instr}")
                else:
                    formatted_lines.append(f"  {line}")
            
            # Regular lines
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _generate_analysis_summary(self, assembly: str) -> str:
        """Generate analysis summary from assembly"""
        lines = assembly.split('\n')
        
        # Count instruction types
        instruction_counts = {}
        function_count = 0
        total_instructions = 0
        
        for line in lines:
            if '<' in line and '>:' in line:
                function_count += 1
            elif ':' in line and any(x in line for x in ['mov', 'add', 'sub', 'call', 'ret', 'jmp', 'cmp']):
                total_instructions += 1
                # Extract instruction mnemonic
                parts = line.split(':', 1)
                if len(parts) == 2:
                    instr_part = parts[1].strip()
                    if instr_part:
                        mnemonic = instr_part.split()[0]
                        instruction_counts[mnemonic] = instruction_counts.get(mnemonic, 0) + 1
        
        # Generate summary
        summary = f"📊 C/C++ Assembly Analysis Summary\n"
        summary += f"{'=' * 40}\n\n"
        summary += f"Functions found: {function_count}\n"
        summary += f"Total instructions: {total_instructions}\n\n"
        
        if instruction_counts:
            summary += "Instruction frequency:\n"
            for instr, count in sorted(instruction_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_instructions) * 100 if total_instructions > 0 else 0
                summary += f"  {instr:<8}: {count:>3} ({percentage:>5.1f}%)\n"
        
        return summary
