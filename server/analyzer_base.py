"""
Base Analyzer Class
Defines the interface for all code analyzers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """Standard analysis result format"""
    analyzer_type: str
    file_path: str
    success: bool
    data: Dict[str, Any]
    errors: List[str]


class AnalyzerBase(ABC):
    """Base class for all code analyzers"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the analyzer"""
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of file extensions this analyzer supports"""
        pass
    
    @property
    @abstractmethod
    def analysis_types(self) -> List[str]:
        """List of analysis types this analyzer provides"""
        pass
    
    @abstractmethod
    def analyze_file(self, file_path: str) -> AnalysisResult:
        """Analyze a file and return results"""
        pass
    
    @abstractmethod
    def analyze_code(self, source_code: str, filename: str = "<string>") -> AnalysisResult:
        """Analyze source code directly"""
        pass
    
    def can_analyze(self, file_path: str) -> bool:
        """Check if this analyzer can handle the given file"""
        from pathlib import Path
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_extensions
    
    def get_info(self) -> Dict[str, Any]:
        """Get analyzer information for client"""
        return {
            "name": self.name,
            "supported_extensions": self.supported_extensions,
            "analysis_types": self.analysis_types
        }
