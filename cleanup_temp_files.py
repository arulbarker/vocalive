#!/usr/bin/env python3
"""
Script untuk membersihkan file temporary dan memperbaiki masalah
"""

import os
import glob
from pathlib import Path

def cleanup_temp_files():
    """Bersihkan file temporary"""
    print("🧹 Cleaning up temporary files...")
    
    # File yang akan dihapus
    temp_files = [
        "add_600k_credits.py",
        "add_basic_pro_credits_fields.py", 
        "add_database_fields.py",
        "test_credit_balance_fix.py",
        "get_supabase_keys.py",
        "test_purchase_with_sufficient_balance.py"
    ]
    
    for file in temp_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ Deleted: {file}")
            except Exception as e:
                print(f"❌ Failed to delete {file}: {e}")
    
    # Hapus file .pyc
    pyc_files = glob.glob("**/*.pyc", recursive=True)
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            print(f"✅ Deleted: {pyc_file}")
        except Exception as e:
            print(f"❌ Failed to delete {pyc_file}: {e}")
    
    # Hapus __pycache__ directories
    cache_dirs = glob.glob("**/__pycache__", recursive=True)
    for cache_dir in cache_dirs:
        try:
            import shutil
            shutil.rmtree(cache_dir)
            print(f"✅ Deleted: {cache_dir}")
        except Exception as e:
            print(f"❌ Failed to delete {cache_dir}: {e}")

def create_vscode_settings():
    """Buat file settings untuk VS Code"""
    print("\n⚙️ Creating VS Code settings...")
    
    settings = {
        "python.analysis.extraPaths": [
            ".",
            "./modules_client",
            "./modules_server"
        ],
        "python.analysis.autoImportCompletions": True,
        "python.analysis.typeCheckingMode": "basic",
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
        ]
    }
    
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    settings_file = vscode_dir / "settings.json"
    with open(settings_file, 'w') as f:
        import json
        json.dump(settings, f, indent=2)
    
    print(f"✅ Created: {settings_file}")

def create_requirements_dev():
    """Buat requirements-dev.txt untuk development dependencies"""
    print("\n📦 Creating development requirements...")
    
    dev_requirements = [
        "requests>=2.31.0",
        "PyQt6>=6.5.0",
        "pytchat>=0.9.0",
        "openai>=1.0.0",
        "google-cloud-texttospeech>=2.14.0",
        "google-cloud-speech>=2.21.0",
        "python-dotenv>=1.0.0",
        "psutil>=5.9.0",
        "pyinstaller>=5.13.0"
    ]
    
    with open("requirements-dev.txt", 'w') as f:
        for req in dev_requirements:
            f.write(f"{req}\n")
    
    print("✅ Created: requirements-dev.txt")

def main():
    """Main function"""
    print("🔧 CLEANUP AND FIX SCRIPT")
    print("=" * 50)
    
    # Cleanup temp files
    cleanup_temp_files()
    
    # Create VS Code settings
    create_vscode_settings()
    
    # Create dev requirements
    create_requirements_dev()
    
    print("\n" + "=" * 50)
    print("✅ Cleanup completed!")
    print("📝 VS Code settings created")
    print("📦 Development requirements created")
    print("🚀 All problems should be fixed!")

if __name__ == "__main__":
    main() 