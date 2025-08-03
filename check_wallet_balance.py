#!/usr/bin/env python3
"""
Script untuk cek balance kredit di dompet secara real-time
"""

import requests
import json
from datetime import datetime

# Supabase configuration
SUPABASE_URL = "https://nivwxqojwljihoybzgkc.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzE3NDY0NywiZXhwIjoyMDY4NzUwNjQ3fQ.r3sftfPQsHkWjK-xQhosh1IS7PSMi5tn4qtsxa5I9CY"

headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

def check_wallet_balance():
    """Cek balance kredit di dompet"""
    print("🔍 Checking Wallet Balance...")
    print("=" * 50)
    
    try:
        email = "mursalinasrul@gmail.com"
        
        # Get user data from Supabase
        url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
        response = requests.get(url, headers=headers)
        
        print(f"📊 Status: {response.status_code}")
        
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
                
                # Format balance dengan pemisah ribuan
                formatted_credits = f"{credits:,}"
                print(f"\n💳 WALLET BALANCE: {formatted_credits} credits")
                
                # Konversi ke IDR (1 credit = 1 IDR)
                idr_amount = credits
                formatted_idr = f"Rp {idr_amount:,}"
                print(f"💵 IDR Value: {formatted_idr}")
                
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

def check_transaction_history():
    """Cek riwayat transaksi"""
    print("\n📋 Transaction History...")
    print("=" * 50)
    
    try:
        # Check if payments table exists and has data
        payments_url = f"{SUPABASE_URL}/rest/v1/payments"
        response = requests.get(payments_url, headers=headers)
        
        if response.status_code == 200:
            payments = response.json()
            print(f"📊 Found {len(payments)} payment records:")
            
            for payment in payments:
                amount = payment.get("amount", 0)
                credits_added = payment.get("credits_added", 0)
                status = payment.get("status", "unknown")
                created_at = payment.get("created_at", "N/A")
                
                print(f"  💰 Amount: Rp {amount:,} | Credits: {credits_added:,} | Status: {status} | Date: {created_at}")
        else:
            print("ℹ️ No payment history found or table doesn't exist")
            
    except Exception as e:
        print(f"❌ Error checking transaction history: {e}")

def check_user_profiles_structure():
    """Cek struktur table user_profiles"""
    print("\n🏗️ Database Structure...")
    print("=" * 50)
    
    try:
        # Get all users to see structure
        url = f"{SUPABASE_URL}/rest/v1/user_profiles"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            users = response.json()
            print(f"📊 Found {len(users)} users in database:")
            
            for user in users:
                email = user.get("email", "N/A")
                credits = user.get("credits", 0)
                created_at = user.get("created_at", "N/A")
                updated_at = user.get("updated_at", "N/A")
                
                print(f"  👤 {email}: {credits:,} credits")
                print(f"     Created: {created_at}")
                print(f"     Updated: {updated_at}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking structure: {e}")

if __name__ == "__main__":
    print("🔍 WALLET BALANCE VERIFICATION")
    print("=" * 50)
    
    # Check current balance
    current_balance = check_wallet_balance()
    
    # Check transaction history
    check_transaction_history()
    
    # Check database structure
    check_user_profiles_structure()
    
    print("\n" + "=" * 50)
    print("✅ Balance verification completed!")
    
    if current_balance > 0:
        print(f"🎉 Your wallet has {current_balance:,} credits!")
    else:
        print("⚠️ Your wallet is empty!") 