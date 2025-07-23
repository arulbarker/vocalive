#!/usr/bin/env python3
"""
Test Script untuk iPaymu Callback
Menguji Edge Function callback dengan data real dari iPaymu
"""

import requests
import json
import time
from datetime import datetime

# Configuration
CALLBACK_URL = "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/ipaymu-callback"
TEST_EMAIL = "test@example.com"

def test_successful_payment():
    """Test payment berhasil"""
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
        "paid_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
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
        else:
            print(f"❌ Payment callback failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing payment: {e}")

def test_failed_payment():
    """Test payment gagal"""
    print("\n🧪 Testing Failed Payment...")
    
    payment_data = {
        "trx_id": "172798",
        "sid": "8f978c25-cf34-4aca-9597-15571d8249ec",
        "reference_id": f"{TEST_EMAIL}_{int(time.time())}",
        "status": "gagal",
        "status_code": "0",
        "sub_total": "50000",
        "total": "52500",
        "amount": "52500",
        "fee": "6000",
        "paid_off": "0",
        "created_at": "2025-07-23 09:04:42",
        "expired_at": "2025-07-24 09:04:42",
        "paid_at": "",
        "settlement_status": "failed",
        "transaction_status_code": "0",
        "is_escrow": "false",
        "system_notes": "Payment failed",
        "via": "va",
        "channel": "bag",
        "payment_no": "",
        "buyer_name": "Test User",
        "buyer_email": TEST_EMAIL,
        "buyer_phone": "08123456789",
        "additional_info": "[]",
        "url": CALLBACK_URL,
        "va": ""
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
            print("✅ Failed payment handled correctly!")
        else:
            print(f"❌ Failed payment test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing failed payment: {e}")

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
        print(f"✅ CORS Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ CORS preflight successful!")
        else:
            print(f"❌ CORS preflight failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing CORS: {e}")

def test_invalid_data():
    """Test dengan data tidak valid"""
    print("\n🧪 Testing Invalid Data...")
    
    invalid_data = {
        "trx_id": "invalid",
        "status": "unknown",
        "reference_id": "invalid_reference"
    }
    
    try:
        response = requests.post(
            CALLBACK_URL,
            data=invalid_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            },
            timeout=30
        )
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"✅ Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Invalid data handled correctly!")
        else:
            print(f"❌ Invalid data test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing invalid data: {e}")

def main():
    """Run semua test"""
    print("🚀 Starting iPaymu Callback Tests...")
    print(f"📍 Callback URL: {CALLBACK_URL}")
    print(f"📧 Test Email: {TEST_EMAIL}")
    print("=" * 50)
    
    # Run tests
    test_cors_preflight()
    test_successful_payment()
    test_failed_payment()
    test_invalid_data()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("\n📋 Next Steps:")
    print("1. Check Supabase logs: supabase functions logs ipaymu-callback")
    print("2. Verify database updates")
    print("3. Test with real iPaymu payment")

if __name__ == "__main__":
    main() 