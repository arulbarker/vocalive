#!/usr/bin/env python3
"""
StreamMate AI - Supabase Migration Test Script
Test all Supabase functionality after migration
"""

import sys
import json
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from modules_client.supabase_client import SupabaseClient

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("🔗 Testing Supabase connection...")
    
    try:
        supabase = SupabaseClient()
        health = supabase.health_check()
        
        if health.get("status") == "success":
            print("✅ Supabase connection successful")
            return True
        else:
            print(f"❌ Supabase connection failed: {health}")
            return False
            
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False

def test_user_creation():
    """Test user creation"""
    print("\n👤 Testing user creation...")
    
    try:
        supabase = SupabaseClient()
        
        # Test user creation
        result = supabase.create_user("test@streammate.ai", "Test User")
        
        if result.get("status") == "success":
            print("✅ User creation successful")
            return True
        else:
            print(f"❌ User creation failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ User creation error: {e}")
        return False

def test_credit_operations():
    """Test credit operations"""
    print("\n💰 Testing credit operations...")
    
    try:
        supabase = SupabaseClient()
        email = "test@streammate.ai"
        
        # Test adding credits
        add_result = supabase.add_credits(email, 1000, "wallet", description="Test top-up")
        
        if add_result.get("status") == "success":
            print("✅ Credit addition successful")
        else:
            print(f"❌ Credit addition failed: {add_result}")
            return False
        
        # Test getting credit balance
        balance_result = supabase.get_credit_balance(email)
        
        if balance_result.get("status") == "success":
            data = balance_result.get("data", {})
            wallet_balance = data.get("wallet_balance", 0)
            print(f"✅ Credit balance retrieved: {wallet_balance}")
        else:
            print(f"❌ Credit balance retrieval failed: {balance_result}")
            return False
        
        # Test deducting credits
        deduct_result = supabase.deduct_credits(email, 100, "wallet", component="test")
        
        if deduct_result.get("status") == "success":
            print("✅ Credit deduction successful")
        else:
            print(f"❌ Credit deduction failed: {deduct_result}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Credit operations error: {e}")
        return False

def test_mode_purchase():
    """Test mode purchase functionality"""
    print("\n🛒 Testing mode purchase...")
    
    try:
        supabase = SupabaseClient()
        email = "test@streammate.ai"
        
        # Add more credits to wallet for testing
        supabase.add_credits(email, 50000, "wallet", description="Test credits for purchase")
        
        # Test basic mode purchase
        purchase_result = supabase.purchase_mode_credits(email, "basic", 10000)
        
        if purchase_result.get("status") == "success":
            print("✅ Basic mode purchase successful")
        else:
            print(f"❌ Basic mode purchase failed: {purchase_result}")
            return False
        
        # Test pro mode purchase
        purchase_result = supabase.purchase_mode_credits(email, "pro", 20000)
        
        if purchase_result.get("status") == "success":
            print("✅ Pro mode purchase successful")
        else:
            print(f"❌ Pro mode purchase failed: {purchase_result}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Mode purchase error: {e}")
        return False

def test_license_validation():
    """Test license validation"""
    print("\n🔐 Testing license validation...")
    
    try:
        supabase = SupabaseClient()
        email = "test@streammate.ai"
        
        # Test license validation
        license_result = supabase.validate_license(email)
        
        if license_result:
            print("✅ License validation successful")
            print(f"   - Valid: {license_result.get('is_valid')}")
            print(f"   - Tier: {license_result.get('tier')}")
            print(f"   - Credits: {license_result.get('hours_credit')}")
            return True
        else:
            print("❌ License validation failed")
            return False
            
    except Exception as e:
        print(f"❌ License validation error: {e}")
        return False

def test_transaction_history():
    """Test transaction history"""
    print("\n📊 Testing transaction history...")
    
    try:
        supabase = SupabaseClient()
        email = "test@streammate.ai"
        
        # Get transaction history
        history = supabase.get_transaction_history(email, limit=10)
        
        if history:
            print(f"✅ Transaction history retrieved: {len(history)} transactions")
            return True
        else:
            print("❌ Transaction history retrieval failed")
            return False
            
    except Exception as e:
        print(f"❌ Transaction history error: {e}")
        return False

def test_payment_transaction():
    """Test payment transaction creation"""
    print("\n💳 Testing payment transaction...")
    
    try:
        supabase = SupabaseClient()
        email = "test@streammate.ai"
        
        # Create payment transaction
        payment_result = supabase.create_payment_transaction(email, "basic", 100000)
        
        if payment_result.get("status") == "success":
            print("✅ Payment transaction created successfully")
            return True
        else:
            print(f"❌ Payment transaction failed: {payment_result}")
            return False
            
    except Exception as e:
        print(f"❌ Payment transaction error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 StreamMate AI - Supabase Migration Test")
    print("=" * 50)
    
    tests = [
        ("Supabase Connection", test_supabase_connection),
        ("User Creation", test_user_creation),
        ("Credit Operations", test_credit_operations),
        ("Mode Purchase", test_mode_purchase),
        ("License Validation", test_license_validation),
        ("Transaction History", test_transaction_history),
        ("Payment Transaction", test_payment_transaction),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Supabase migration is successful!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 