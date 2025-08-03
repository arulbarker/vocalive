#!/usr/bin/env python3
"""
Script untuk menambahkan Pro credits secara manual untuk testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules_client.supabase_client import SupabaseClient
from modules_client.config_manager import ConfigManager

def add_pro_credits():
    """Menambahkan Pro credits untuk user yang sedang login"""
    try:
        # Get user email
        cfg = ConfigManager()
        email = cfg.get("user_data", {}).get("email", "")
        
        if not email:
            print("❌ No user logged in. Please login first.")
            return
        
        print(f"🔍 Adding Pro credits for user: {email}")
        
        # Initialize Supabase client
        supabase = SupabaseClient()
        
        # Add 100,000 Pro credits
        result = supabase.add_specific_credits(
            email=email,
            credit_type="pro_credits",
            amount=100000,
            description="Manual Pro credits addition for testing"
        )
        
        if result.get("status") == "success":
            print("✅ Successfully added 100,000 Pro credits!")
            print(f"📧 Email: {email}")
            print(f"💰 Amount: 100,000 Pro credits")
            print(f"📝 Description: Manual Pro credits addition for testing")
            
            # Also check current balance
            balance_data = supabase.get_credit_balance(email)
            if balance_data.get("status") == "success":
                data = balance_data.get("data", {})
                print(f"\n📊 Current balances:")
                print(f"💳 Wallet Balance: {data.get('wallet_balance', 0):,}")
                print(f"🔵 Basic Credits: {data.get('basic_credits', 0):,}")
                print(f"🟠 Pro Credits: {data.get('pro_credits', 0):,}")
        else:
            print(f"❌ Failed to add Pro credits: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Adding Pro Credits for Testing")
    print("=" * 50)
    add_pro_credits()
    print("=" * 50)
    print("✨ Done!")