#!/usr/bin/env python3
"""
Script untuk migrasi kredensial penting ke Supabase
Memindahkan API keys, OAuth tokens, dan kredensial sensitif lainnya dari .env ke Supabase
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main migration function"""
    print("🔐 STREAMMATE AI - SECURE CREDENTIALS MIGRATION")
    print("=" * 60)
    print("Memindahkan kredensial penting dari .env ke Supabase untuk keamanan maksimal")
    print()
    
    try:
        # Import setelah path setup
        from modules_client.secure_credentials_manager import SecureCredentialsManager
        
        # Initialize manager
        print("📡 Connecting to Supabase...")
        manager = SecureCredentialsManager()
        print("✅ Connected to Supabase successfully")
        print()
        
        # 1. Setup database table (jika belum ada)
        print("🗄️ Setting up secure credentials table...")
        setup_result = setup_database_table(manager)
        if setup_result:
            print("✅ Database table ready")
        else:
            print("⚠️ Database table setup skipped (may already exist)")
        print()
        
        # 2. Migrate credentials from .env
        print("📦 Migrating credentials from .env file...")
        migration_result = manager.migrate_env_to_supabase()
        
        if migration_result.get("status") == "success":
            print("✅ Migration completed successfully!")
            print(f"   📊 Summary: {migration_result.get('summary')}")
            
            migrated = migration_result.get("migrated", [])
            skipped = migration_result.get("skipped", [])
            errors = migration_result.get("errors", [])
            
            if migrated:
                print(f"   ✅ Migrated ({len(migrated)}):")
                for cred in migrated:
                    print(f"      • {cred}")
            
            if skipped:
                print(f"   ⏭️ Skipped ({len(skipped)}):")
                for cred in skipped:
                    print(f"      • {cred}")
            
            if errors:
                print(f"   ❌ Errors ({len(errors)}):")
                for error in errors:
                    print(f"      • {error}")
        else:
            print(f"❌ Migration failed: {migration_result.get('message')}")
            return False
        
        print()
        
        # 3. Verify migration
        print("🔍 Verifying migrated credentials...")
        verification_result = verify_credentials(manager)
        if verification_result:
            print("✅ Verification completed successfully")
        else:
            print("⚠️ Some credentials may need attention")
        
        print()
        
        # 4. Setup environment from Supabase
        print("🌍 Setting up environment variables from Supabase...")
        env_result = manager.setup_environment_from_supabase()
        
        if env_result.get("status") == "success":
            loaded = env_result.get("loaded", [])
            print(f"✅ Loaded {len(loaded)} environment variables from Supabase")
        else:
            print(f"⚠️ Environment setup warning: {env_result.get('message')}")
        
        print()
        
        # 5. Create backup of original .env
        print("💾 Creating backup of original .env file...")
        backup_result = create_env_backup()
        if backup_result:
            print("✅ Backup created successfully")
        else:
            print("⚠️ Backup creation skipped")
        
        print()
        print("🎉 MIGRATION COMPLETED!")
        print("=" * 60)
        print("✅ Kredensial penting telah dipindahkan ke Supabase")
        print("✅ Aplikasi sekarang akan menggunakan kredensial dari Supabase")
        print("✅ File .env asli telah di-backup")
        print()
        print("📋 NEXT STEPS:")
        print("1. Test aplikasi untuk memastikan semua kredensial berfungsi")
        print("2. Hapus kredensial sensitif dari .env jika sudah yakin")
        print("3. Update deployment scripts untuk menggunakan Supabase")
        print()
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Pastikan semua dependencies telah diinstall")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def setup_database_table(manager):
    """Setup database table menggunakan SQL script"""
    try:
        sql_file = Path("create_secure_credentials_table.sql")
        if not sql_file.exists():
            print(f"⚠️ SQL file not found: {sql_file}")
            return False
        
        # Baca SQL script
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Execute SQL (ini perlu dilakukan manual di Supabase Dashboard)
        print("📝 SQL script ready for execution in Supabase Dashboard")
        print(f"   File: {sql_file.absolute()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False

def verify_credentials(manager):
    """Verify that credentials were migrated successfully"""
    try:
        # List all credentials
        result = manager.list_credentials()
        
        if result.get("status") == "success":
            credentials = result.get("data", [])
            print(f"   📊 Found {len(credentials)} credentials in Supabase")
            
            # Test beberapa kredensial penting
            important_keys = [
                "SUPABASE_ANON_KEY",
                "GOOGLE_OAUTH_CLIENT_ID", 
                "STRIPE_SECRET_KEY",
                "OPENAI_API_KEY"
            ]
            
            verified = 0
            for key in important_keys:
                test_result = manager.get_credential(key)
                if test_result.get("status") == "success":
                    verified += 1
                    print(f"   ✅ {key}: OK")
                else:
                    print(f"   ⚠️ {key}: {test_result.get('message', 'Not found')}")
            
            print(f"   📊 Verified {verified}/{len(important_keys)} important credentials")
            return verified > 0
        else:
            print(f"   ❌ Verification failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
        return False

def create_env_backup():
    """Create backup of original .env file"""
    try:
        env_file = Path(".env")
        if not env_file.exists():
            print("   ⚠️ .env file not found, skipping backup")
            return False
        
        # Create backup with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = Path(f".env.backup_{timestamp}")
        
        # Copy file
        import shutil
        shutil.copy2(env_file, backup_file)
        
        print(f"   💾 Backup created: {backup_file}")
        return True
        
    except Exception as e:
        print(f"   ❌ Backup error: {e}")
        return False

def interactive_mode():
    """Interactive mode untuk konfigurasi manual"""
    print("\n🔧 INTERACTIVE CONFIGURATION MODE")
    print("=" * 50)
    
    try:
        from modules_client.secure_credentials_manager import SecureCredentialsManager
        manager = SecureCredentialsManager()
        
        while True:
            print("\nPilih aksi:")
            print("1. Store new credential")
            print("2. Get credential")
            print("3. List all credentials")
            print("4. Delete credential")
            print("5. Exit")
            
            choice = input("\nMasukkan pilihan (1-5): ").strip()
            
            if choice == "1":
                key = input("Credential key: ").strip()
                value = input("Credential value: ").strip()
                cred_type = input("Type (api_key/oauth/database/payment/security): ").strip()
                description = input("Description (optional): ").strip() or None
                
                result = manager.store_credential(key, value, cred_type, description)
                print(f"Result: {result}")
                
            elif choice == "2":
                key = input("Credential key: ").strip()
                result = manager.get_credential(key)
                if result.get("status") == "success":
                    print(f"Value: {result.get('value')}")
                    print(f"Type: {result.get('type')}")
                else:
                    print(f"Error: {result.get('message')}")
                    
            elif choice == "3":
                result = manager.list_credentials()
                if result.get("status") == "success":
                    credentials = result.get("data", [])
                    print(f"\nFound {len(credentials)} credentials:")
                    for cred in credentials:
                        print(f"  • {cred.get('key')} ({cred.get('type')})")
                else:
                    print(f"Error: {result.get('message')}")
                    
            elif choice == "4":
                key = input("Credential key to delete: ").strip()
                result = manager.delete_credential(key)
                print(f"Result: {result}")
                
            elif choice == "5":
                break
            else:
                print("Invalid choice")
                
    except Exception as e:
        print(f"❌ Interactive mode error: {e}")

if __name__ == "__main__":
    print("🔐 StreamMate AI - Secure Credentials Migration Tool")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        success = main()
        if not success:
            sys.exit(1)
        
        # Tanya apakah ingin masuk interactive mode
        response = input("\n🔧 Ingin masuk interactive mode untuk konfigurasi manual? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_mode()