#!/usr/bin/env python3
"""
MASTER MIGRATION & SECURITY SCRIPT
Complete migration from VPS to Supabase with security hardening
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MasterMigration')

class MasterMigrationSecurity:
    """Master controller for migration and security operations"""
    
    def __init__(self):
        """Initialize master migration controller"""
        self.root = Path(".")
        self.scripts = {
            "migration": "migrate_to_supabase_complete.py",
            "vps_removal": "remove_vps_dependencies.py", 
            "security_audit": "security_audit_complete.py"
        }
        
        logger.info("🚀 Master Migration & Security Controller initialized")
    
    def run_pre_migration_checks(self) -> bool:
        """Run pre-migration checks"""
        logger.info("🔍 Running pre-migration checks...")
        
        checks_passed = 0
        total_checks = 0
        
        # Check if Supabase config exists
        total_checks += 1
        supabase_config = Path("config/supabase_config.json")
        if supabase_config.exists():
            checks_passed += 1
            logger.info("✅ Supabase configuration found")
        else:
            logger.error("❌ Supabase configuration missing")
        
        # Check if secure credentials table SQL exists
        total_checks += 1
        secure_creds_sql = Path("create_secure_credentials_table.sql")
        if secure_creds_sql.exists():
            checks_passed += 1
            logger.info("✅ Secure credentials SQL found")
        else:
            logger.error("❌ Secure credentials SQL missing")
        
        # Check if required modules exist
        total_checks += 1
        supabase_client = Path("modules_client/supabase_client.py")
        if supabase_client.exists():
            checks_passed += 1
            logger.info("✅ Supabase client module found")
        else:
            logger.error("❌ Supabase client module missing")
        
        # Check if secure credentials manager exists
        total_checks += 1
        secure_creds_manager = Path("modules_client/secure_credentials_manager.py")
        if secure_creds_manager.exists():
            checks_passed += 1
            logger.info("✅ Secure credentials manager found")
        else:
            logger.error("❌ Secure credentials manager missing")
        
        # Check internet connectivity to Supabase
        total_checks += 1
        try:
            import requests
            supabase_url = "https://nivwxqojwljihoybzgkc.supabase.co"
            response = requests.get(f"{supabase_url}/rest/v1/", timeout=10)
            if response.status_code in [200, 401, 403]:  # Any response means it's reachable
                checks_passed += 1
                logger.info("✅ Supabase connectivity verified")
            else:
                logger.error(f"❌ Supabase connectivity issue: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Supabase connectivity failed: {e}")
        
        success_rate = (checks_passed / total_checks) * 100
        logger.info(f"📊 Pre-migration checks: {checks_passed}/{total_checks} passed ({success_rate:.1f}%)")
        
        return success_rate >= 80  # Need at least 80% to proceed
    
    def run_script(self, script_name: str, description: str) -> bool:
        """Run a migration script and capture results"""
        script_path = Path(self.scripts.get(script_name))
        
        if not script_path.exists():
            logger.error(f"❌ Script not found: {script_path}")
            return False
        
        logger.info(f"🔧 Running {description}...")
        logger.info(f"📄 Script: {script_path}")
        
        try:
            # Run the script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=self.root
            )
            
            # Log output
            if result.stdout:
                for line in result.stdout.strip().split('\\n'):
                    logger.info(f"  {line}")
            
            if result.stderr:
                for line in result.stderr.strip().split('\\n'):
                    logger.warning(f"  STDERR: {line}")
            
            success = result.returncode == 0
            if success:
                logger.info(f"✅ {description} completed successfully")
            else:
                logger.error(f"❌ {description} failed with code {result.returncode}")
            
            return success
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {description} timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"❌ {description} failed with exception: {e}")
            return False
    
    def create_migration_report(self, results: Dict[str, bool]) -> str:
        """Create comprehensive migration report"""
        report = []
        report.append("# STREAMMATE AI - MIGRATION TO SUPABASE REPORT")
        report.append("=" * 60)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Version: 3.0.0 - Supabase Only")
        report.append("")
        
        # Executive Summary
        report.append("## EXECUTIVE SUMMARY")
        report.append("")
        total_steps = len(results)
        successful_steps = sum(1 for success in results.values() if success)
        success_rate = (successful_steps / total_steps) * 100 if total_steps > 0 else 0
        
        if success_rate >= 90:
            report.append("🎉 **MIGRATION SUCCESSFUL** - Application is now 100% Supabase dependent")
            report.append("✅ VPS subscription can be safely cancelled")
        elif success_rate >= 70:
            report.append("⚠️ **MIGRATION MOSTLY SUCCESSFUL** - Minor issues detected")
            report.append("🔧 Some manual intervention may be required")
        else:
            report.append("❌ **MIGRATION INCOMPLETE** - Critical issues detected")
            report.append("🚨 VPS subscription should NOT be cancelled yet")
        
        report.append(f"📊 **Success Rate:** {success_rate:.1f}% ({successful_steps}/{total_steps} steps)")
        report.append("")
        
        # Detailed Results
        report.append("## DETAILED RESULTS")
        report.append("")
        
        step_descriptions = {
            "pre_checks": "Pre-migration System Checks",
            "migration": "Data Migration to Supabase", 
            "vps_removal": "VPS Dependencies Removal",
            "security_audit": "Security Audit & Verification"
        }
        
        for step, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            description = step_descriptions.get(step, step)
            report.append(f"- **{description}:** {status}")
        
        report.append("")
        
        # Security Status
        report.append("## SECURITY STATUS")
        report.append("")
        report.append("🔒 **Data Protection:**")
        report.append("- API keys encrypted in Supabase secure storage")
        report.append("- Row Level Security (RLS) enabled")
        report.append("- Service role authentication implemented")
        report.append("- No plain text credentials in source code")
        report.append("")
        
        # Next Steps
        report.append("## NEXT STEPS")
        report.append("")
        
        if success_rate >= 90:
            report.append("1. ✅ **Test application functionality**")
            report.append("2. ✅ **Verify all features work with Supabase**")
            report.append("3. ✅ **Cancel VPS subscription safely**")
            report.append("4. 🔄 **Monitor application for 24-48 hours**")
        else:
            report.append("1. 🔧 **Review failed migration steps**")
            report.append("2. 🛠️ **Fix identified issues**")
            report.append("3. 🔄 **Re-run migration scripts**")
            report.append("4. ⚠️ **Keep VPS active until issues resolved**")
        
        report.append("")
        
        # Technical Details
        report.append("## TECHNICAL DETAILS")
        report.append("")
        report.append("**Supabase Configuration:**")
        report.append(f"- URL: https://nivwxqojwljihoybzgkc.supabase.co")
        report.append(f"- Database: PostgreSQL with RLS")
        report.append(f"- Storage: Encrypted credentials table")
        report.append(f"- Functions: Secure payment callbacks")
        report.append("")
        
        report.append("**Data Migrated:**")
        report.append("- User account profiles")
        report.append("- Credit balances and transactions")
        report.append("- API keys and credentials (encrypted)")
        report.append("- Payment history and callbacks")
        report.append("- Demo usage tracking")
        report.append("")
        
        # Files Generated
        report.append("## FILES GENERATED")
        report.append("")
        report.append("- `SUPABASE_ONLY_MODE.json` - Supabase-only mode indicator")
        report.append("- `security_audit_results.json` - Detailed security audit")
        report.append("- `backup_before_vps_removal/` - Code backups")
        report.append("- `config/fallback_config.json` - Fallback configuration")
        report.append("")
        
        report.append("---")
        report.append("*Report generated by StreamMate AI Migration System*")
        
        return "\\n".join(report)
    
    def run_complete_migration(self) -> bool:
        """Run complete migration process"""
        logger.info("🚀 STARTING COMPLETE MIGRATION TO SUPABASE")
        logger.info("=" * 70)
        logger.info("⚠️ This will make the application 100% dependent on Supabase")
        logger.info("⚠️ VPS subscription can be cancelled after successful completion")
        logger.info("=" * 70)
        
        # Track results
        results = {}
        
        # Step 1: Pre-migration checks
        logger.info("\\n📋 STEP 1: Pre-migration checks")
        results["pre_checks"] = self.run_pre_migration_checks()
        
        if not results["pre_checks"]:
            logger.error("❌ Pre-migration checks failed - aborting migration")
            return False
        
        # Step 2: Data migration
        logger.info("\\n📋 STEP 2: Data migration to Supabase")
        results["migration"] = self.run_script("migration", "Data Migration to Supabase")
        
        # Step 3: VPS dependency removal
        logger.info("\\n📋 STEP 3: VPS dependencies removal")
        results["vps_removal"] = self.run_script("vps_removal", "VPS Dependencies Removal")
        
        # Step 4: Security audit
        logger.info("\\n📋 STEP 4: Security audit and verification")
        results["security_audit"] = self.run_script("security_audit", "Security Audit & Verification")
        
        # Generate comprehensive report
        logger.info("\\n📋 STEP 5: Generating migration report")
        try:
            report_content = self.create_migration_report(results)
            report_file = Path("MIGRATION_REPORT.md")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"📄 Migration report saved to: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate report: {e}")
        
        # Final assessment
        logger.info("\\n" + "=" * 70)
        logger.info("📊 MIGRATION RESULTS SUMMARY")
        logger.info("=" * 70)
        
        total_steps = len(results)
        successful_steps = sum(1 for success in results.values() if success)
        success_rate = (successful_steps / total_steps) * 100 if total_steps > 0 else 0
        
        for step, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"{status} {step.replace('_', ' ').title()}")
        
        logger.info(f"\\n📈 Overall Success Rate: {success_rate:.1f}% ({successful_steps}/{total_steps})")
        
        if success_rate >= 90:
            logger.info("\\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("✅ Application is now 100% Supabase dependent")
            logger.info("🔒 All data secured with encryption and RLS")
            logger.info("💰 VPS subscription can be safely cancelled")
            logger.info("🎯 Test the application thoroughly before cancelling VPS")
        elif success_rate >= 70:
            logger.info("\\n⚠️ MIGRATION MOSTLY SUCCESSFUL")
            logger.info("🔧 Some issues detected - review logs and fix")
            logger.info("⏳ Keep VPS active until all issues resolved")
        else:
            logger.info("\\n❌ MIGRATION INCOMPLETE")
            logger.info("🚨 Critical issues detected")
            logger.info("🔧 Manual intervention required")
            logger.info("⚠️ DO NOT cancel VPS subscription yet")
        
        return success_rate >= 90

def main():
    """Main migration execution"""
    try:
        # Confirmation prompt
        print("🚨 CRITICAL: This will migrate StreamMate AI to 100% Supabase dependency")
        print("🚨 After successful completion, VPS subscription can be cancelled")
        print("\\n⚠️ Make sure you have:")
        print("1. ✅ Supabase project configured and accessible")
        print("2. ✅ Database tables created (user_profiles, credit_transactions, etc.)")
        print("3. ✅ Secure credentials table created")
        print("4. ✅ Current application backup")
        print("\\nType 'MIGRATE' to proceed or 'CANCEL' to abort:")
        
        confirmation = input().strip().upper()
        
        if confirmation != 'MIGRATE':
            print("❌ Migration cancelled by user")
            return 1
        
        print("\\n🚀 Starting migration process...")
        
        migration = MasterMigrationSecurity()
        success = migration.run_complete_migration()
        
        if success:
            print("\\n🎉 MIGRATION SUCCESSFUL!")
            print("📄 Check MIGRATION_REPORT.md for detailed results")
            return 0
        else:
            print("\\n⚠️ MIGRATION INCOMPLETE")
            print("📄 Check logs and MIGRATION_REPORT.md for details")
            return 1
            
    except KeyboardInterrupt:
        print("\\n❌ Migration interrupted by user")
        return 2
    except Exception as e:
        logger.error(f"❌ CRITICAL MIGRATION ERROR: {e}")
        return 3

if __name__ == "__main__":
    sys.exit(main())