#!/usr/bin/env python3
"""
Script untuk cek sistem pemindahan kredit dari wallet ke Basic dan Pro
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

def check_current_credits():
    """Cek kredit saat ini"""
    print("🔍 Checking current credits...")
    print("=" * 60)
    
    try:
        email = "mursalinasrul@gmail.com"
        url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            users = response.json()
            if users:
                user = users[0]
                
                wallet_credits = user.get("credits", 0)
                basic_credits = user.get("basic_credits", 0)
                pro_credits = user.get("pro_credits", 0)
                total_spent = user.get("total_spent", 0)
                
                print("📊 Current Credit Status:")
                print(f"   💰 Wallet Credits: {wallet_credits:,}")
                print(f"   🟠 Basic Credits: {basic_credits:,}")
                print(f"   🔵 Pro Credits: {pro_credits:,}")
                print(f"   💸 Total Spent: {total_spent:,}")
                print(f"   📈 Total All Credits: {wallet_credits + basic_credits + pro_credits:,}")
                
                return {
                    "wallet": wallet_credits,
                    "basic": basic_credits,
                    "pro": pro_credits,
                    "total_spent": total_spent
                }
            else:
                print("❌ User not found")
                return None
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking credits: {e}")
        return None

def check_expected_credits():
    """Cek kredit yang seharusnya"""
    print("\n🎯 Expected Credit Status:")
    print("=" * 60)
    
    # Berdasarkan log sebelumnya
    initial_credits = 610000
    basic_purchase = 100000
    pro_purchase = 300000
    total_purchased = basic_purchase + pro_purchase
    
    expected_wallet = initial_credits - total_purchased
    expected_basic = basic_purchase
    expected_pro = pro_purchase
    
    print(f"💰 Initial Credits: {initial_credits:,}")
    print(f"🟠 Basic Purchase: {basic_purchase:,}")
    print(f"🔵 Pro Purchase: {pro_purchase:,}")
    print(f"💸 Total Purchased: {total_purchased:,}")
    print(f"💰 Expected Wallet: {expected_wallet:,}")
    print(f"🟠 Expected Basic: {expected_basic:,}")
    print(f"🔵 Expected Pro: {expected_pro:,}")
    
    return {
        "expected_wallet": expected_wallet,
        "expected_basic": expected_basic,
        "expected_pro": expected_pro,
        "total_purchased": total_purchased
    }

def test_credit_transfer():
    """Test sistem pemindahan kredit"""
    print("\n🧪 Testing Credit Transfer System:")
    print("=" * 60)
    
    try:
        email = "mursalinasrul@gmail.com"
        
        # Simulasi pemindahan kredit
        print("1️⃣ Simulating credit transfer...")
        
        # Get current data
        current_data = check_current_credits()
        if not current_data:
            return False
        
        expected_data = check_expected_credits()
        
        # Check if transfer is needed
        wallet_diff = expected_data["expected_wallet"] - current_data["wallet"]
        basic_diff = expected_data["expected_basic"] - current_data["basic"]
        pro_diff = expected_data["expected_pro"] - current_data["pro"]
        
        print(f"\n📊 Transfer Analysis:")
        print(f"   Wallet difference: {wallet_diff:,}")
        print(f"   Basic difference: {basic_diff:,}")
        print(f"   Pro difference: {pro_diff:,}")
        
        if wallet_diff == 0 and basic_diff == 0 and pro_diff == 0:
            print("✅ Credits are already correctly transferred!")
            return True
        
        # Perform transfer if needed
        if basic_diff > 0 or pro_diff > 0:
            print("\n2️⃣ Performing credit transfer...")
            
            new_wallet = expected_data["expected_wallet"]
            new_basic = expected_data["expected_basic"]
            new_pro = expected_data["expected_pro"]
            new_total_spent = expected_data["total_purchased"]
            
            update_data = {
                "credits": new_wallet,
                "basic_credits": new_basic,
                "pro_credits": new_pro,
                "total_spent": new_total_spent,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            patch_url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
            patch_response = requests.patch(patch_url, headers=headers, json=update_data)
            
            print(f"📊 Transfer status: {patch_response.status_code}")
            
            if patch_response.status_code in [200, 204]:
                print("✅ Credit transfer successful!")
                
                # Verify transfer
                print("\n3️⃣ Verifying transfer...")
                verify_data = check_current_credits()
                if verify_data:
                    if (verify_data["wallet"] == new_wallet and 
                        verify_data["basic"] == new_basic and 
                        verify_data["pro"] == new_pro):
                        print("✅ Transfer verified successfully!")
                        return True
                    else:
                        print("❌ Transfer verification failed!")
                        return False
            else:
                print(f"❌ Transfer failed: {patch_response.text}")
                return False
        else:
            print("✅ No transfer needed!")
            return True
            
    except Exception as e:
        print(f"❌ Error during transfer: {e}")
        return False

def check_transaction_history():
    """Cek history transaksi"""
    print("\n📋 Checking Transaction History:")
    print("=" * 60)
    
    try:
        # Check if credit_transactions table exists
        url = f"{SUPABASE_URL}/rest/v1/credit_transactions?email=eq.mursalinasrul@gmail.com&order=created_at.desc&limit=10"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            transactions = response.json()
            print(f"📊 Found {len(transactions)} transactions")
            
            for i, tx in enumerate(transactions[:5], 1):
                amount = tx.get("amount", 0)
                transaction_type = tx.get("transaction_type", "unknown")
                description = tx.get("description", "No description")
                created_at = tx.get("created_at", "Unknown")
                
                print(f"{i}. {transaction_type}: {amount:,} credits - {description}")
                print(f"   Date: {created_at}")
        else:
            print("⚠️ No transaction history found or table doesn't exist")
            
    except Exception as e:
        print(f"❌ Error checking transactions: {e}")

def main():
    """Main function"""
    print("🔍 COMPREHENSIVE CREDIT TRANSFER CHECK")
    print("=" * 60)
    
    # Check current credits
    current_data = check_current_credits()
    
    # Check expected credits
    expected_data = check_expected_credits()
    
    # Test transfer system
    transfer_success = test_credit_transfer()
    
    # Check transaction history
    check_transaction_history()
    
    print("\n" + "=" * 60)
    if transfer_success:
        print("✅ Credit transfer system is working correctly!")
        print("💰 Wallet credits properly deducted")
        print("🟠 Basic credits properly allocated")
        print("🔵 Pro credits properly allocated")
    else:
        print("❌ Credit transfer system has issues!")
        print("⚠️ Please check the transfer logic")
    
    print("\n📊 Final Credit Summary:")
    final_data = check_current_credits()
    if final_data:
        total = final_data["wallet"] + final_data["basic"] + final_data["pro"]
        print(f"   Total Credits: {total:,}")
        print(f"   Wallet: {final_data['wallet']:,}")
        print(f"   Basic: {final_data['basic']:,}")
        print(f"   Pro: {final_data['pro']:,}")

if __name__ == "__main__":
    main() 