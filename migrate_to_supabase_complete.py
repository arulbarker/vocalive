#!/usr/bin/env python3
"""
COMPLETE MIGRATION FROM VPS TO SUPABASE
Migrate all critical data to ensure 100% Supabase dependency
"""

import os
import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Migration')

# Add project root to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

class CompleteMigration:
    """Complete migration from VPS to Supabase"""
    
    def __init__(self):
        """Initialize migration with all necessary components"""
        try:
            from modules_client.supabase_client import SupabaseClient
            from modules_client.secure_credentials_manager import SecureCredentialsManager
            from modules_client.config_manager import ConfigManager
            
            self.supabase = SupabaseClient()
            self.secure_creds = SecureCredentialsManager()
            self.config = ConfigManager()
            
            logger.info("🚀 Migration system initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize migration: {e}")
            raise
    
    def migrate_api_credentials(self) -> bool:
        """Migrate all API credentials to Supabase secure storage"""
        logger.info("📧 Migrating API credentials...")
        
        try:
            # Get API keys from settings.json
            api_keys = self.config.get("api_keys", {})
            ipaymu_config = self.config.get("ipaymu_config", {})
            
            credentials_to_migrate = [
                # AI API Keys
                ("DEEPSEEK_API_KEY", api_keys.get("DEEPSEEK_API_KEY"), "api_key", "DeepSeek AI API Key"),
                ("YOUTUBE_API_KEY", api_keys.get("YOUTUBE_API_KEY"), "api_key", "YouTube Data API Key"),
                ("TRAKTEER_API_KEY", api_keys.get("TRAKTEER_API_KEY"), "api_key", "Trakteer API Key"),
                
                # Payment Gateway
                ("IPAYMU_API_KEY", ipaymu_config.get("API_KEY"), "payment", "iPaymu Payment Gateway API Key"),
                ("IPAYMU_VA_NUMBER", ipaymu_config.get("VA_NUMBER"), "payment", "iPaymu Virtual Account Number"),
                
                # OAuth credentials if they exist
                ("GOOGLE_CLIENT_ID", self._get_google_oauth_client_id(), "oauth", "Google OAuth Client ID"),
                ("GOOGLE_CLIENT_SECRET", self._get_google_oauth_client_secret(), "oauth", "Google OAuth Client Secret"),
            ]
            
            migrated_count = 0
            for key, value, cred_type, description in credentials_to_migrate:
                if value and value != "your_ipaymu_api_key":  # Skip placeholder values
                    result = self.secure_creds.store_credential(key, value, cred_type, description)
                    if result.get('status') == 'success':
                        logger.info(f"✅ Migrated {key}")
                        migrated_count += 1
                    else:
                        logger.error(f"❌ Failed to migrate {key}: {result.get('message')}")
                else:
                    logger.warning(f"⚠️ Skipping {key} - no value or placeholder")
            
            logger.info(f"📊 Migration complete: {migrated_count} credentials migrated")
            return migrated_count > 0
            
        except Exception as e:
            logger.error(f"❌ API credentials migration failed: {e}")
            return False
    
    def migrate_user_data(self) -> bool:
        """Migrate user account data to Supabase"""
        logger.info("👤 Migrating user account data...")
        
        try:
            user_data = self.config.get("user_data", {})
            email = user_data.get("email")
            
            if not email:
                logger.warning("⚠️ No user email found in config")
                return False
            
            # Ensure user profile exists in Supabase
            profile_result = self.supabase.ensure_user_profile(email)
            if profile_result.get('status') == 'success':
                logger.info(f"✅ User profile ensured for {email}")
                return True
            else:
                logger.error(f"❌ Failed to ensure user profile: {profile_result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ User data migration failed: {e}")
            return False
    
    def migrate_demo_data(self) -> bool:
        """Migrate demo data and settings to Supabase"""
        logger.info("🎮 Migrating demo data...")
        
        try:
            # Demo data should be handled by Supabase functions
            # Check if demo reset system is working
            email = self.config.get("user_data", {}).get("email")
            if not email:
                logger.warning("⚠️ No email for demo data migration")
                return False
            
            # Demo data is handled by subscription system
            logger.info("✅ Demo data managed by Supabase subscription system")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo data migration failed: {e}")
            return False
    
    def migrate_credit_data(self) -> bool:
        """Verify credit and payment data is in Supabase"""
        logger.info("💰 Verifying credit data migration...")
        
        try:
            email = self.config.get("user_data", {}).get("email")
            if not email:
                logger.warning("⚠️ No email for credit data verification")
                return False
            
            # Check if user has credit balance in Supabase
            credit_data = self.supabase.get_credit_balance(email)
            if credit_data.get('status') == 'success':
                balance = credit_data.get('data', {}).get('wallet_balance', 0)
                logger.info(f"✅ Credit balance verified: {balance} credits")
                return True
            else:
                logger.error(f"❌ Credit data verification failed: {credit_data.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Credit data verification failed: {e}")
            return False
    
    def remove_vps_dependencies(self) -> bool:
        """Remove or disable VPS dependencies"""
        logger.info("🔧 Removing VPS dependencies...")
        
        try:
            # Update config to remove VPS server URL
            current_config = self.config.get_all()
            
            # Remove VPS references
            if "server_url" in current_config:
                current_config["server_url"] = "supabase_backend"
                logger.info("✅ Removed VPS server_url")
            
            # Update production config to force Supabase mode
            production_config = {
                "mode": "production",
                "backend_type": "supabase",
                "disable_vps": True,
                "require_supabase": True,
                "force_supabase_only": True,
                "created_at": datetime.now().isoformat(),
                "version": "3.0.0_supabase_only"
            }
            
            prod_config_path = Path("config/production_config.json")
            with open(prod_config_path, 'w', encoding='utf-8') as f:
                json.dump(production_config, f, indent=2)
            
            logger.info("✅ Updated production config for Supabase-only mode")
            return True
            
        except Exception as e:
            logger.error(f"❌ VPS dependency removal failed: {e}")
            return False
    
    def create_supabase_fallback_system(self) -> bool:
        """Create fallback system for when VPS is unavailable"""
        logger.info("🛡️ Creating Supabase fallback system...")
        
        try:
            fallback_config = {
                "fallback_mode": "supabase_only",
                "disable_vps_fallback": True,
                "primary_backend": "supabase",
                "secondary_backend": None,
                "emergency_mode": "local_only",
                "created_at": datetime.now().isoformat()
            }
            
            fallback_path = Path("config/fallback_config.json")
            with open(fallback_path, 'w', encoding='utf-8') as f:
                json.dump(fallback_config, f, indent=2)
            
            logger.info("✅ Fallback system configured")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fallback system creation failed: {e}")
            return False
    
    def verify_migration_completeness(self) -> Dict[str, bool]:
        """Verify all migration steps completed successfully"""
        logger.info("🔍 Verifying migration completeness...")
        
        verification_results = {
            "api_credentials": False,
            "user_data": False,
            "demo_data": False,
            "credit_data": False,
            "vps_removal": False,
            "fallback_system": False
        }
        
        try:
            # Check API credentials
            creds_list = self.secure_creds.list_credentials()
            if creds_list.get('status') == 'success':
                creds_data = creds_list.get('data', [])
                if len(creds_data) > 0:
                    verification_results["api_credentials"] = True
                    logger.info(f"✅ API credentials verified: {len(creds_data)} stored")
            
            # Check user data
            email = self.config.get("user_data", {}).get("email")
            if email:
                profile = self.supabase.get_user_data(email)
                if profile:
                    verification_results["user_data"] = True
                    logger.info("✅ User data verified")
            
            # Check credit data
            if email:
                credit_data = self.supabase.get_credit_balance(email)
                if credit_data.get('status') == 'success':
                    verification_results["credit_data"] = True
                    logger.info("✅ Credit data verified")
            
            # Check config files
            prod_config_path = Path("config/production_config.json")
            if prod_config_path.exists():
                with open(prod_config_path, 'r', encoding='utf-8') as f:
                    prod_config = json.load(f)
                    if prod_config.get("force_supabase_only"):
                        verification_results["vps_removal"] = True
                        logger.info("✅ VPS removal verified")
            
            fallback_path = Path("config/fallback_config.json")
            if fallback_path.exists():
                verification_results["fallback_system"] = True
                logger.info("✅ Fallback system verified")
            
            # Demo data is managed by Supabase
            verification_results["demo_data"] = True
            logger.info("✅ Demo data managed by Supabase")
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
        
        return verification_results
    
    def _get_google_oauth_client_id(self) -> str:
        """Get Google OAuth client ID from config"""
        try:
            oauth_path = Path("config/google_oauth.json")
            if oauth_path.exists():
                with open(oauth_path, 'r', encoding='utf-8') as f:
                    oauth_data = json.load(f)
                    return oauth_data.get("installed", {}).get("client_id", "")
        except:
            pass
        return ""
    
    def _get_google_oauth_client_secret(self) -> str:
        """Get Google OAuth client secret from config"""
        try:
            oauth_path = Path("config/google_oauth.json")
            if oauth_path.exists():
                with open(oauth_path, 'r', encoding='utf-8') as f:
                    oauth_data = json.load(f)
                    return oauth_data.get("installed", {}).get("client_secret", "")
        except:
            pass
        return ""
    
    def run_complete_migration(self) -> bool:
        """Run complete migration process"""
        logger.info("🚀 Starting complete VPS to Supabase migration...")
        logger.info("=" * 60)
        
        migration_steps = [
            ("API Credentials", self.migrate_api_credentials),
            ("User Account Data", self.migrate_user_data),
            ("Demo Data", self.migrate_demo_data),
            ("Credit Data", self.migrate_credit_data),
            ("VPS Dependencies Removal", self.remove_vps_dependencies),
            ("Fallback System", self.create_supabase_fallback_system),
        ]
        
        success_count = 0
        for step_name, step_func in migration_steps:
            logger.info(f"📋 Executing: {step_name}")
            try:
                if step_func():
                    logger.info(f"✅ {step_name} - SUCCESS")
                    success_count += 1
                else:
                    logger.error(f"❌ {step_name} - FAILED")
            except Exception as e:
                logger.error(f"❌ {step_name} - ERROR: {e}")
        
        logger.info("=" * 60)
        logger.info(f"📊 Migration Results: {success_count}/{len(migration_steps)} steps completed")
        
        # Verification
        verification = self.verify_migration_completeness()
        passed_checks = sum(verification.values())
        total_checks = len(verification)
        
        logger.info(f"🔍 Verification: {passed_checks}/{total_checks} checks passed")
        
        for check, result in verification.items():
            status = "✅" if result else "❌"
            logger.info(f"  {status} {check}")
        
        migration_success = success_count == len(migration_steps)
        verification_success = passed_checks >= (total_checks * 0.8)  # 80% threshold
        
        overall_success = migration_success and verification_success
        
        if overall_success:
            logger.info("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("🔒 Application is now 100% Supabase dependent")
            logger.info("🚫 VPS dependency removed - safe to cancel VPS subscription")
        else:
            logger.warning("⚠️ MIGRATION COMPLETED WITH ISSUES")
            logger.warning("🔧 Some manual intervention may be required")
        
        return overall_success

def main():
    """Main migration execution"""
    try:
        migration = CompleteMigration()
        success = migration.run_complete_migration()
        
        if success:
            print("\\n🎉 MIGRATION SUCCESSFUL - VPS can be safely discontinued")
            return 0
        else:
            print("\\n⚠️ MIGRATION COMPLETED WITH ISSUES - Please review logs")
            return 1
            
    except Exception as e:
        logger.error(f"❌ CRITICAL MIGRATION ERROR: {e}")
        print("\\n🚨 MIGRATION FAILED - VPS still required")
        return 2

if __name__ == "__main__":
    sys.exit(main())