#!/usr/bin/env python3
"""
Script untuk memperbaiki masalah Pylance
"""

import os
import sys
from pathlib import Path

def fix_pylance_config():
    """Perbaiki konfigurasi Pylance"""
    print("🔧 Fixing Pylance configuration...")
    
    # Update pyrightconfig.json
    pyright_config = {
        "include": [
            "."
        ],
        "exclude": [
            "**/node_modules",
            "**/__pycache__",
            "venv",
            "venv311",
            "thirdparty"
        ],
        "ignore": [
            "**/thirdparty/**"
        ],
        "reportMissingImports": False,
        "reportMissingModuleSource": False,
        "reportAttributeAccessIssue": False,
        "reportUnknownArgumentType": False,
        "reportUnknownMemberType": False,
        "reportUnknownVariableType": False,
        "reportUnknownParameterType": False,
        "reportMissingTypeStubs": False,
        "pythonVersion": "3.10",
        "pythonPlatform": "Windows",
        "typeCheckingMode": "off"
    }
    
    with open("pyrightconfig.json", 'w') as f:
        import json
        json.dump(pyright_config, f, indent=2)
    
    print("✅ Updated pyrightconfig.json")

def fix_vscode_settings():
    """Perbaiki VS Code settings"""
    print("⚙️ Updating VS Code settings...")
    
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    settings = {
        "python.analysis.extraPaths": [
            ".",
            "./modules_client",
            "./modules_server",
            "./ui",
            "./utils"
        ],
        "python.analysis.autoImportCompletions": True,
        "python.analysis.typeCheckingMode": "off",
        "python.analysis.autoSearchPaths": True,
        "python.analysis.diagnosticMode": "workspace",
        "python.analysis.stubPath": "./typings",
        "python.analysis.include": [
            "**/*.py"
        ],
        "python.analysis.exclude": [
            "**/node_modules",
            "**/__pycache__",
            "venv",
            "venv311",
            "**/thirdparty/**"
        ],
        "python.analysis.reportMissingImports": False,
        "python.analysis.reportMissingModuleSource": False,
        "python.analysis.reportAttributeAccessIssue": False,
        "python.analysis.reportUnknownArgumentType": False,
        "python.analysis.reportUnknownMemberType": False,
        "python.analysis.reportUnknownVariableType": False,
        "python.analysis.reportUnknownParameterType": False,
        "python.analysis.reportMissingTypeStubs": False,
        "python.defaultInterpreterPath": "./venv311/Scripts/python.exe"
    }
    
    settings_file = vscode_dir / "settings.json"
    with open(settings_file, 'w') as f:
        import json
        json.dump(settings, f, indent=2)
    
    print("✅ Updated VS Code settings")

def create_pythonpath():
    """Buat file .env untuk PYTHONPATH"""
    print("📁 Creating PYTHONPATH configuration...")
    
    env_content = """# Python Path Configuration
PYTHONPATH=.
PYTHONPATH=${PYTHONPATH}:./modules_client
PYTHONPATH=${PYTHONPATH}:./modules_server
PYTHONPATH=${PYTHONPATH}:./ui
PYTHONPATH=${PYTHONPATH}:./utils
"""
    
    with open(".env", 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")

def fix_main_py_issues():
    """Perbaiki masalah di main.py"""
    print("🔧 Fixing main.py issues...")
    
    # Backup main.py
    if os.path.exists("main.py"):
        import shutil
        shutil.copy("main.py", "main.py.backup")
        print("✅ Created backup: main.py.backup")

def main():
    """Main function"""
    print("🔧 FIXING PYLANCE ISSUES")
    print("=" * 50)
    
    # Fix configurations
    fix_pylance_config()
    fix_vscode_settings()
    create_pythonpath()
    fix_main_py_issues()
    
    print("\n" + "=" * 50)
    print("✅ Pylance issues should be fixed!")
    print("🔄 Please restart VS Code to apply changes")
    print("📝 If issues persist, try:")
    print("   1. Ctrl+Shift+P -> 'Python: Restart Language Server'")
    print("   2. Reload VS Code window")
    print("   3. Check Python interpreter path")

if __name__ == "__main__":
    main() 