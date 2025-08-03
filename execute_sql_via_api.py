#!/usr/bin/env python3
"""
Script untuk execute SQL via Supabase API
"""

import requests
import json

# Supabase configuration
SUPABASE_URL = "https://nivwxqojwljihoybzgkc.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzE3NDY0NywiZXhwIjoyMDY4NzUwNjQ3fQ.r3sftfPQsHkWjK-xQhosh1IS7PSMi5tn4qtsxa5I9CY"

headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

def execute_sql_via_api():
    """Execute SQL via Supabase API"""
    print("🔧 Executing SQL via API")
    print("=" * 60)
    
    # Simple SQL to create functions
    sql_commands = [
        # Drop existing functions
        "DROP FUNCTION IF EXISTS update_user_credits(TEXT, INTEGER, TEXT, TEXT);",
        "DROP FUNCTION IF EXISTS process_payment_callback(TEXT, INTEGER, TEXT, TEXT);",
        
        # Create test function
        """
        CREATE OR REPLACE FUNCTION test_function()
        RETURNS TEXT
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN 'Hello World!';
        END;
        $$;
        """,
        
        # Create update_user_credits function
        """
        CREATE OR REPLACE FUNCTION update_user_credits(
            user_email TEXT,
            credit_amount INTEGER,
            transaction_type TEXT,
            description TEXT
        )
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        BEGIN
            UPDATE user_profiles 
            SET credits = credits + credit_amount
            WHERE email = user_email;
            
            INSERT INTO credit_transactions (
                email, amount, transaction_type, description, created_at
            ) VALUES (
                user_email, credit_amount, transaction_type, description, NOW()
            );
            
            RETURN TRUE;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN FALSE;
        END;
        $$;
        """,
        
        # Create process_payment_callback function
        """
        CREATE OR REPLACE FUNCTION process_payment_callback(
            user_email TEXT,
            payment_amount INTEGER,
            payment_status TEXT,
            payment_id TEXT
        )
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        BEGIN
            IF payment_status = 'success' THEN
                UPDATE user_profiles 
                SET credits = credits + payment_amount
                WHERE email = user_email;
                
                INSERT INTO credit_transactions (
                    email, amount, transaction_type, description, created_at
                ) VALUES (
                    user_email, payment_amount, 'credit_add', 
                    'Payment callback: ' || payment_id, NOW()
                );
                
                RETURN TRUE;
            END IF;
            
            RETURN FALSE;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN FALSE;
        END;
        $$;
        """,
        
        # Grant permissions
        "GRANT EXECUTE ON FUNCTION test_function() TO service_role;",
        "GRANT EXECUTE ON FUNCTION update_user_credits(TEXT, INTEGER, TEXT, TEXT) TO service_role;",
        "GRANT EXECUTE ON FUNCTION process_payment_callback(TEXT, INTEGER, TEXT, TEXT) TO service_role;"
    ]
    
    success_count = 0
    total_commands = len(sql_commands)
    
    for i, sql in enumerate(sql_commands, 1):
        try:
            print(f"Executing SQL {i}/{total_commands}...")
            
            # Execute SQL via API
            url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
            data = {"sql": sql}
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                print(f"✅ SQL {i} executed successfully")
                success_count += 1
            else:
                print(f"❌ SQL {i} failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error executing SQL {i}: {e}")
    
    print(f"\n📊 SQL Execution Summary: {success_count}/{total_commands} successful")
    
    if success_count == total_commands:
        print("✅ All SQL commands executed successfully!")
        return True
    else:
        print("❌ Some SQL commands failed")
        return False

def test_functions_after_execution():
    """Test functions after SQL execution"""
    print("\n🧪 Testing Functions After Execution")
    print("=" * 60)
    
    # Test simple function first
    try:
        url = f"{SUPABASE_URL}/rest/v1/rpc/test_function"
        response = requests.post(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ test_function: {result}")
        else:
            print(f"❌ test_function failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing test_function: {e}")
    
    # Test update_user_credits function
    try:
        test_data = {
            "user_email": "mursalinasrul@gmail.com",
            "credit_amount": 100,
            "transaction_type": "test",
            "description": "API test transaction"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/rpc/update_user_credits"
        response = requests.post(url, headers=headers, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ update_user_credits: {result}")
        else:
            print(f"❌ update_user_credits failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing update_user_credits: {e}")
    
    # Test process_payment_callback function
    try:
        callback_data = {
            "user_email": "mursalinasrul@gmail.com",
            "payment_amount": 500,
            "payment_status": "success",
            "payment_id": "api_test_123"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/rpc/process_payment_callback"
        response = requests.post(url, headers=headers, json=callback_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ process_payment_callback: {result}")
        else:
            print(f"❌ process_payment_callback failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing process_payment_callback: {e}")

def provide_manual_instructions():
    """Provide manual instructions for SQL execution"""
    print("\n📋 MANUAL SQL EXECUTION INSTRUCTIONS")
    print("=" * 60)
    
    print("Jika API execution gagal, lakukan manual:")
    print("\n1️⃣ Buka Supabase Dashboard:")
    print("   - Login ke https://supabase.com")
    print("   - Pilih project Anda")
    
    print("\n2️⃣ Buka SQL Editor:")
    print("   - Klik 'SQL Editor' di sidebar")
    print("   - Klik 'New Query'")
    
    print("\n3️⃣ Copy dan paste SQL ini:")
    sql_code = """
-- Drop existing functions
DROP FUNCTION IF EXISTS update_user_credits(TEXT, INTEGER, TEXT, TEXT);
DROP FUNCTION IF EXISTS process_payment_callback(TEXT, INTEGER, TEXT, TEXT);

-- Create test function
CREATE OR REPLACE FUNCTION test_function()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN 'Hello World!';
END;
$$;

-- Create update_user_credits function
CREATE OR REPLACE FUNCTION update_user_credits(
    user_email TEXT,
    credit_amount INTEGER,
    transaction_type TEXT,
    description TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    UPDATE user_profiles 
    SET credits = credits + credit_amount
    WHERE email = user_email;
    
    INSERT INTO credit_transactions (
        email, amount, transaction_type, description, created_at
    ) VALUES (
        user_email, credit_amount, transaction_type, description, NOW()
    );
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$;

-- Create process_payment_callback function
CREATE OR REPLACE FUNCTION process_payment_callback(
    user_email TEXT,
    payment_amount INTEGER,
    payment_status TEXT,
    payment_id TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    IF payment_status = 'success' THEN
        UPDATE user_profiles 
        SET credits = credits + payment_amount
        WHERE email = user_email;
        
        INSERT INTO credit_transactions (
            email, amount, transaction_type, description, created_at
        ) VALUES (
            user_email, payment_amount, 'credit_add', 
            'Payment callback: ' || payment_id, NOW()
        );
        
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION test_function() TO service_role;
GRANT EXECUTE ON FUNCTION update_user_credits(TEXT, INTEGER, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION process_payment_callback(TEXT, INTEGER, TEXT, TEXT) TO service_role;

-- Test the functions
SELECT test_function() as test_result;
SELECT 'Functions created successfully!' as status;
"""
    
    print(sql_code)
    
    print("\n4️⃣ Execute SQL:")
    print("   - Klik tombol 'Run' atau tekan Ctrl+Enter")
    print("   - Tunggu sampai selesai")
    
    print("\n5️⃣ Test functions:")
    print("   - Jalankan: python debug_secure_functions.py")

def main():
    """Main function"""
    print("🔧 EXECUTE SQL VIA API")
    print("=" * 60)
    
    # Try API execution first
    print("Trying API execution...")
    success = execute_sql_via_api()
    
    if success:
        # Test functions after execution
        test_functions_after_execution()
    else:
        # Provide manual instructions
        provide_manual_instructions()
    
    print("\n" + "=" * 60)
    print("📊 EXECUTION SUMMARY")
    print("-" * 30)
    
    if success:
        print("✅ SQL executed via API successfully!")
        print("✅ Functions should now be working")
    else:
        print("❌ API execution failed")
        print("📋 Follow manual instructions above")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Execute SQL (API or manual)")
    print("2. Test functions")
    print("3. Verify security")
    print("4. Deploy to production")

if __name__ == "__main__":
    main() 