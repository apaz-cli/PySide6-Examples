"""
API Client for Analysis Server
Handles communication with the analysis server.
"""

import json
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """Client-side analysis result"""
    analyzer_type: str
    file_path: str
    success: bool
    data: Dict[str, Any]
    errors: List[str]


class AnalysisClient:
    """Client for communicating with the analysis server"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:5000"):
        self.server_url = server_url.rstrip('/')
        self.available_analyzers = {}
        self._load_analyzers()
    
    def _load_analyzers(self):
        """Load available analyzers from server"""
        try:
            response = requests.get(f"{self.server_url}/api/analyzers", timeout=5)
            if response.status_code == 200:
                self.available_analyzers = response.json()
            else:
                print(f"Failed to load analyzers: {response.status_code}")
        except Exception as e:
            print(f"Error connecting to analysis server: {e}")
    
    def get_analyzers(self) -> Dict[str, Any]:
        """Get available analyzers"""
        return self.available_analyzers
    
    def analyze_file(self, file_path: str, analyzer_type: str) -> Optional[AnalysisResult]:
        """Analyze a file using specified analyzer"""
        try:
            payload = {
                'analyzer_type': analyzer_type,
                'file_path': file_path
            }
            
            response = requests.post(
                f"{self.server_url}/api/analyze",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return AnalysisResult(
                    analyzer_type=data['analyzer_type'],
                    file_path=data['file_path'],
                    success=data['success'],
                    data=data['data'],
                    errors=data['errors']
                )
            else:
                print(f"Analysis failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error during analysis: {e}")
            return None
    
    def analyze_code(self, source_code: str, analyzer_type: str, filename: str = "<string>") -> Optional[AnalysisResult]:
        """Analyze source code using specified analyzer"""
        try:
            payload = {
                'analyzer_type': analyzer_type,
                'source_code': source_code,
                'filename': filename
            }
            
            response = requests.post(
                f"{self.server_url}/api/analyze",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return AnalysisResult(
                    analyzer_type=data['analyzer_type'],
                    file_path=data['file_path'],
                    success=data['success'],
                    data=data['data'],
                    errors=data['errors']
                )
            else:
                print(f"Analysis failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error during analysis: {e}")
            return None
    
    def health_check(self) -> bool:
        """Check if server is healthy"""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def can_analyze(self, file_path: str) -> List[str]:
        """Get list of analyzers that can handle this file"""
        from pathlib import Path
        ext = Path(file_path).suffix.lower()
        
        compatible_analyzers = []
        for analyzer_name, analyzer_info in self.available_analyzers.items():
            if ext in analyzer_info.get('supported_extensions', []):
                compatible_analyzers.append(analyzer_name)
        
        return compatible_analyzers
