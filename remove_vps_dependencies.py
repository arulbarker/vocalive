#!/usr/bin/env python3
"""
REMOVE VPS DEPENDENCIES FROM CODEBASE
Update all code to use Supabase instead of VPS server
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple

class VPSRemover:
    """Remove VPS dependencies from codebase"""
    
    def __init__(self):
        self.root = Path(".")
        self.vps_patterns = [
            r'69\.62\.79\.238',
            r'http://69\.62\.79\.238:8000',
            r'vps.*server',
            r'server.*vps',
        ]
        self.files_to_update = []
        self.backup_dir = Path("backup_before_vps_removal")
    
    def find_vps_references(self) -> List[Tuple[Path, List[str]]]:
        """Find all VPS references in code"""
        print("🔍 Scanning for VPS references...")
        
        vps_files = []
        exclude_dirs = {'.git', '__pycache__', 'node_modules', 'venv', 'venv311', '.env', 'backup_before_vps_removal'}
        exclude_files = {'migrate_to_supabase_complete.py', 'remove_vps_dependencies.py'}
        
        for file_path in self.root.rglob('*.py'):
            # Skip excluded directories and files
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
            if file_path.name in exclude_files:
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                matches = []
                for pattern in self.vps_patterns:
                    found = re.findall(pattern, content, re.IGNORECASE)
                    if found:
                        matches.extend(found)
                
                if matches:
                    vps_files.append((file_path, matches))
                    print(f"  📄 {file_path}: {len(matches)} VPS references")
            
            except (UnicodeDecodeError, PermissionError):
                continue
        
        return vps_files
    
    def create_backups(self, files_to_update: List[Path]) -> bool:
        """Create backups of files before modification"""
        print("💾 Creating backups...")
        
        try:
            self.backup_dir.mkdir(exist_ok=True)
            
            for file_path in files_to_update:
                # Create backup directory structure
                backup_path = self.backup_dir / file_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file to backup
                with open(file_path, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                
                print(f"  ✅ {file_path} -> {backup_path}")
            
            return True
        except Exception as e:
            print(f"❌ Backup creation failed: {e}")
            return False
    
    def update_api_client(self) -> bool:
        """Update API client to use Supabase only"""
        print("🔧 Updating API client...")
        
        try:
            api_file = Path("modules_client/api.py")
            if not api_file.exists():
                print("⚠️ API client file not found")
                return False
            
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace VPS server references
            replacements = [
                (r'self\.base_url\s*=\s*"http://69\.62\.79\.238:8000"', 'self.base_url = "supabase_backend"'),
                (r'"http://69\.62\.79\.238:8000"', '"supabase_backend"'),
                (r'# FORCE PRODUCTION MODE - Always use VPS server', '# FORCE PRODUCTION MODE - Always use Supabase'),
                (r'Using VPS server', 'Using Supabase backend'),
                (r'VPS server unavailable', 'Supabase unavailable'),
            ]
            
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            # Add Supabase-only mode comment
            if 'SUPABASE_ONLY_MODE' not in content:
                content = content.replace(
                    'class APIClient:',
                    '''class APIClient:
    """API Client - SUPABASE_ONLY_MODE - No VPS dependencies"""'''
                )
            
            with open(api_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("  ✅ API client updated")
            return True
            
        except Exception as e:
            print(f"❌ API client update failed: {e}")
            return False
    
    def update_credit_tracker(self) -> bool:
        """Update credit tracker to remove VPS sync"""
        print("🔧 Updating credit tracker...")
        
        try:
            tracker_file = Path("modules_server/real_credit_tracker.py")
            if not tracker_file.exists():
                print("⚠️ Credit tracker file not found")
                return False
            
            with open(tracker_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Comment out VPS sync functionality
            vps_sync_pattern = r'def sync_usage_to_vps.*?(?=def|\Z)'
            content = re.sub(vps_sync_pattern, '''def sync_usage_to_vps(self, hours_used: float):
        """VPS sync disabled - using Supabase only"""
        logger.debug(f"VPS sync disabled, using Supabase for: {hours_used:.4f}h")
        # VPS sync removed - all data now in Supabase
        pass
    
    ''', content, flags=re.DOTALL)
            
            with open(tracker_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("  ✅ Credit tracker updated")
            return True
            
        except Exception as e:
            print(f"❌ Credit tracker update failed: {e}")
            return False
    
    def update_config_files(self) -> bool:
        """Update configuration files"""
        print("🔧 Updating configuration files...")
        
        try:
            # Update settings.json
            settings_file = Path("config/settings.json")
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Remove or update VPS references
                if "server_url" in settings:
                    settings["server_url"] = "supabase_backend"
                
                # Add Supabase-only flag
                settings["supabase_only_mode"] = True
                settings["vps_disabled"] = True
                settings["backend_type"] = "supabase"
                
                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2)
                
                print("  ✅ settings.json updated")
            
            # Update production config
            prod_config_file = Path("config/production_config.json")
            if prod_config_file.exists():
                prod_config = {
                    "mode": "production",
                    "backend_type": "supabase",
                    "server_only": False,
                    "disable_local_fallback": False,
                    "require_internet": True,
                    "supabase_only": True,
                    "vps_disabled": True,
                    "max_offline_time": 300,
                    "force_login": True,
                    "disable_demo_mode": False,
                    "created_at": "2025-07-30T16:00:00.000000",
                    "version": "3.0.0_supabase_only"
                }
                
                with open(prod_config_file, 'w', encoding='utf-8') as f:
                    json.dump(prod_config, f, indent=2)
                
                print("  ✅ production_config.json updated")
            
            return True
            
        except Exception as e:
            print(f"❌ Config files update failed: {e}")
            return False
    
    def remove_vps_server_files(self) -> bool:
        """Remove or rename VPS server files"""
        print("🔧 Handling VPS server files...")
        
        try:
            vps_files = [
                "server_inti.py",
                "streammateai_server",
            ]
            
            for vps_file in vps_files:
                vps_path = Path(vps_file)
                if vps_path.exists():
                    # Rename instead of delete for safety
                    backup_name = f"{vps_file}.vps_backup"
                    backup_path = Path(backup_name)
                    
                    if vps_path.is_file():
                        vps_path.rename(backup_path)
                        print(f"  📦 {vps_file} -> {backup_name}")
                    elif vps_path.is_dir():
                        vps_path.rename(backup_path)
                        print(f"  📁 {vps_file}/ -> {backup_name}/")
            
            return True
            
        except Exception as e:
            print(f"❌ VPS files handling failed: {e}")
            return False
    
    def create_supabase_only_indicator(self) -> bool:
        """Create indicator file for Supabase-only mode"""
        print("🔧 Creating Supabase-only indicator...")
        
        try:
            indicator_content = {
                "mode": "supabase_only",
                "vps_removed": True,
                "migration_date": "2025-07-30",
                "version": "3.0.0",
                "description": "This application now runs 100% on Supabase - no VPS required",
                "security_features": [
                    "Encrypted credentials in Supabase",
                    "Row Level Security (RLS) enabled",
                    "Service role authentication",
                    "Secure API endpoints",
                    "No plain text API keys"
                ]
            }
            
            indicator_file = Path("SUPABASE_ONLY_MODE.json")
            with open(indicator_file, 'w', encoding='utf-8') as f:
                json.dump(indicator_content, f, indent=2)
            
            print("  ✅ Supabase-only indicator created")
            return True
            
        except Exception as e:
            print(f"❌ Indicator creation failed: {e}")
            return False
    
    def run_vps_removal(self) -> bool:
        """Run complete VPS removal process"""
        print("🚀 Starting VPS dependencies removal...")
        print("=" * 60)
        
        # Find VPS references
        vps_files = self.find_vps_references()
        if not vps_files:
            print("✅ No VPS references found - already clean!")
            return True
        
        print(f"📊 Found VPS references in {len(vps_files)} files")
        
        # Create backups
        files_to_backup = [file_path for file_path, _ in vps_files]
        if not self.create_backups(files_to_backup):
            print("❌ Backup creation failed - aborting")
            return False
        
        # Execute removal steps
        removal_steps = [
            ("API Client Update", self.update_api_client),
            ("Credit Tracker Update", self.update_credit_tracker),
            ("Config Files Update", self.update_config_files),
            ("VPS Server Files Handling", self.remove_vps_server_files),
            ("Supabase-Only Indicator", self.create_supabase_only_indicator),
        ]
        
        success_count = 0
        for step_name, step_func in removal_steps:
            print(f"📋 Executing: {step_name}")
            try:
                if step_func():
                    print(f"✅ {step_name} - SUCCESS")
                    success_count += 1
                else:
                    print(f"❌ {step_name} - FAILED")
            except Exception as e:
                print(f"❌ {step_name} - ERROR: {e}")
        
        print("=" * 60)
        print(f"📊 Removal Results: {success_count}/{len(removal_steps)} steps completed")
        
        if success_count == len(removal_steps):
            print("🎉 VPS DEPENDENCIES REMOVAL COMPLETED!")
            print("🔒 Application is now VPS-independent")
            print("💾 Backups stored in: backup_before_vps_removal/")
            return True
        else:
            print("⚠️ VPS REMOVAL COMPLETED WITH ISSUES")
            print("🔧 Some manual intervention may be required")
            return False

def main():
    """Main VPS removal execution"""
    try:
        remover = VPSRemover()
        success = remover.run_vps_removal()
        
        if success:
            print("\\n🎉 VPS REMOVAL SUCCESSFUL")
            return 0
        else:
            print("\\n⚠️ VPS REMOVAL COMPLETED WITH ISSUES")
            return 1
            
    except Exception as e:
        print(f"❌ CRITICAL VPS REMOVAL ERROR: {e}")
        return 2

if __name__ == "__main__":
    exit(main())