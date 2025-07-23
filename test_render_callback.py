#!/usr/bin/env python3
"""
Test Render Callback
"""

import requests
import time

# Configuration
RENDER_URL = "https://streammate-callback.onrender.com"
CALLBACK_URL = f"{RENDER_URL}/ipaymu-callback"
HEALTH_URL = f"{RENDER_URL}/health"

def test_health():
    """Test health endpoint"""
    print("🧪 Testing Health Endpoint...")
    
    try:
        response = requests.get(HEALTH_URL, timeout=10)
        print(f"✅ Health Status: {response.status_code}")
        print(f"✅ Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Render service is running!")
            return True
        else:
            print("❌ Render service not responding properly")
            return False
            
    except Exception as e:
        print(f"❌ Error testing health: {e}")
        return False

def test_callback():
    """Test callback endpoint"""
    print("\n🧪 Testing Callback Endpoint...")
    
    # Data payment berhasil
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
        "paid_at": "2025-01-23 06:30:00"
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
    print("🚀 Testing Render Callback...")
    print(f"📍 Render URL: {RENDER_URL}")
    print(f"📍 Callback URL: {CALLBACK_URL}")
    print("=" * 50)
    
    # Test health first
    health_ok = test_health()
    
    if health_ok:
        # Test callback
        callback_ok = test_callback()
        
        if callback_ok:
            print("\n✅ SUCCESS: Render callback is working!")
            print("📋 Next Steps:")
            print("1. Update iPaymu dashboard with callback URL")
            print("2. Test with real payment")
        else:
            print("\n❌ Callback not working")
    else:
        print("\n❌ Render service not accessible")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    main() 