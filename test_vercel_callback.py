#!/usr/bin/env python3
"""
Test Script untuk Vercel API Routes
Test callback dan payment completion
"""

import requests
import time

# Configuration - Ganti dengan URL Vercel Anda
VERCEL_BASE_URL = "https://your-app.vercel.app"  # Ganti dengan URL Vercel Anda
CALLBACK_URL = f"{VERCEL_BASE_URL}/api/ipaymu-callback"
COMPLETED_URL = f"{VERCEL_BASE_URL}/api/payment-completed"
TEST_EMAIL = "test@example.com"

def test_callback_function():
    """Test iPaymu callback function"""
    print("🧪 Testing Vercel Callback Function...")
    
    # Data payment berhasil
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
            print("✅ Callback function working correctly!")
            return payment_data["reference_id"]
        else:
            print(f"❌ Callback function failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing callback: {e}")
        return None

def test_payment_completed_page(order_id):
    """Test payment completed page"""
    if not order_id:
        print("❌ No order ID to test")
        return
    
    print(f"\n🧪 Testing Payment Completed Page...")
    print(f"📍 Order ID: {order_id}")
    
    try:
        response = requests.get(
            f"{COMPLETED_URL}?order_id={order_id}",
            headers={"Accept": "text/html"},
            timeout=30
        )
        
        print(f"✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Payment completed page working!")
            print("✅ HTML page generated successfully")
        else:
            print(f"❌ Payment completed page failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing payment completed page: {e}")

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
    """Run all tests"""
    print("🚀 Starting Vercel API Routes Tests...")
    print(f"📍 Base URL: {VERCEL_BASE_URL}")
    print(f"📧 Test Email: {TEST_EMAIL}")
    print("=" * 50)
    
    # Test CORS
    test_cors_preflight()
    
    # Test callback function
    order_id = test_callback_function()
    
    # Test payment completed page
    test_payment_completed_page(order_id)
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("\n📋 Next Steps:")
    print("1. Update VERCEL_BASE_URL with your actual Vercel URL")
    print("2. Set environment variables in Vercel dashboard")
    print("3. Update iPaymu callback URLs")
    print("4. Test with real payment")

if __name__ == "__main__":
    main() 