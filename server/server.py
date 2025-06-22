"""
Analysis Server
Web server that provides code analysis services via REST API.
"""

import json
import os
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from python_analyzer import PythonAnalyzer
from cpp_analyzer import CppAnalyzer


app = Flask(__name__)
CORS(app)

# Initialize analyzers
analyzers = {
    'python': PythonAnalyzer(),
    'cpp': CppAnalyzer()
}


@app.route('/api/analyzers', methods=['GET'])
def get_analyzers():
    """Get list of available analyzers"""
    return jsonify({
        analyzer_name: analyzer.get_info()
        for analyzer_name, analyzer in analyzers.items()
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_code():
    """Analyze code or file"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    analyzer_type = data.get('analyzer_type')
    if not analyzer_type or analyzer_type not in analyzers:
        return jsonify({'error': f'Unknown analyzer type: {analyzer_type}'}), 400
    
    analyzer = analyzers[analyzer_type]
    
    # Analyze from source code
    if 'source_code' in data:
        filename = data.get('filename', '<string>')
        result = analyzer.analyze_code(data['source_code'], filename)
    
    # Analyze from file path
    elif 'file_path' in data:
        file_path = data['file_path']
        if not os.path.exists(file_path):
            return jsonify({'error': f'File not found: {file_path}'}), 404
        result = analyzer.analyze_file(file_path)
    
    else:
        return jsonify({'error': 'Either source_code or file_path must be provided'}), 400
    
    return jsonify({
        'analyzer_type': result.analyzer_type,
        'file_path': result.file_path,
        'success': result.success,
        'data': result.data,
        'errors': result.errors
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'analyzers': list(analyzers.keys())})


if __name__ == '__main__':
    print("Starting Analysis Server...")
    print(f"Available analyzers: {list(analyzers.keys())}")
    app.run(host='127.0.0.1', port=5000, debug=True)
