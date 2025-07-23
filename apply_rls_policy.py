#!/usr/bin/env python3
"""
Script untuk Apply RLS Policies di Supabase
Mengatasi masalah 401 "Missing authorization header" untuk callback
"""

import requests
import json
import os
from datetime import datetime

def apply_rls_policies():
    """Apply RLS policies untuk Edge Functions"""
    print("🔧 Applying RLS Policies for Edge Functions")
    
    # Supabase credentials
    supabase_url = "https://nivwxqojwljihoybzgkc.supabase.co"
    service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzE3NDY0NywiZXhwIjoyMDY4NzUwNjQ3fQ.r3sftfPQsHkWjK-xQhosh1IS7PSMi5tn4qtsxa5I9CY"
    
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # SQL queries untuk apply policies
    policies_sql = [
        # 1. Payment Transactions
        """
        CREATE POLICY IF NOT EXISTS "Allow Edge Functions - Payment Transactions" 
        ON payment_transactions 
        FOR ALL 
        USING (auth.role() = 'service_role' OR auth.role() = 'anon')
        WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');
        """,
        
        # 2. Users
        """
        CREATE POLICY IF NOT EXISTS "Allow Edge Functions - Users" 
        ON users 
        FOR ALL 
        USING (auth.role() = 'service_role' OR auth.role() = 'anon')
        WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');
        """,
        
        # 3. Credit Transactions
        """
        CREATE POLICY IF NOT EXISTS "Allow Edge Functions - Credit Transactions" 
        ON credit_transactions 
        FOR ALL 
        USING (auth.role() = 'service_role' OR auth.role() = 'anon')
        WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');
        """,
        
        # 4. Demo Usage
        """
        CREATE POLICY IF NOT EXISTS "Allow Edge Functions - Demo Usage" 
        ON demo_usage 
        FOR ALL 
        USING (auth.role() = 'service_role' OR auth.role() = 'anon')
        WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');
        """,
        
        # 5. Session Tracking
        """
        CREATE POLICY IF NOT EXISTS "Allow Edge Functions - Session Tracking" 
        ON session_tracking 
        FOR ALL 
        USING (auth.role() = 'service_role' OR auth.role() = 'anon')
        WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');
        """,
        
        # 6. Package Subscriptions
        """
        CREATE POLICY IF NOT EXISTS "Allow Edge Functions - Package Subscriptions" 
        ON package_subscriptions 
        FOR ALL 
        USING (auth.role() = 'service_role' OR auth.role() = 'anon')
        WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');
        """
    ]
    
    # Alternative: Disable RLS completely
    disable_rls_sql = [
        "ALTER TABLE payment_transactions DISABLE ROW LEVEL SECURITY;",
        "ALTER TABLE users DISABLE ROW LEVEL SECURITY;",
        "ALTER TABLE credit_transactions DISABLE ROW LEVEL SECURITY;",
        "ALTER TABLE demo_usage DISABLE ROW LEVEL SECURITY;",
        "ALTER TABLE session_tracking DISABLE ROW LEVEL SECURITY;",
        "ALTER TABLE package_subscriptions DISABLE ROW LEVEL SECURITY;"
    ]
    
    print("📋 Available options:")
    print("1. Apply RLS Policies (Recommended)")
    print("2. Disable RLS Completely (Faster)")
    print("3. Check current RLS status")
    
    choice = input("Enter your choice (1/2/3): ").strip()
    
    if choice == "1":
        print("\n🔧 Applying RLS Policies...")
        for i, sql in enumerate(policies_sql, 1):
            print(f"📝 Applying policy {i}/6...")
            try:
                response = requests.post(
                    f"{supabase_url}/rest/v1/rpc/exec_sql",
                    headers=headers,
                    json={"sql": sql}
                )
                if response.status_code == 200:
                    print(f"✅ Policy {i} applied successfully")
                else:
                    print(f"❌ Policy {i} failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Error applying policy {i}: {e}")
    
    elif choice == "2":
        print("\n🔧 Disabling RLS completely...")
        for i, sql in enumerate(disable_rls_sql, 1):
            print(f"📝 Disabling RLS for table {i}/6...")
            try:
                response = requests.post(
                    f"{supabase_url}/rest/v1/rpc/exec_sql",
                    headers=headers,
                    json={"sql": sql}
                )
                if response.status_code == 200:
                    print(f"✅ RLS disabled for table {i}")
                else:
                    print(f"❌ Failed to disable RLS for table {i}: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Error disabling RLS for table {i}: {e}")
    
    elif choice == "3":
        print("\n🔍 Checking RLS status...")
        check_sql = """
        SELECT 
            schemaname,
            tablename,
            rowsecurity
        FROM pg_tables 
        WHERE tablename IN (
            'payment_transactions',
            'users', 
            'credit_transactions',
            'demo_usage',
            'session_tracking',
            'package_subscriptions'
        )
        ORDER BY tablename;
        """
        try:
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={"sql": check_sql}
            )
            if response.status_code == 200:
                print("📊 RLS Status:")
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"❌ Failed to check RLS status: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error checking RLS status: {e}")
    
    else:
        print("❌ Invalid choice!")

def test_callback_after_policy():
    """Test callback setelah apply policy"""
    print("\n🧪 Testing callback after policy application...")
    
    url = "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/ipaymu-webhook"
    
    data = {
        "trx_id": "test_after_policy",
        "sid": "test-session-policy",
        "reference_id": "mursalinasrul@gmail.com_test_policy",
        "status": "berhasil",
        "status_code": "1",
        "sub_total": "50000",
        "total": "52500",
        "amount": "52500",
        "fee": "6000",
        "paid_off": "46500",
        "created_at": "2025-07-23 09:04:42",
        "expired_at": "2025-07-24 09:04:42",
        "paid_at": "2025-07-23T09:05:14+07:00",
        "settlement_status": "settled",
        "transaction_status_code": "1",
        "is_escrow": "false",
        "system_notes": "Test after policy",
        "via": "va",
        "channel": "bag",
        "payment_no": "test_payment_no",
        "buyer_name": "test_policy",
        "buyer_email": "mursalinasrul@gmail.com",
        "buyer_phone": "test_policy",
        "additional_info": "[]",
        "url": url,
        "va": "test_va"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        print(f"📡 Testing callback to: {url}")
        response = requests.post(url, data=data, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Callback works after policy application!")
            try:
                result = response.json()
                print(f"📈 Result: {json.dumps(result, indent=2)}")
            except:
                print("⚠️ Response is not JSON format")
        else:
            print(f"❌ ERROR: Callback still fails with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

def main():
    """Main function"""
    print("🚀 StreamMate AI - RLS Policy Manager")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now()}")
    print("=" * 50)
    
    # Apply policies
    apply_rls_policies()
    
    # Test callback
    test_callback_after_policy()
    
    print("\n" + "=" * 50)
    print("🏁 RLS Policy management completed!")
    print("=" * 50)

if __name__ == "__main__":
    main() 