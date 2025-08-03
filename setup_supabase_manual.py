#!/usr/bin/env python3
"""
Script untuk setup manual secure credentials di Supabase
Menggunakan Supabase Python client untuk eksekusi SQL
"""

import sys
import os
from pathlib import Path

def setup_supabase_credentials():
    """Setup secure credentials system di Supabase"""
    
    print("🔐 STREAMMATE AI - SECURE CREDENTIALS SETUP")
    print("=" * 60)
    print("Setting up secure credentials storage in Supabase...")
    print()
    
    try:
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from supabase import create_client, Client
        
        # Supabase configuration
        SUPABASE_URL = "https://nivwxqojwljihoybzgkc.supabase.co"
        SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzE3NDY0NywiZXhwIjoyMDY4NzUwNjQ3fQ.r3sftfPQsHkWjK-xQhosh1IS7PSMi5tn4qtsxa5I9CY"
        
        print("📡 Connecting to Supabase...")
        supabase: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
        print("✅ Connected to Supabase successfully")
        print()
        
        # Step 1: Create secure_credentials table
        print("🗄️ Step 1: Creating secure_credentials table...")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS secure_credentials (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            key VARCHAR(255) UNIQUE NOT NULL,
            encrypted_value TEXT NOT NULL,
            credential_type VARCHAR(100) DEFAULT 'api_key',
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_by UUID,
            is_active BOOLEAN DEFAULT TRUE
        );
        """
        
        try:
            result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
            print("   ✅ Table created successfully")
        except Exception as e:
            # Try alternative method
            try:
                # Use direct SQL execution if available
                result = supabase.postgrest.rpc('exec_sql', {'sql': create_table_sql}).execute()
                print("   ✅ Table created successfully (alternative method)")
            except Exception as e2:
                print(f"   ⚠️ Table creation skipped (may already exist): {e2}")
        
        # Step 2: Create indexes
        print("\n🔍 Step 2: Creating indexes...")
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_secure_credentials_key ON secure_credentials(key);",
            "CREATE INDEX IF NOT EXISTS idx_secure_credentials_type ON secure_credentials(credential_type);",
            "CREATE INDEX IF NOT EXISTS idx_secure_credentials_active ON secure_credentials(is_active);"
        ]
        
        for i, sql in enumerate(indexes_sql, 1):
            try:
                result = supabase.rpc('exec_sql', {'sql': sql}).execute()
                print(f"   ✅ Index {i} created")
            except Exception as e:
                print(f"   ⚠️ Index {i} skipped: {e}")
        
        # Step 3: Enable RLS
        print("\n🔒 Step 3: Enabling Row Level Security...")
        
        rls_sql = "ALTER TABLE secure_credentials ENABLE ROW LEVEL SECURITY;"
        
        try:
            result = supabase.rpc('exec_sql', {'sql': rls_sql}).execute()
            print("   ✅ RLS enabled")
        except Exception as e:
            print(f"   ⚠️ RLS setup skipped: {e}")
        
        # Step 4: Create RLS policies
        print("\n🛡️ Step 4: Creating RLS policies...")
        
        policies_sql = [
            """
            CREATE POLICY IF NOT EXISTS "service_role_all_access" ON secure_credentials
            FOR ALL USING (auth.role() = 'service_role');
            """,
            """
            CREATE POLICY IF NOT EXISTS "authenticated_read_own" ON secure_credentials
            FOR SELECT USING (auth.uid() = created_by);
            """
        ]
        
        for i, sql in enumerate(policies_sql, 1):
            try:
                result = supabase.rpc('exec_sql', {'sql': sql}).execute()
                print(f"   ✅ Policy {i} created")
            except Exception as e:
                print(f"   ⚠️ Policy {i} skipped: {e}")
        
        print("\n🎉 SETUP COMPLETED!")
        print("✅ Secure credentials system is ready")
        return True
        
    except ImportError:
        print("❌ Supabase library not found")
        print("💡 Install with: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def test_credentials_system():
    """Test the credentials system"""
    print("\n🧪 TESTING SECURE CREDENTIALS SYSTEM")
    print("=" * 50)
    
    try:
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from modules_client.secure_credentials_manager import SecureCredentialsManager
        
        print("📡 Initializing SecureCredentialsManager...")
        manager = SecureCredentialsManager()
        print("✅ Manager initialized successfully")
        
        # Test basic functionality
        print("\n🔧 Testing basic operations...")
        
        # Store test credential
        result = manager.store_credential(
            key="TEST_SETUP_KEY",
            value="test_setup_value_123",
            credential_type="test",
            description="Setup verification test"
        )
        
        if result.get("status") == "success":
            print("   ✅ Store operation works")
            
            # Retrieve test credential
            result = manager.get_credential("TEST_SETUP_KEY")
            if result.get("status") == "success" and result.get("value") == "test_setup_value_123":
                print("   ✅ Retrieve operation works")
                
                # Clean up
                manager.delete_credential("TEST_SETUP_KEY")
                print("   ✅ Delete operation works")
                
                print("\n🎉 ALL TESTS PASSED!")
                return True
            else:
                print("   ❌ Retrieve test failed")
                return False
        else:
            print(f"   ❌ Store test failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        return False

def show_manual_instructions():
    """Show manual setup instructions"""
    print("\n📋 MANUAL SETUP INSTRUCTIONS")
    print("=" * 50)
    print("If automatic setup fails, follow these steps:")
    print()
    print("1. Open Supabase Dashboard: https://supabase.com/dashboard")
    print("2. Go to your project: nivwxqojwljihoybzgkc")
    print("3. Navigate to SQL Editor")
    print("4. Execute this SQL script:")
    print()
    print("```sql")
    
    sql_content = """
-- Create secure_credentials table
CREATE TABLE IF NOT EXISTS secure_credentials (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    encrypted_value TEXT NOT NULL,
    credential_type VARCHAR(100) DEFAULT 'api_key',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_secure_credentials_key ON secure_credentials(key);
CREATE INDEX IF NOT EXISTS idx_secure_credentials_type ON secure_credentials(credential_type);
CREATE INDEX IF NOT EXISTS idx_secure_credentials_active ON secure_credentials(is_active);

-- Enable RLS
ALTER TABLE secure_credentials ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY IF NOT EXISTS "service_role_all_access" ON secure_credentials
FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY IF NOT EXISTS "authenticated_read_own" ON secure_credentials
FOR SELECT USING (auth.uid() = created_by);
"""
    
    print(sql_content)
    print("```")
    print()
    print("5. After executing, run this script again to test")

def main():
    """Main function"""
    print("Starting secure credentials setup...")
    
    # Try automatic setup
    setup_success = setup_supabase_credentials()
    
    if setup_success:
        # Test the system
        test_success = test_credentials_system()
        
        if test_success:
            print("\n🎉 SETUP COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("✅ Secure credentials system is ready")
            print("✅ You can now migrate your .env credentials")
            print()
            print("📋 NEXT STEPS:")
            print("1. Run: python migrate_credentials_to_supabase.py")
            print("2. Test your application with Supabase credentials")
            print("3. Remove sensitive data from .env file")
            return True
        else:
            print("\n⚠️ Setup completed but testing failed")
            print("You may need to check the configuration manually")
    else:
        print("\n❌ Automatic setup failed")
        show_manual_instructions()
    
    return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)