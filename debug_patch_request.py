#!/usr/bin/env python3
"""
Debug script untuk test PATCH request yang gagal
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

def test_patch_with_exact_data():
    """Test PATCH dengan data yang sama persis seperti di kode"""
    print("🔍 Testing PATCH with exact data from code...")
    
    try:
        email = "mursalinasrul@gmail.com"
        
        # Get current user data
        get_url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
        get_response = requests.get(get_url, headers=headers)
        
        if get_response.status_code != 200:
            print(f"❌ Failed to get user: {get_response.text}")
            return False
        
        user_data = get_response.json()[0]
        current_credits = user_data.get("credits", 0)
        print(f"💰 Current credits: {current_credits}")
        
        # Calculate new balance (deduct 100000)
        new_credits = current_credits - 100000
        print(f"💰 New credits: {new_credits}")
        
        # Create update data exactly like in the code
        update_data = {
            "credits": new_credits,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"📝 Update data: {update_data}")
        
        # Test PATCH request
        patch_url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
        print(f"📝 PATCH URL: {patch_url}")
        
        response = requests.patch(patch_url, headers=headers, json=update_data)
        
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
        import traceback
        traceback.print_exc()
        return False

def test_patch_with_minimal_data():
    """Test PATCH dengan data minimal"""
    print("\n🔍 Testing PATCH with minimal data...")
    
    try:
        email = "mursalinasrul@gmail.com"
        
        # Minimal update data
        update_data = {
            "credits": 17620  # Just reduce credits
        }
        
        print(f"📝 Update data: {update_data}")
        
        # Test PATCH request
        patch_url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
        print(f"📝 PATCH URL: {patch_url}")
        
        response = requests.patch(patch_url, headers=headers, json=update_data)
        
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

def test_patch_with_different_headers():
    """Test PATCH dengan headers yang berbeda"""
    print("\n🔍 Testing PATCH with different headers...")
    
    try:
        email = "mursalinasrul@gmail.com"
        
        # Different headers
        test_headers = {
            "apikey": SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"  # Add Prefer header
        }
        
        update_data = {
            "credits": 17620
        }
        
        print(f"📝 Headers: {test_headers}")
        print(f"📝 Update data: {update_data}")
        
        patch_url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
        response = requests.patch(patch_url, headers=test_headers, json=update_data)
        
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

if __name__ == "__main__":
    print("🔍 PATCH Request Debug Test")
    print("=" * 50)
    
    test_patch_with_exact_data()
    test_patch_with_minimal_data()
    test_patch_with_different_headers()
    
    print("\n" + "=" * 50)
    print("✅ Debug test completed!") 