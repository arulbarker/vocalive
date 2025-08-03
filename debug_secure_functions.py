#!/usr/bin/env python3
"""
Debug script untuk cek kenapa secure functions masih failed
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

def debug_secure_functions():
    """Debug secure functions"""
    print("🔍 Debugging Secure Functions")
    print("=" * 60)
    
    # Test update_user_credits function
    print("\n1️⃣ Testing update_user_credits function:")
    print("-" * 40)
    
    test_data = {
        "user_email": "mursalinasrul@gmail.com",
        "credit_amount": 100,
        "transaction_type": "test",
        "description": "Debug test transaction"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/rpc/update_user_credits"
    print(f"URL: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=test_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Result: {result}")
            if result:
                print("✅ Function working!")
            else:
                print("❌ Function returned False")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test process_payment_callback function
    print("\n2️⃣ Testing process_payment_callback function:")
    print("-" * 40)
    
    callback_data = {
        "user_email": "mursalinasrul@gmail.com",
        "payment_amount": 500,
        "payment_status": "success",
        "payment_id": "debug_test_123"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/rpc/process_payment_callback"
    print(f"URL: {url}")
    print(f"Data: {json.dumps(callback_data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=callback_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Result: {result}")
            if result:
                print("✅ Function working!")
            else:
                print("❌ Function returned False")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def check_function_exists():
    """Check if functions exist in database"""
    print("\n🔍 Checking if functions exist:")
    print("-" * 40)
    
    try:
        # Check if functions are accessible
        url = f"{SUPABASE_URL}/rest/v1/rpc/update_user_credits"
        response = requests.post(url, headers=headers, json={})
        print(f"update_user_credits accessible: {response.status_code}")
        
        url = f"{SUPABASE_URL}/rest/v1/rpc/process_payment_callback"
        response = requests.post(url, headers=headers, json={})
        print(f"process_payment_callback accessible: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Error checking functions: {e}")

def check_user_exists():
    """Check if user exists in database"""
    print("\n🔍 Checking if user exists:")
    print("-" * 40)
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.mursalinasrul@gmail.com"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                user = data[0]
                print(f"✅ User found: {user.get('email')}")
                print(f"   Credits: {user.get('credits', 0)}")
                return True
            else:
                print("❌ User not found")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Main function"""
    print("🔍 DEBUGGING SECURE FUNCTIONS")
    print("=" * 60)
    
    # Check if user exists
    user_exists = check_user_exists()
    
    # Check if functions exist
    check_function_exists()
    
    # Debug secure functions
    debug_secure_functions()
    
    print("\n" + "=" * 60)
    print("📊 DEBUG SUMMARY")
    print("-" * 30)
    
    if user_exists:
        print("✅ User exists in database")
    else:
        print("❌ User not found - this might be the issue")
    
    print("\n🔧 POSSIBLE SOLUTIONS:")
    print("1. Check if SQL was executed correctly in Supabase")
    print("2. Verify function names match exactly")
    print("3. Check user email exists in database")
    print("4. Test with different user email")

if __name__ == "__main__":
    main() 