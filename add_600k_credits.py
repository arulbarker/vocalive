#!/usr/bin/env python3
"""
Script untuk menambah 600,000 kredit ke akun mursalinasrul@gmail.com
"""

try:
    import requests
except ImportError:
    print("❌ requests module not found. Installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
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

def add_600k_credits():
    """Tambah 600,000 kredit ke akun"""
    print("🔧 Adding 600,000 credits to account...")
    print("=" * 50)
    
    try:
        email = "mursalinasrul@gmail.com"
        credits_to_add = 600000
        
        # 1. Get current balance
        print("1️⃣ Getting current balance...")
        get_url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
        get_response = requests.get(get_url, headers=headers)
        
        if get_response.status_code != 200:
            print(f"❌ Failed to get user: {get_response.text}")
            return False
        
        users = get_response.json()
        if not users:
            print("❌ User not found")
            return False
        
        user = users[0]
        current_credits = user.get("credits", 0)
        print(f"💰 Current credits: {current_credits:,}")
        
        # 2. Calculate new balance
        new_credits = current_credits + credits_to_add
        print(f"💰 New credits: {new_credits:,}")
        
        # 3. Update credits
        print("2️⃣ Updating credits...")
        update_data = {
            "credits": new_credits,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        patch_url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
        patch_response = requests.patch(patch_url, headers=headers, json=update_data)
        
        print(f"📊 Status: {patch_response.status_code}")
        
        if patch_response.status_code in [200, 204]:
            print("✅ Credits updated successfully!")
            
            # 4. Verify updated balance
            print("3️⃣ Verifying updated balance...")
            verify_response = requests.get(get_url, headers=headers)
            if verify_response.status_code == 200:
                updated_user = verify_response.json()[0]
                updated_credits = updated_user.get("credits", 0)
                print(f"💰 Updated credits: {updated_credits:,}")
                
                if updated_credits == new_credits:
                    print("✅ Credits added successfully!")
                    print(f"🎉 New balance: {updated_credits:,} credits")
                    print(f"💵 IDR Value: Rp {updated_credits:,}")
                    return True
                else:
                    print(f"❌ Credits not updated correctly: expected {new_credits:,}, got {updated_credits:,}")
                    return False
            else:
                print(f"❌ Failed to verify: {verify_response.text}")
                return False
        else:
            print(f"❌ Failed to update credits: {patch_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding credits: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_final_balance():
    """Cek balance akhir"""
    print("\n🔍 Final Balance Check...")
    print("=" * 50)
    
    try:
        email = "mursalinasrul@gmail.com"
        url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            users = response.json()
            if users:
                user = users[0]
                credits = user.get("credits", 0)
                email = user.get("email", "N/A")
                updated_at = user.get("updated_at", "N/A")
                
                print(f"📧 Email: {email}")
                print(f"💰 Credits: {credits:,}")
                print(f"🕒 Last Updated: {updated_at}")
                print(f"💳 WALLET BALANCE: {credits:,} credits")
                print(f"💵 IDR Value: Rp {credits:,}")
                
                return credits
            else:
                print("❌ User not found")
                return 0
        else:
            print(f"❌ Error: {response.text}")
            return 0
            
    except Exception as e:
        print(f"❌ Error checking balance: {e}")
        return 0

if __name__ == "__main__":
    print("🔧 ADD 600,000 CREDITS TO ACCOUNT")
    print("=" * 50)
    
    # Add credits
    success = add_600k_credits()
    
    if success:
        # Check final balance
        final_balance = check_final_balance()
        
        print("\n" + "=" * 50)
        print("✅ Credits added successfully!")
        print(f"🎉 Your wallet now has {final_balance:,} credits!")
        print("🚀 You can now test Basic and Pro package purchases!")
    else:
        print("\n" + "=" * 50)
        print("❌ Failed to add credits!") 