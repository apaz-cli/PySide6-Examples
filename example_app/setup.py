#!/usr/bin/env python3
"""
Setup script to download Monaco Editor for offline use
Run this script once to set up Monaco Editor locally
"""

import os
import requests
import tarfile
import shutil
from pathlib import Path

def download_monaco_editor():
    """Download and extract Monaco Editor for offline use"""
    
    # Create monaco-editor directory
    monaco_dir = Path("monaco-editor")
    monaco_dir.mkdir(exist_ok=True)
    
    print("Downloading Monaco Editor...")
    
    # Download from npm registry
    url = "https://registry.npmjs.org/monaco-editor/-/monaco-editor-0.45.0.tgz"
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Save tarball
        tarball_path = monaco_dir / "monaco-editor.tgz"
        with open(tarball_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("Extracting Monaco Editor...")
        
        # Extract tarball
        with tarfile.open(tarball_path, 'r:gz') as tar:
            tar.extractall(monaco_dir)
        
        # Move files from package subdirectory to root
        package_dir = monaco_dir / "package"
        if package_dir.exists():
            for item in package_dir.iterdir():
                if item.is_dir():
                    shutil.move(str(item), str(monaco_dir / item.name))
                else:
                    shutil.move(str(item), str(monaco_dir / item.name))
            
            # Remove empty package directory
            package_dir.rmdir()
        
        # Clean up tarball
        tarball_path.unlink()
        
        print("✅ Monaco Editor setup complete!")
        print(f"📁 Files extracted to: {monaco_dir.absolute()}")
        
        # Verify installation
        loader_path = monaco_dir / "min" / "vs" / "loader.js"
        if loader_path.exists():
            print("✅ Installation verified - loader.js found")
        else:
            print("❌ Installation verification failed - loader.js not found")
            
    except Exception as e:
        print(f"❌ Error downloading Monaco Editor: {e}")
        print("\nManual installation instructions:")
        print("1. Go to https://github.com/microsoft/monaco-editor/releases")
        print("2. Download the latest release")
        print("3. Extract the contents to a 'monaco-editor' folder")

if __name__ == "__main__":
    download_monaco_editor()