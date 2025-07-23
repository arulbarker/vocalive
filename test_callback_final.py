#!/usr/bin/env python3
"""
Final Test Script untuk iPaymu Callback
Test dengan data real dari iPaymu
"""

import requests
import time

# Configuration
CALLBACK_URL = "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/ipaymu-callback"
TEST_EMAIL = "test@example.com"

def test_successful_payment():
    """Test payment berhasil dengan data real"""
    print("🧪 Testing Successful Payment...")
    
    # Data payment berhasil (format real dari iPaymu)
    payment_data = {
        "trx_id": "172797",
        "sid": "7f978c25-cf34-4aca-9597-15571d8249ec",
        "reference_id": f"{TEST_EMAIL}_{int(time.time())}",
        "status": "berhasil",
        "status_code": "1",
        "sub_total": "50000",
        "total": "52500",
        "amount": "52500",
        "fee": "6000",
        "paid_off": "46500",
        "created_at": "2025-07-23 09:04:42",
        "expired_at": "2025-07-24 09:04:42",
        "paid_at": "2025-07-23T09:05:14+07:00",
        "settlement_status": "settled",
        "transaction_status_code": "1",
        "is_escrow": "false",
        "system_notes": "Test payment",
        "via": "va",
        "channel": "bag",
        "payment_no": "000039325851",
        "buyer_name": "Test User",
        "buyer_email": TEST_EMAIL,
        "buyer_phone": "08123456789",
        "additional_info": "[]",
        "url": CALLBACK_URL,
        "va": "000039325851"
    }
    
    try:
        response = requests.post(
            CALLBACK_URL,
            data=payment_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            },
            timeout=30
        )
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"✅ Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Payment callback processed successfully!")
            print("✅ Credits should be added to user account")
        else:
            print(f"❌ Payment callback failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing payment: {e}")

def test_cors_preflight():
    """Test CORS preflight request"""
    print("\n🧪 Testing CORS Preflight...")
    
    try:
        response = requests.options(
            CALLBACK_URL,
            headers={
                "Origin": "https://ipaymu.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=30
        )
        
        print(f"✅ CORS Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ CORS preflight successful!")
        else:
            print(f"❌ CORS preflight failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing CORS: {e}")

def main():
    """Run tests"""
    print("🚀 Starting Final iPaymu Callback Tests...")
    print(f"📍 Callback URL: {CALLBACK_URL}")
    print(f"📧 Test Email: {TEST_EMAIL}")
    print("=" * 50)
    
    # Run tests
    test_cors_preflight()
    test_successful_payment()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("\n📋 Next Steps:")
    print("1. Check Supabase logs for function execution")
    print("2. Verify credits added to user account")
    print("3. Test with real iPaymu payment")

if __name__ == "__main__":
    main() 