"""
Bytecode Parser and Representation
Parses Python bytecode disassembly into structured data for analysis and visualization.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from enum import Enum


class InstructionType(Enum):
    """Categories of bytecode instructions"""
    LOAD = "load"
    STORE = "store"
    CALL = "call"
    JUMP = "jump"
    COMPARE = "compare"
    BINARY_OP = "binary_op"
    BUILD = "build"
    RETURN = "return"
    LOOP = "loop"
    OTHER = "other"


@dataclass
class BytecodeInstruction:
    """Represents a single bytecode instruction"""
    offset: int
    opname: str
    arg: Optional[int]
    argval: Optional[str]
    argrepr: str
    line_number: Optional[int]
    is_jump_target: bool
    instruction_type: InstructionType
    
    def __str__(self):
        target_marker = ">>" if self.is_jump_target else "  "
        line_info = f"({self.line_number:3d})" if self.line_number else "     "
        
        if self.arg is not None:
            return f"{target_marker} {self.offset:4d} {self.opname:<20} {self.arg:4d} {self.argrepr}"
        else:
            return f"{target_marker} {self.offset:4d} {self.opname:<20}"


@dataclass
class BytecodeAnalysis:
    """Analysis results for bytecode"""
    instructions: List[BytecodeInstruction]
    jump_targets: Set[int]
    local_vars: Set[str]
    global_vars: Set[str]
    constants: Set[str]
    function_calls: List[str]
    
    @property
    def loads(self) -> List[BytecodeInstruction]:
        """Get all load instructions"""
        return [instr for instr in self.instructions if instr.instruction_type == InstructionType.LOAD]
    
    @property
    def stores(self) -> List[BytecodeInstruction]:
        """Get all store instructions"""
        return [instr for instr in self.instructions if instr.instruction_type == InstructionType.STORE]
    
    @property
    def calls(self) -> List[BytecodeInstruction]:
        """Get all call instructions"""
        return [instr for instr in self.instructions if instr.instruction_type == InstructionType.CALL]
    
    @property
    def jumps(self) -> List[BytecodeInstruction]:
        """Get all jump instructions"""
        return [instr for instr in self.instructions if instr.instruction_type == InstructionType.JUMP]


class BytecodeParser:
    """Parses dis.dis() output into structured data"""
    
    # Core instruction patterns (stable across Python versions)
    LOAD_INSTRUCTIONS = {
        'LOAD_CONST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 
        'LOAD_DEREF', 'LOAD_CLOSURE'
    }
    
    STORE_INSTRUCTIONS = {
        'STORE_NAME', 'STORE_GLOBAL', 'STORE_FAST', 'STORE_DEREF',
        'STORE_SUBSCR', 'STORE_ATTR'
    }
    
    CALL_INSTRUCTIONS = {
        'CALL_FUNCTION', 'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX',
        'CALL_METHOD', 'CALL'  # CALL is newer Python versions
    }
    
    JUMP_INSTRUCTIONS = {
        'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'POP_JUMP_IF_TRUE', 
        'POP_JUMP_IF_FALSE', 'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'
    }
    
    COMPARE_INSTRUCTIONS = {
        'COMPARE_OP', 'IS_OP', 'CONTAINS_OP'
    }
    
    BINARY_INSTRUCTIONS = {
        'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_MULTIPLY', 'BINARY_DIVIDE',
        'BINARY_MODULO', 'BINARY_POWER', 'BINARY_AND', 'BINARY_OR', 'BINARY_XOR'
    }
    
    BUILD_INSTRUCTIONS = {
        'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_SET', 'BUILD_MAP',
        'BUILD_SLICE', 'UNPACK_SEQUENCE'
    }
    
    RETURN_INSTRUCTIONS = {
        'RETURN_VALUE', 'YIELD_VALUE'
    }
    
    LOOP_INSTRUCTIONS = {
        'GET_ITER', 'FOR_ITER'
    }
    
    def __init__(self):
        self.instruction_map = self._build_instruction_map()
    
    def _build_instruction_map(self) -> Dict[str, InstructionType]:
        """Build mapping from instruction name to type"""
        mapping = {}
        
        for instr in self.LOAD_INSTRUCTIONS:
            mapping[instr] = InstructionType.LOAD
        for instr in self.STORE_INSTRUCTIONS:
            mapping[instr] = InstructionType.STORE
        for instr in self.CALL_INSTRUCTIONS:
            mapping[instr] = InstructionType.CALL
        for instr in self.JUMP_INSTRUCTIONS:
            mapping[instr] = InstructionType.JUMP
        for instr in self.COMPARE_INSTRUCTIONS:
            mapping[instr] = InstructionType.COMPARE
        for instr in self.BINARY_INSTRUCTIONS:
            mapping[instr] = InstructionType.BINARY_OP
        for instr in self.BUILD_INSTRUCTIONS:
            mapping[instr] = InstructionType.BUILD
        for instr in self.RETURN_INSTRUCTIONS:
            mapping[instr] = InstructionType.RETURN
        for instr in self.LOOP_INSTRUCTIONS:
            mapping[instr] = InstructionType.LOOP
            
        return mapping
    
    def parse_disassembly(self, dis_output: str) -> BytecodeAnalysis:
        """Parse dis.dis() output into structured bytecode representation"""
        lines = dis_output.strip().split('\n')
        instructions = []
        jump_targets = set()
        local_vars = set()
        global_vars = set()
        constants = set()
        function_calls = []
        
        # First pass: identify jump targets
        for line in lines:
            if '>>' in line:
                match = re.search(r'>>\s*(\d+)', line)
                if match:
                    jump_targets.add(int(match.group(1)))
        
        # Second pass: parse instructions
        for line in lines:
            instruction = self._parse_instruction_line(line, jump_targets)
            if instruction:
                instructions.append(instruction)
                
                # Extract variable and constant information
                self._extract_metadata(instruction, local_vars, global_vars, constants, function_calls)
        
        return BytecodeAnalysis(
            instructions=instructions,
            jump_targets=jump_targets,
            local_vars=local_vars,
            global_vars=global_vars,
            constants=constants,
            function_calls=function_calls
        )
    
    def _parse_instruction_line(self, line: str, jump_targets: Set[int]) -> Optional[BytecodeInstruction]:
        """Parse a single line of disassembly output"""
        line = line.strip()
        if not line or line.startswith('Disassembly'):
            return None
        
        # Handle jump target marker
        is_jump_target = line.startswith('>>')
        if is_jump_target:
            line = line[2:].strip()
        
        # Parse instruction components
        # Format: offset opname [arg] [argval] [(argrepr)]
        parts = line.split()
        if len(parts) < 2:
            return None
        
        try:
            offset = int(parts[0])
            opname = parts[1]
        except (ValueError, IndexError):
            return None
        
        # Extract line number if present (in parentheses at start)
        line_number = None
        line_match = re.search(r'\((\d+)\)', line)
        if line_match:
            line_number = int(line_match.group(1))
        
        # Extract argument and argument representation
        arg = None
        argval = None
        argrepr = ""
        
        if len(parts) > 2:
            try:
                arg = int(parts[2])
            except ValueError:
                pass
        
        # Extract argument representation (everything after the opname and arg)
        if len(parts) > 3:
            argrepr = ' '.join(parts[3:])
            # Clean up parentheses and extract argval
            if '(' in argrepr and ')' in argrepr:
                argval_match = re.search(r'\(([^)]+)\)', argrepr)
                if argval_match:
                    argval = argval_match.group(1)
        
        # Determine instruction type
        instruction_type = self.instruction_map.get(opname, InstructionType.OTHER)
        
        return BytecodeInstruction(
            offset=offset,
            opname=opname,
            arg=arg,
            argval=argval,
            argrepr=argrepr,
            line_number=line_number,
            is_jump_target=is_jump_target,
            instruction_type=instruction_type
        )
    
    def _extract_metadata(self, instruction: BytecodeInstruction, 
                         local_vars: Set[str], global_vars: Set[str], 
                         constants: Set[str], function_calls: List[str]):
        """Extract variable names, constants, and function calls from instruction"""
        
        if instruction.opname in ['LOAD_FAST', 'STORE_FAST'] and instruction.argval:
            local_vars.add(instruction.argval)
        
        elif instruction.opname in ['LOAD_GLOBAL', 'STORE_GLOBAL'] and instruction.argval:
            global_vars.add(instruction.argval)
        
        elif instruction.opname == 'LOAD_CONST' and instruction.argval:
            constants.add(instruction.argval)
        
        elif instruction.instruction_type == InstructionType.CALL and instruction.argval:
            function_calls.append(instruction.argval)
    
    def format_analysis_summary(self, analysis: BytecodeAnalysis) -> str:
        """Format a summary of the bytecode analysis"""
        summary = []
        summary.append(f"📊 Bytecode Analysis Summary")
        summary.append(f"{'='*40}")
        summary.append(f"Total Instructions: {len(analysis.instructions)}")
        summary.append(f"Jump Targets: {len(analysis.jump_targets)}")
        summary.append("")
        
        summary.append(f"🔄 Instruction Breakdown:")
        type_counts = {}
        for instr in analysis.instructions:
            type_counts[instr.instruction_type] = type_counts.get(instr.instruction_type, 0) + 1
        
        for instr_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            summary.append(f"  {instr_type.value.title()}: {count}")
        
        summary.append("")
        summary.append(f"📦 Variables & Constants:")
        summary.append(f"  Local Variables: {', '.join(sorted(analysis.local_vars)) if analysis.local_vars else 'None'}")
        summary.append(f"  Global Variables: {', '.join(sorted(analysis.global_vars)) if analysis.global_vars else 'None'}")
        summary.append(f"  Constants: {len(analysis.constants)} items")
        
        if analysis.function_calls:
            summary.append("")
            summary.append(f"📞 Function Calls:")
            for call in analysis.function_calls[:10]:  # Show first 10
                summary.append(f"  {call}")
            if len(analysis.function_calls) > 10:
                summary.append(f"  ... and {len(analysis.function_calls) - 10} more")
        
        return '\n'.join(summary)
