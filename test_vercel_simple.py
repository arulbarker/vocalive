#!/usr/bin/env python3
"""
Simple Test Script untuk Vercel Callback
"""

import requests
import time

# Configuration
CALLBACK_URL = "https://streammate-releases-c1toa4yo4-aruls-projects-b3d561fd.vercel.app/api/ipaymu-callback"
TEST_EMAIL = "test@example.com"

def test_callback():
    """Test callback function"""
    print("🧪 Testing Vercel Callback...")
    
    # Data payment berhasil
    payment_data = {
        "trx_id": "12345",
        "status": "berhasil",
        "status_code": "1",
        "reference_id": f"{TEST_EMAIL}_{int(time.time())}",
        "paid_off": "50000",
        "total": "52500",
        "via": "va",
        "channel": "bag"
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
            print("✅ Callback function working!")
        else:
            print(f"❌ Callback function failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_cors():
    """Test CORS"""
    print("\n🧪 Testing CORS...")
    
    try:
        response = requests.options(
            CALLBACK_URL,
            headers={
                "Origin": "https://ipaymu.com",
                "Access-Control-Request-Method": "POST"
            },
            timeout=30
        )
        
        print(f"✅ CORS Status: {response.status_code}")
        
    except Exception as e:
        print(f"❌ CORS Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Vercel Callback...")
    print(f"📍 URL: {CALLBACK_URL}")
    print("=" * 50)
    
    test_cors()
    test_callback()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!") 