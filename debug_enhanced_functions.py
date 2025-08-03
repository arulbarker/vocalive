#!/usr/bin/env python3
"""
Debug enhanced functions to understand why they return false
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

def check_user_data():
    """Check current user data"""
    print("🔍 CHECKING USER DATA")
    print("=" * 60)
    
    try:
        # Get user profile
        url = f"{SUPABASE_URL}/rest/v1/user_profiles"
        params = {"email": "eq.mursalinasrul@gmail.com"}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                user = data[0]
                print(f"✅ User found:")
                print(f"   Email: {user.get('email')}")
                print(f"   Credits: {user.get('credits')}")
                print(f"   Created: {user.get('created_at')}")
            else:
                print("❌ User not found")
        else:
            print(f"❌ Failed to get user: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking user data: {e}")

def check_credit_transactions():
    """Check recent credit transactions"""
    print("\n🔍 CHECKING CREDIT TRANSACTIONS")
    print("=" * 60)
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/credit_transactions"
        params = {"email": "eq.mursalinasrul@gmail.com", "order": "created_at.desc", "limit": "5"}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} recent transactions:")
            for tx in data:
                print(f"   - {tx.get('transaction_type')}: {tx.get('amount')} credits ({tx.get('created_at')})")
        else:
            print(f"❌ Failed to get transactions: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking transactions: {e}")

def test_enhanced_functions():
    """Test enhanced functions with different scenarios"""
    print("\n🧪 TESTING ENHANCED FUNCTIONS")
    print("=" * 60)
    
    # Test 1: Valid credit update
    print("\n1️⃣ Testing valid credit update:")
    try:
        test_data = {
            "user_email": "mursalinasrul@gmail.com",
            "credit_amount": 100,
            "transaction_type": "test_enhanced",
            "description": "Enhanced function test"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/rpc/update_user_credits"
        response = requests.post(url, headers=headers, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ update_user_credits: {result}")
        else:
            print(f"   ❌ update_user_credits failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Payment callback
    print("\n2️⃣ Testing payment callback:")
    try:
        callback_data = {
            "user_email": "mursalinasrul@gmail.com",
            "payment_amount": 500,
            "payment_status": "success",
            "payment_id": "enhanced_test_123"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/rpc/process_payment_callback"
        response = requests.post(url, headers=headers, json=callback_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ process_payment_callback: {result}")
        else:
            print(f"   ❌ process_payment_callback failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Invalid user
    print("\n3️⃣ Testing with invalid user:")
    try:
        invalid_data = {
            "user_email": "nonexistent@email.com",
            "credit_amount": 100,
            "transaction_type": "test",
            "description": "Invalid user test"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/rpc/update_user_credits"
        response = requests.post(url, headers=headers, json=invalid_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ update_user_credits (invalid): {result} (should be false)")
        else:
            print(f"   ❌ update_user_credits (invalid) failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Zero amount
    print("\n4️⃣ Testing with zero amount:")
    try:
        zero_data = {
            "user_email": "mursalinasrul@gmail.com",
            "credit_amount": 0,
            "transaction_type": "test",
            "description": "Zero amount test"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/rpc/update_user_credits"
        response = requests.post(url, headers=headers, json=zero_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ update_user_credits (zero): {result} (should be false)")
        else:
            print(f"   ❌ update_user_credits (zero) failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def check_error_logs():
    """Check error logs if they exist"""
    print("\n🔍 CHECKING ERROR LOGS")
    print("=" * 60)
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/error_logs"
        params = {"order": "created_at.desc", "limit": "5"}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"✅ Found {len(data)} recent error logs:")
                for log in data:
                    print(f"   - {log.get('error_type')}: {log.get('error_message')} ({log.get('created_at')})")
            else:
                print("✅ No error logs found")
        else:
            print(f"❌ Failed to get error logs: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking error logs: {e}")

def main():
    """Main function"""
    print("🔧 ENHANCED FUNCTIONS DEBUG")
    print("=" * 60)
    
    check_user_data()
    check_credit_transactions()
    test_enhanced_functions()
    check_error_logs()
    
    print("\n" + "=" * 60)
    print("📊 DEBUG SUMMARY")
    print("-" * 30)
    print("✅ Enhanced functions tested")
    print("📋 Check results above for issues")

if __name__ == "__main__":
    main() 