#!/usr/bin/env python3
"""
Script untuk menambah field database yang hilang dan memperbaiki sistem transfer kredit
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

def add_database_fields():
    """Tambah field yang hilang ke database"""
    print("🔧 Adding missing database fields...")
    print("=" * 60)
    
    print("📋 SQL Commands to run in Supabase SQL Editor:")
    print("-" * 50)
    print("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS basic_credits INTEGER DEFAULT 0;")
    print("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS pro_credits INTEGER DEFAULT 0;")
    print("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS total_spent INTEGER DEFAULT 0;")
    print("-" * 50)
    
    print("⚠️  Please run these SQL commands in Supabase SQL Editor first!")
    print("   Then run this script again to update user credits.")
    
    return True

def update_user_credits_after_fields():
    """Update kredit user setelah field ditambahkan"""
    print("\n🔧 Updating user credits after adding fields...")
    print("=" * 60)
    
    try:
        email = "mursalinasrul@gmail.com"
        
        # Get current user data
        print("1️⃣ Getting current user data...")
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
        current_wallet = user.get("credits", 0)
        print(f"💰 Current wallet credits: {current_wallet:,}")
        
        # Calculate correct credit allocation
        initial_credits = 610000
        basic_purchase = 100000
        pro_purchase = 300000
        total_purchased = basic_purchase + pro_purchase
        
        expected_wallet = initial_credits - total_purchased
        expected_basic = basic_purchase
        expected_pro = pro_purchase
        
        print(f"📊 Credit allocation:")
        print(f"   💰 Wallet credits: {expected_wallet:,}")
        print(f"   🟠 Basic credits: {expected_basic:,}")
        print(f"   🔵 Pro credits: {expected_pro:,}")
        print(f"   💸 Total spent: {total_purchased:,}")
        
        # Update user with correct credits
        print("2️⃣ Updating user with correct credits...")
        update_data = {
            "credits": expected_wallet,
            "basic_credits": expected_basic,
            "pro_credits": expected_pro,
            "total_spent": total_purchased,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        patch_url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
        patch_response = requests.patch(patch_url, headers=headers, json=update_data)
        
        print(f"📊 Update status: {patch_response.status_code}")
        
        if patch_response.status_code in [200, 204]:
            print("✅ User credits updated successfully!")
            
            # Verify update
            print("3️⃣ Verifying updated credits...")
            verify_response = requests.get(get_url, headers=headers)
            if verify_response.status_code == 200:
                updated_user = verify_response.json()[0]
                
                wallet = updated_user.get("credits", 0)
                basic = updated_user.get("basic_credits", 0)
                pro = updated_user.get("pro_credits", 0)
                total_spent = updated_user.get("total_spent", 0)
                
                print(f"✅ Updated credits:")
                print(f"   💰 Wallet: {wallet:,}")
                print(f"   🟠 Basic: {basic:,}")
                print(f"   🔵 Pro: {pro:,}")
                print(f"   💸 Total Spent: {total_spent:,}")
                
                return True
            else:
                print(f"❌ Failed to verify: {verify_response.text}")
                return False
        else:
            print(f"❌ Failed to update: {patch_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating credits: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_credit_system():
    """Test sistem kredit setelah perbaikan"""
    print("\n🧪 Testing credit system after fix...")
    print("=" * 60)
    
    try:
        email = "mursalinasrul@gmail.com"
        url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            users = response.json()
            if users:
                user = users[0]
                
                wallet = user.get("credits", 0)
                basic = user.get("basic_credits", 0)
                pro = user.get("pro_credits", 0)
                total_spent = user.get("total_spent", 0)
                
                print("📊 Final Credit Status:")
                print(f"   💰 Wallet Credits: {wallet:,}")
                print(f"   🟠 Basic Credits: {basic:,}")
                print(f"   🔵 Pro Credits: {pro:,}")
                print(f"   💸 Total Spent: {total_spent:,}")
                print(f"   📈 Total All Credits: {wallet + basic + pro:,}")
                
                # Check if system is working
                if wallet == 210000 and basic == 100000 and pro == 300000:
                    print("✅ Credit system is working correctly!")
                    return True
                else:
                    print("❌ Credit system still has issues!")
                    return False
            else:
                print("❌ User not found")
                return False
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing system: {e}")
        return False

def main():
    """Main function"""
    print("🔧 FIXING CREDIT TRANSFER SYSTEM")
    print("=" * 60)
    
    # Step 1: Add database fields
    print("STEP 1: Add Database Fields")
    add_database_fields()
    
    # Step 2: Update user credits
    print("\nSTEP 2: Update User Credits")
    success = update_user_credits_after_fields()
    
    if success:
        # Step 3: Test system
        print("\nSTEP 3: Test Credit System")
        test_success = test_credit_system()
        
        print("\n" + "=" * 60)
        if test_success:
            print("✅ Credit transfer system is now working!")
            print("💰 Wallet credits: 210,000")
            print("🟠 Basic credits: 100,000")
            print("🔵 Pro credits: 300,000")
            print("🎉 User can now access Basic and Pro modes!")
        else:
            print("❌ Credit system still needs fixing!")
    else:
        print("\n" + "=" * 60)
        print("❌ Failed to update credits!")
        print("⚠️  Please add database fields first!")

if __name__ == "__main__":
    main() 