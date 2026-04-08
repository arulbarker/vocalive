#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VocaLive - Setup Validator
Validates all required files and configurations before app starts
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Tuple, Dict

# Fix Windows console encoding for emoji
if sys.platform == "win32":
    import codecs
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass

class SetupValidator:
    """Validates application setup and configuration"""

    def __init__(self, root_dir: str = None):
        if root_dir:
            self.root_dir = Path(root_dir)
        else:
            if getattr(sys, 'frozen', False):
                self.root_dir = Path(sys.executable).parent
            else:
                self.root_dir = Path(__file__).resolve().parent.parent

        self.config_dir = self.root_dir / "config"
        self.errors = []
        self.warnings = []

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate all setup requirements
        Returns: (is_valid, errors, warnings)
        """
        print("[SETUP_VALIDATOR] Starting setup validation...")

        # 1. Check config directory
        self._check_config_dir()

        # 2. Check required JSON files
        self._check_required_files()

        # 3. Validate JSON syntax
        self._validate_json_files()

        # 4. Check API keys
        self._check_api_keys()

        # 5. Check permissions
        self._check_permissions()

        # 6. Check dependencies
        self._check_dependencies()

        is_valid = len(self.errors) == 0

        if is_valid:
            print("[SETUP_VALIDATOR] ✅ All checks passed!")
        else:
            print(f"[SETUP_VALIDATOR] ❌ {len(self.errors)} error(s) found")

        if self.warnings:
            print(f"[SETUP_VALIDATOR] ⚠️ {len(self.warnings)} warning(s)")

        return is_valid, self.errors, self.warnings

    def _check_config_dir(self):
        """Check if config directory exists"""
        if not self.config_dir.exists():
            self.errors.append(
                "Config directory not found! "
                f"Expected: {self.config_dir}"
            )
            # Try to create it
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
                self.warnings.append(
                    f"Created missing config directory: {self.config_dir}"
                )
            except Exception as e:
                self.errors.append(
                    f"Failed to create config directory: {e}"
                )

    def _check_required_files(self):
        """Check if all required files exist"""
        required_files = {
            "settings.json": "Application settings and API keys",
        }

        for filename, description in required_files.items():
            file_path = self.config_dir / filename
            if not file_path.exists():
                self.errors.append(
                    f"❌ MISSING: {filename}\n"
                    f"   Purpose: {description}\n"
                    f"   Expected path: {file_path}\n"
                    f"   📖 See PANDUAN_INSTALL_USER.md for setup instructions"
                )

    def _validate_json_files(self):
        """Validate JSON syntax of config files"""
        json_files = [
            "settings.json",
        ]

        for filename in json_files:
            file_path = self.config_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    # Check file size
                    size = file_path.stat().st_size
                    if size < 10:
                        self.errors.append(
                            f"❌ {filename} is too small ({size} bytes). "
                            "File might be empty or corrupted."
                        )
                except json.JSONDecodeError as e:
                    self.errors.append(
                        f"❌ {filename} has INVALID JSON syntax!\n"
                        f"   Error: {e}\n"
                        f"   Fix: Validate JSON at https://jsonlint.com/"
                    )
                except Exception as e:
                    self.errors.append(
                        f"❌ Cannot read {filename}: {e}"
                    )

    def _check_api_keys(self):
        """Check if API keys are configured"""
        settings_file = self.config_dir / "settings.json"

        if not settings_file.exists():
            return  # Already reported in _check_required_files

        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # Check DeepSeek API Key
            deepseek_key = None
            if "DEEPSEEK_API_KEY" in settings:
                deepseek_key = settings["DEEPSEEK_API_KEY"]
            elif "api_keys" in settings and "DEEPSEEK_API_KEY" in settings["api_keys"]:
                deepseek_key = settings["api_keys"]["DEEPSEEK_API_KEY"]

            if not deepseek_key or deepseek_key == "":
                self.warnings.append(
                    "⚠️ DeepSeek API key not configured.\n"
                    "   AI auto-reply will NOT work.\n"
                    "   Get API key from: https://platform.deepseek.com/"
                )
            elif not deepseek_key.startswith("sk-"):
                self.warnings.append(
                    "⚠️ DeepSeek API key format looks invalid.\n"
                    "   Valid format: sk-xxxxxxxxxxxxx"
                )

        except Exception as e:
            # Already handled in _validate_json_files
            pass

    def _check_permissions(self):
        """Check if app has proper file permissions"""
        test_file = self.config_dir / ".permission_test"

        try:
            # Try to write
            with open(test_file, 'w') as f:
                f.write("test")

            # Try to read
            with open(test_file, 'r') as f:
                f.read()

            # Try to delete
            test_file.unlink()

        except PermissionError:
            self.errors.append(
                "❌ PERMISSION DENIED: Cannot write to config directory!\n"
                "   Solution 1: Run as Administrator (Right-click → Run as admin)\n"
                "   Solution 2: Move app to a folder without restrictions\n"
                f"   Solution 3: Unblock folder: Right-click '{self.root_dir}' → Properties → Unblock"
            )
        except Exception as e:
            self.warnings.append(
                f"⚠️ File permission test failed: {e}"
            )

    def _check_dependencies(self):
        """Check if required Python packages are available"""
        required_packages = [
            ("cryptography", "License encryption"),
            ("requests", "HTTP requests"),
            ("pygame", "Audio playback")
        ]

        missing = []
        for package_name, description in required_packages:
            try:
                __import__(package_name)
            except ImportError:
                missing.append(f"{package_name} ({description})")

        if missing:
            self.errors.append(
                "❌ Missing Python dependencies:\n" +
                "\n".join(f"   - {pkg}" for pkg in missing) +
                "\n   This should NOT happen in EXE build!"
            )

    def generate_report(self) -> str:
        """Generate detailed validation report"""
        report = []
        report.append("="*60)
        report.append("VOCALIVE - SETUP VALIDATION REPORT")
        report.append("="*60)

        if self.errors:
            report.append("\n❌ CRITICAL ERRORS:")
            for i, error in enumerate(self.errors, 1):
                report.append(f"\n{i}. {error}")

        if self.warnings:
            report.append("\n⚠️ WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                report.append(f"\n{i}. {warning}")

        if not self.errors and not self.warnings:
            report.append("\n✅ ALL CHECKS PASSED!")
            report.append("Application is ready to run.")

        report.append("\n" + "="*60)
        report.append("📖 For setup help, see: PANDUAN_INSTALL_USER.md")
        report.append("="*60)

        return "\n".join(report)

    def show_gui_error(self, message: str):
        """Show error dialog using tkinter"""
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()  # Hide main window

            messagebox.showerror(
                "VocaLive - Setup Error",
                message + "\n\n📖 Lihat PANDUAN_INSTALL_USER.md untuk solusi lengkap"
            )

            root.destroy()
        except:
            # Fallback to console
            print("\n" + "="*60)
            print("SETUP ERROR")
            print("="*60)
            print(message)
            print("\n📖 Lihat PANDUAN_INSTALL_USER.md untuk solusi lengkap")
            print("="*60)

# Global instance
_validator = None

def get_validator(root_dir: str = None) -> SetupValidator:
    """Get or create global validator instance"""
    global _validator
    if _validator is None:
        _validator = SetupValidator(root_dir)
    return _validator

def validate_setup(root_dir: str = None, show_gui: bool = True) -> bool:
    """
    Validate application setup
    Returns True if valid, False if critical errors found
    """
    validator = get_validator(root_dir)
    is_valid, errors, warnings = validator.validate_all()

    # Print report
    report = validator.generate_report()
    print(report)

    # Show GUI error if not valid and GUI enabled
    if not is_valid and show_gui:
        error_msg = "Aplikasi tidak dapat dijalankan karena ada file konfigurasi yang hilang atau tidak valid:\n\n"
        error_msg += "\n".join(f"• {err[:100]}" for err in errors[:3])  # Show first 3 errors
        if len(errors) > 3:
            error_msg += f"\n... dan {len(errors)-3} error lainnya"

        validator.show_gui_error(error_msg)

    return is_valid

if __name__ == "__main__":
    # Test the validator
    import sys
    is_valid = validate_setup(show_gui=False)
    sys.exit(0 if is_valid else 1)
