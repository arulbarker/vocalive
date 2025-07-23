#!/usr/bin/env python3
"""
Test Script untuk iPaymu Webhook
Menguji Edge Function ipaymu-webhook dengan berbagai skenario
"""

import requests
import json
import time
from datetime import datetime

def test_webhook_success():
    """Test webhook dengan payment berhasil"""
    print("🔧 Testing iPaymu Webhook - Payment Success")
    
    url = "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/ipaymu-webhook"
    
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
        "url": "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/ipaymu-webhook",
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
            print("✅ SUCCESS: Webhook processed successfully!")
            try:
                result = response.json()
                print(f"📈 Result: {json.dumps(result, indent=2)}")
            except:
                print("⚠️ Response is not JSON format")
        else:
            print(f"❌ ERROR: Webhook failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

def test_webhook_health():
    """Test health check webhook"""
    print("\n🔧 Testing iPaymu Webhook Health Check")
    
    url = "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/ipaymu-webhook"
    
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
            print("✅ SUCCESS: Webhook is healthy!")
        else:
            print(f"❌ ERROR: Webhook health check failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

def test_webhook_json():
    """Test webhook dengan JSON data"""
    print("\n🔧 Testing iPaymu Webhook - JSON Data")
    
    url = "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/ipaymu-webhook"
    
    # Data payment berhasil dalam format JSON
    data = {
        "trx_id": "172800",
        "sid": "test-session-json",
        "reference_id": "mursalinasrul@gmail.com_1753236267",
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
        "payment_no": "000039325853",
        "buyer_name": "test-json",
        "buyer_email": "mursalinasrul@gmail.com",
        "buyer_phone": "test-json",
        "additional_info": "[]",
        "url": "https://nivwxqojwljihoybzgkc.supabase.co/functions/v1/ipaymu-webhook",
        "va": "000039325853"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print(f"📡 Sending JSON request to: {url}")
        print(f"📦 Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: JSON webhook processed successfully!")
            try:
                result = response.json()
                print(f"📈 Result: {json.dumps(result, indent=2)}")
            except:
                print("⚠️ Response is not JSON format")
        else:
            print(f"❌ ERROR: JSON webhook failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

def main():
    """Main test function"""
    print("🚀 StreamMate AI - iPaymu Webhook Test Script")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now()}")
    print("=" * 50)
    
    # Test 1: Health check
    test_webhook_health()
    
    # Test 2: Success webhook
    test_webhook_success()
    
    # Test 3: JSON webhook
    test_webhook_json()
    
    print("\n" + "=" * 50)
    print("🏁 All webhook tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    main() 