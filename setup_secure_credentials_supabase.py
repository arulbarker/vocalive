#!/usr/bin/env python3
"""
Script untuk menjalankan SQL setup di Supabase
Membuat tabel dan fungsi untuk secure credentials storage
"""

import sys
import os
import requests
import json
from pathlib import Path

def execute_sql_in_supabase():
    """Execute SQL script di Supabase menggunakan REST API"""
    
    print("🗄️ SUPABASE SQL EXECUTOR")
    print("=" * 50)
    print("Setting up secure credentials table and functions...")
    print()
    
    # Supabase configuration
    SUPABASE_URL = "https://nivwxqojwljihoybzgkc.supabase.co"
    SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzE3NDY0NywiZXhwIjoyMDY4NzUwNjQ3fQ.r3sftfPQsHkWjK-xQhosh1IS7PSMi5tn4qtsxa5I9CY"
    
    headers = {
        "apikey": SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Baca SQL file
        sql_file = Path("create_secure_credentials_table.sql")
        if not sql_file.exists():
            print(f"❌ SQL file not found: {sql_file}")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"📄 Loaded SQL script: {sql_file}")
        print(f"📏 Script size: {len(sql_content)} characters")
        print()
        
        # Split SQL menjadi statements individual
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        print(f"🔧 Executing {len(statements)} SQL statements...")
        print()
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue
                
            print(f"[{i}/{len(statements)}] Executing statement...")
            
            try:
                # Execute SQL statement
                url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
                data = {"sql": statement}
                
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    print(f"   ✅ Success")
                    success_count += 1
                else:
                    print(f"   ❌ Error: {response.status_code} - {response.text}")
                    error_count += 1
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                error_count += 1
        
        print()
        print("📊 EXECUTION SUMMARY:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Total: {len(statements)}")
        
        if error_count == 0:
            print()
            print("🎉 All SQL statements executed successfully!")
            print("✅ Secure credentials system is ready")
            return True
        else:
            print()
            print("⚠️ Some statements failed. Manual execution may be required.")
            print("💡 Try executing the SQL script manually in Supabase Dashboard")
            return False
            
    except Exception as e:
        print(f"❌ SQL execution failed: {e}")
        return False

def test_secure_credentials_system():
    """Test the secure credentials system"""
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
        
        # Test 1: Store a test credential
        print("\n🔧 Test 1: Store test credential...")
        result = manager.store_credential(
            key="TEST_API_KEY",
            value="test_value_12345",
            credential_type="api_key",
            description="Test credential for system verification"
        )
        
        if result.get("status") == "success":
            print("   ✅ Store test passed")
        else:
            print(f"   ❌ Store test failed: {result.get('message')}")
            return False
        
        # Test 2: Retrieve the test credential
        print("\n🔍 Test 2: Retrieve test credential...")
        result = manager.get_credential("TEST_API_KEY")
        
        if result.get("status") == "success":
            retrieved_value = result.get("value")
            if retrieved_value == "test_value_12345":
                print("   ✅ Retrieve test passed")
            else:
                print(f"   ❌ Retrieve test failed: value mismatch")
                return False
        else:
            print(f"   ❌ Retrieve test failed: {result.get('message')}")
            return False
        
        # Test 3: List credentials
        print("\n📋 Test 3: List credentials...")
        result = manager.list_credentials()
        
        if result.get("status") == "success":
            credentials = result.get("data", [])
            print(f"   ✅ List test passed: found {len(credentials)} credentials")
        else:
            print(f"   ❌ List test failed: {result.get('message')}")
            return False
        
        # Test 4: Delete test credential
        print("\n🗑️ Test 4: Delete test credential...")
        result = manager.delete_credential("TEST_API_KEY")
        
        if result.get("status") == "success":
            print("   ✅ Delete test passed")
        else:
            print(f"   ❌ Delete test failed: {result.get('message')}")
            return False
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Secure credentials system is working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        return False

def main():
    """Main function"""
    print("🔐 STREAMMATE AI - SECURE CREDENTIALS SETUP")
    print("=" * 60)
    print("Setting up secure credentials storage in Supabase...")
    print()
    
    # Step 1: Execute SQL setup
    sql_success = execute_sql_in_supabase()
    
    if not sql_success:
        print("\n💡 MANUAL SETUP REQUIRED:")
        print("1. Open Supabase Dashboard")
        print("2. Go to SQL Editor")
        print("3. Execute the SQL script: create_secure_credentials_table.sql")
        print("4. Run this script again to test the system")
        return False
    
    # Step 2: Test the system
    test_success = test_secure_credentials_system()
    
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
        print("\n❌ SETUP FAILED")
        print("Please check the errors above and try again")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)