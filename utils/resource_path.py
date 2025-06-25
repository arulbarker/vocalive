"""
Resource path utilities for PyInstaller EXE compatibility
"""

import sys
import os
from pathlib import Path

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for both development and PyInstaller EXE.
    
    Args:
        relative_path (str): Relative path to resource file
        
    Returns:
        Path: Absolute path to resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        print(f"[DEBUG] Running in EXE mode, base_path: {base_path}")
    except AttributeError:
        # Development mode - use current directory
        base_path = Path(__file__).parent.parent
        print(f"[DEBUG] Running in development mode, base_path: {base_path}")
    
    resource_path = Path(base_path) / relative_path
    print(f"[DEBUG] Resource path for '{relative_path}': {resource_path}")
    print(f"[DEBUG] Resource exists: {resource_path.exists()}")
    
    return resource_path

def get_config_path(config_file):
    """
    Get path to config file, with EXE compatibility.
    
    Args:
        config_file (str): Config filename (e.g., 'voices.json')
        
    Returns:
        Path: Absolute path to config file
    """
    return get_resource_path(f"config/{config_file}")

def list_bundled_files(directory="config"):
    """
    List files in bundled directory for debugging.
    
    Args:
        directory (str): Directory to list
        
    Returns:
        list: List of files found
    """
    try:
        dir_path = get_resource_path(directory)
        if dir_path.exists() and dir_path.is_dir():
            files = list(dir_path.iterdir())
            print(f"[DEBUG] Files in bundled {directory}: {[f.name for f in files]}")
            return files
        else:
            print(f"[DEBUG] Bundled directory {directory} not found or not a directory")
            return []
    except Exception as e:
        print(f"[DEBUG] Error listing bundled files: {e}")
        return [] 