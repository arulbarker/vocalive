#!/usr/bin/env python3
"""
Debug script untuk test request Supabase yang gagal
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

def test_get_user():
    """Test GET user request"""
    print("🔍 Testing GET user request...")
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.mursalinasrul@gmail.com",
            headers=headers
        )
        
        print(f"📊 Status: {response.status_code}")
        print(f"📊 Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User found: {data}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_patch_user():
    """Test PATCH user request"""
    print("\n🔍 Testing PATCH user request...")
    
    try:
        # Get current user data first
        get_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.mursalinasrul@gmail.com",
            headers=headers
        )
        
        if get_response.status_code == 200:
            user_data = get_response.json()[0]
            current_credits = user_data.get("credits", 0)
            print(f"💰 Current credits: {current_credits}")
            
            # Calculate new credits (deduct 100000)
            new_credits = current_credits - 100000
            print(f"💰 New credits: {new_credits}")
            
            # Test PATCH request
            patch_data = {
                "credits": new_credits,
                "updated_at": "2025-07-23T13:41:36.774+00:00"
            }
            
            print(f"📝 PATCH data: {patch_data}")
            
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.mursalinasrul@gmail.com",
                headers=headers,
                json=patch_data
            )
            
            print(f"📊 Status: {response.status_code}")
            print(f"📊 Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ PATCH successful!")
            else:
                print(f"❌ PATCH failed: {response.text}")
        else:
            print(f"❌ Failed to get user: {get_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_patch_user_simple():
    """Test simple PATCH user request"""
    print("\n🔍 Testing simple PATCH user request...")
    
    try:
        patch_data = {
            "credits": 117620  # Reduce by 100000
        }
        
        print(f"📝 PATCH data: {patch_data}")
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.mursalinasrul@gmail.com",
            headers=headers,
            json=patch_data
        )
        
        print(f"📊 Status: {response.status_code}")
        print(f"📊 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ PATCH successful!")
        else:
            print(f"❌ PATCH failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 Supabase Request Debug Test")
    print("=" * 50)
    
    test_get_user()
    test_patch_user()
    test_patch_user_simple()
    
    print("\n" + "=" * 50)
    print("✅ Debug test completed!") 