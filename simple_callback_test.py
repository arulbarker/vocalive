#!/usr/bin/env python3
"""
Simple Callback Test - Works with existing server
"""

import requests
import time

# Configuration
SERVER_URL = "http://69.62.79.238:8000"
CALLBACK_URL = f"{SERVER_URL}/api/payment/callback"

def test_simple_callback():
    """Test callback dengan data yang sesuai dengan server"""
    print("🧪 Testing Simple Callback...")
    
    # Data yang sesuai dengan server yang sudah ada
    payment_data = {
        "trx_id": f"TEST_{int(time.time())}",
        "reference_id": f"test@example.com_{int(time.time())}",
        "status": "berhasil",
        "status_code": "1",
        "amount": "50000",
        "total": "52500",
        "paid_off": "50000",
        "via": "va",
        "channel": "bag",
        "buyer_email": "test@example.com",
        "buyer_name": "Test User",
        "paid_at": "2025-01-23 06:15:00"
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
    """Run test"""
    print("🚀 Testing Simple Callback...")
    print(f"📍 Server URL: {SERVER_URL}")
    print(f"📍 Callback URL: {CALLBACK_URL}")
    print("=" * 50)
    
    # Test callback
    callback_ok = test_simple_callback()
    
    if callback_ok:
        print("\n✅ SUCCESS: Callback is working!")
        print("📋 Next Steps:")
        print("1. Update iPaymu dashboard with callback URL")
        print("2. Test with real payment")
    else:
        print("\n❌ Callback not working")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    main() 