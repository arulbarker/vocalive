#!/usr/bin/env python3
"""
Test Credit Wallet System - Validasi sistem kredit yang dipisah
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from modules_server.credit_wallet import get_credit_wallet
from modules_client.credit_wallet_client import (
    get_credit_wallet_client, get_credit_packages,
    get_current_balance, format_current_balance
)



def test_credit_packages():
    """Test credit packages for top-up"""
    print("=== TESTING CREDIT TOP-UP PACKAGES ===")
    
    packages = get_credit_packages()
    print(f"Available top-up packages: {len(packages)}")
    
    for pkg in packages:
        print(f"\n📦 {pkg['name']}")
        print(f"   💵 Price: Rp {pkg['price_idr']:,}")
        print(f"   💰 Credits: {pkg['credits']:,}")
        print(f"   🎁 Bonus: {pkg['bonus']:,}")
        print(f"   📊 Total: {pkg['total_credits']:,}")
        print(f"   📝 Description: {pkg['description']}")
        print(f"   🔥 Popular: {pkg['popular']}")

def test_current_balance():
    """Test current balance check"""
    print("\n=== TESTING CURRENT BALANCE ===")
    
    try:
        balance = get_current_balance()
        formatted = format_current_balance()
        print(f"Current balance: {balance} credits")
        print(f"Formatted: {formatted} credits")
    except Exception as e:
        print(f"Error getting balance: {e}")

def test_package_purchase_validation():
    """Test validation for package purchases"""
    print("\n=== TESTING PACKAGE PURCHASE VALIDATION ===")
    
    subscription_file = Path("config/subscription_status.json")
    
    if subscription_file.exists():
        with open(subscription_file, 'r', encoding='utf-8') as f:
            sub_data = json.load(f)
        
        print("Current subscription status:")
        basic_active = sub_data.get("basic", {}).get("active", False)
        cohost_active = sub_data.get("cohost_seller", {}).get("active", False)
        
        print(f"  Basic Package: {'✅ ACTIVE' if basic_active else '❌ NOT PURCHASED'}")
        print(f"  CoHost Seller: {'✅ ACTIVE' if cohost_active else '❌ NOT PURCHASED'}")
        
        if basic_active:
            basic_data = sub_data.get("basic", {})
            print(f"    Purchased at: {basic_data.get('purchased_at', 'N/A')}")
            print(f"    Email: {basic_data.get('email', 'N/A')}")
        
        if cohost_active:
            cohost_data = sub_data.get("cohost_seller", {})
            print(f"    Purchased at: {cohost_data.get('purchased_at', 'N/A')}")
            print(f"    Email: {cohost_data.get('email', 'N/A')}")
            print(f"    Product slots: {cohost_data.get('purchased_slots', 'N/A')}")
    else:
        print("❌ No subscription file found - no packages purchased")

def test_credit_requirements():
    """Test credit requirements for packages"""
    print("\n=== TESTING CREDIT REQUIREMENTS ===")
    
    try:
        balance = get_current_balance()
        
        print(f"Current balance: {balance:,} credits")
        print("\nPackage requirements:")
        print(f"  Basic Package: 100,000 credits {'✅ Can afford' if balance >= 100000 else '❌ Insufficient'}")
        print(f"  CoHost Seller: 300,000 credits {'✅ Can afford' if balance >= 300000 else '❌ Insufficient'}")
        
        if balance < 100000:
            needed = 100000 - balance
            print(f"\nNeed {needed:,} more credits for Basic package")
            
        if balance < 300000:
            needed = 300000 - balance
            print(f"Need {needed:,} more credits for CoHost Seller package")
            
    except Exception as e:
        print(f"Error checking requirements: {e}")

def test_wallet_client():
    """Test credit wallet client"""
    print("\n=== TESTING CREDIT WALLET CLIENT ===")
    
    try:
        client = get_credit_wallet_client()
        print(f"Wallet client initialized:")
        print(f"  User ID: {client.user_id}")
        print(f"  Local mode: {client.local_mode}")
        
        # Test balance check
        balance = client.get_balance()
        print(f"  Current balance: {balance:,} credits")
        
        # Test wallet info
        wallet_info = client.get_wallet_info()
        if wallet_info:
            print(f"  Total top-up: {wallet_info['total_topup']:,}")
            print(f"  Total spent: {wallet_info['total_spent']:,}")
            print(f"  Created: {wallet_info['created_at']}")
            print(f"  Updated: {wallet_info['updated_at']}")
        
    except Exception as e:
        print(f"Error testing wallet client: {e}")

def main():
    """Run all tests"""
    print("🧪 TESTING STREAMMATE CREDIT SYSTEM 🧪")
    print("=" * 50)
    
    test_credit_packages()
    test_current_balance()
    test_package_purchase_validation()
    test_credit_requirements()
    test_wallet_client()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("\n💡 SYSTEM SUMMARY:")
    print("1. Credit Wallet Tab → For top-up credits with money")
    print("2. Subscription Tab → For buying packages with credits")
    print("3. Features only activate when packages are purchased")
    print("4. No features activate just by having credits")

if __name__ == "__main__":
    sys.exit(main()) 