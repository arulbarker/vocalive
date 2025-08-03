#!/usr/bin/env python3
"""
Detailed debug script untuk test request Supabase
"""

import requests
import json
from datetime import datetime, timezone

# Supabase configuration
SUPABASE_URL = "https://nivwxqojwljihoybzgkc.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzE3NDY0NywiZXhwIjoyMDY4NzUwNjQ3fQ.r3sftfPQsHkWjK-xQhosh1IS7PSMi5tn4qtsxa5I9CY"

headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

def test_get_user_detailed():
    """Test GET user request dengan detail"""
    print("🔍 Testing GET user request...")
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.mursalinasrul@gmail.com"
        print(f"📝 URL: {url}")
        print(f"📝 Headers: {headers}")
        
        response = requests.get(url, headers=headers)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📊 Headers: {dict(response.headers)}")
        print(f"📊 Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User found: {data}")
            return data[0] if data else None
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_patch_user_detailed(user_data):
    """Test PATCH user request dengan detail"""
    print("\n🔍 Testing PATCH user request...")
    
    try:
        current_credits = user_data.get("credits", 0)
        print(f"💰 Current credits: {current_credits}")
        
        # Calculate new credits (deduct 100000)
        new_credits = current_credits - 100000
        print(f"💰 New credits: {new_credits}")
        
        # Test PATCH request
        patch_data = {
            "credits": new_credits,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.mursalinasrul@gmail.com"
        print(f"📝 URL: {url}")
        print(f"📝 Headers: {headers}")
        print(f"📝 PATCH data: {patch_data}")
        
        response = requests.patch(url, headers=headers, json=patch_data)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📊 Headers: {dict(response.headers)}")
        print(f"📊 Response: {response.text}")
        
        if response.status_code in [200, 204]:
            print("✅ PATCH successful!")
            return True
        else:
            print(f"❌ PATCH failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_patch_user_minimal():
    """Test minimal PATCH user request"""
    print("\n🔍 Testing minimal PATCH user request...")
    
    try:
        patch_data = {
            "credits": 117620
        }
        
        url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.mursalinasrul@gmail.com"
        print(f"📝 URL: {url}")
        print(f"📝 PATCH data: {patch_data}")
        
        response = requests.patch(url, headers=headers, json=patch_data)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📊 Response: {response.text}")
        
        if response.status_code in [200, 204]:
            print("✅ PATCH successful!")
            return True
        else:
            print(f"❌ PATCH failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_table_structure():
    """Test table structure"""
    print("\n🔍 Testing table structure...")
    
    try:
        # Test different endpoints
        endpoints = [
            "/rest/v1/user_profiles",
            "/rest/v1/user_profiles?select=*&limit=1",
            "/rest/v1/user_profiles?select=id,email,credits&limit=1"
        ]
        
        for endpoint in endpoints:
            url = f"{SUPABASE_URL}{endpoint}"
            print(f"\n📝 Testing endpoint: {endpoint}")
            
            response = requests.get(url, headers=headers)
            print(f"📊 Status: {response.status_code}")
            print(f"📊 Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 Detailed Supabase Request Debug Test")
    print("=" * 50)
    
    user_data = test_get_user_detailed()
    if user_data:
        test_patch_user_detailed(user_data)
        test_patch_user_minimal()
    
    test_table_structure()
    
    print("\n" + "=" * 50)
    print("✅ Debug test completed!") 