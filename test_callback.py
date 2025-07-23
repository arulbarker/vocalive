#!/usr/bin/env python3
"""
Test Script untuk Callback iPaymu
Menguji Edge Function callback dengan berbagai skenario
"""

import requests
import json
import time
from datetime import datetime

def test_callback_success():
    """Test callback dengan payment berhasil"""
    print("🔧 Testing Callback - Payment Success")
    
    url = "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/callback"
    
    # Data payment berhasil
    data = {
        "trx_id": "172797",
        "sid": "7f978c25-cf34-4aca-9597-15571d8249ec",
        "reference_id": "mursalinasrul@gmail.com_1753236264",
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
        "system_notes": "Sandbox notify",
        "via": "va",
        "channel": "bag",
        "payment_no": "000039325851",
        "buyer_name": "dsad",
        "buyer_email": "mursalinasrul@gmail.com",
        "buyer_phone": "dasd",
        "additional_info": "[]",
        "url": "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/callback",
        "va": "000039325851"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        print(f"📡 Sending request to: {url}")
        print(f"📦 Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, data=data, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Callback processed successfully!")
            try:
                result = response.json()
                print(f"📈 Result: {json.dumps(result, indent=2)}")
            except:
                print("⚠️ Response is not JSON format")
        else:
            print(f"❌ ERROR: Callback failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

def test_callback_failed():
    """Test callback dengan payment gagal"""
    print("\n🔧 Testing Callback - Payment Failed")
    
    url = "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/callback"
    
    # Data payment gagal
    data = {
        "trx_id": "172798",
        "sid": "test-session-failed",
        "reference_id": "mursalinasrul@gmail.com_1753236265",
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
        "buyer_name": "test",
        "buyer_email": "mursalinasrul@gmail.com",
        "buyer_phone": "test",
        "additional_info": "[]",
        "url": "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/callback",
        "va": ""
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        print(f"📡 Sending request to: {url}")
        print(f"📦 Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, data=data, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Failed payment callback processed!")
            try:
                result = response.json()
                print(f"📈 Result: {json.dumps(result, indent=2)}")
            except:
                print("⚠️ Response is not JSON format")
        else:
            print(f"❌ ERROR: Callback failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

def test_callback_with_auth():
    """Test callback dengan authorization header"""
    print("\n🔧 Testing Callback - With Authorization Header")
    
    url = "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/callback"
    
    # Data payment berhasil
    data = {
        "trx_id": "172799",
        "sid": "test-session-auth",
        "reference_id": "mursalinasrul@gmail.com_1753236266",
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
        "system_notes": "Sandbox notify",
        "via": "va",
        "channel": "bag",
        "payment_no": "000039325852",
        "buyer_name": "test-auth",
        "buyer_email": "mursalinasrul@gmail.com",
        "buyer_phone": "test-auth",
        "additional_info": "[]",
        "url": "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/callback",
        "va": "000039325852"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Authorization": "Bearer test-token"
    }
    
    try:
        print(f"📡 Sending request to: {url}")
        print(f"📦 Data: {json.dumps(data, indent=2)}")
        print(f"🔑 Headers: {json.dumps(headers, indent=2)}")
        
        response = requests.post(url, data=data, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Callback with auth processed successfully!")
            try:
                result = response.json()
                print(f"📈 Result: {json.dumps(result, indent=2)}")
            except:
                print("⚠️ Response is not JSON format")
        else:
            print(f"❌ ERROR: Callback failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

def test_edge_function_health():
    """Test health check Edge Function"""
    print("\n🔧 Testing Edge Function Health Check")
    
    url = "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/callback"
    
    headers = {
        "Accept": "application/json"
    }
    
    try:
        print(f"📡 Sending OPTIONS request to: {url}")
        
        response = requests.options(url, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Edge Function is healthy!")
        else:
            print(f"❌ ERROR: Edge Function health check failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

def main():
    """Main test function"""
    print("🚀 StreamMate AI - Callback Test Script")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now()}")
    print("=" * 50)
    
    # Test 1: Health check
    test_edge_function_health()
    
    # Test 2: Success callback
    test_callback_success()
    
    # Test 3: Failed callback
    test_callback_failed()
    
    # Test 4: Callback with auth header
    test_callback_with_auth()
    
    print("\n" + "=" * 50)
    print("🏁 All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    main() 