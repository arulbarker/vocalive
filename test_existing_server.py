#!/usr/bin/env python3
"""
Test Script untuk Server yang Sudah Ada
"""

import requests
import time

# Configuration
SERVER_URL = "http://69.62.79.238:8000"
CALLBACK_URL = f"{SERVER_URL}/api/payment/callback"
TEST_EMAIL = "test@example.com"

def test_server_health():
    """Test server health"""
    print("🧪 Testing Server Health...")
    
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=10)
        print(f"✅ Health Status: {response.status_code}")
        print(f"✅ Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
        else:
            print("❌ Server is not responding properly")
            return False
            
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def test_callback():
    """Test callback endpoint"""
    print("\n🧪 Testing Callback Endpoint...")
    
    # Data payment berhasil
    payment_data = {
        "trx_id": "12345",
        "sid": "test-sid",
        "reference_id": f"{TEST_EMAIL}_{int(time.time())}",
        "status": "berhasil",
        "status_code": "1",
        "amount": "50000",
        "total": "52500",
        "paid_off": "50000",
        "via": "va",
        "channel": "bag",
        "buyer_email": TEST_EMAIL,
        "buyer_name": "Test User"
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
            print("✅ Callback endpoint working!")
            return True
        else:
            print(f"❌ Callback endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing callback: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Existing Server...")
    print(f"📍 Server URL: {SERVER_URL}")
    print(f"📍 Callback URL: {CALLBACK_URL}")
    print("=" * 50)
    
    # Test server health
    server_ok = test_server_health()
    
    if server_ok:
        # Test callback
        callback_ok = test_callback()
        
        if callback_ok:
            print("\n✅ SUCCESS: Server callback is working!")
            print("📋 Next Steps:")
            print("1. Update iPaymu dashboard with callback URL")
            print("2. Test with real payment")
        else:
            print("\n❌ Callback endpoint not working")
    else:
        print("\n❌ Server not accessible")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    main() 