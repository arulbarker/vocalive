import requests
import json

# Test sandbox callback data
test_data = {
    "trx_id": "SANDBOX123456789",
    "sid": "S1234567890",
    "reference_id": "mursalinasrul@gmail.com_1234567890",
    "status": "berhasil",
    "status_code": "1",
    "sub_total": "5000",
    "total": "5000",
    "amount": "5000",
    "fee": "0",
    "paid_off": "5000",
    "created_at": "2025-07-23 15:00:00",
    "expired_at": "2025-07-24 15:00:00",
    "paid_at": "2025-07-23 15:05:00",
    "settlement_status": "settlement",
    "transaction_status_code": "1",
    "is_escrow": "0",
    "system_notes": "Sandbox payment successful",
    "via": "va",
    "channel": "bca",
    "payment_no": "SANDBOX123456",
    "buyer_name": "Mursalin Asrul",
    "buyer_email": "mursalinasrul@gmail.com",
    "buyer_phone": "081234567890",
    "additional_info": "",
    "url": "https://streammate-callback.onrender.com/payment-completed",
    "va": "SANDBOX123456"
}

# Test callback endpoint
url = "https://streammate-callback.onrender.com/ipaymu-callback"

print("🧪 Testing iPaymu Sandbox Callback...")
print(f"URL: {url}")
print(f"User: mursalinasrul@gmail.com")
print(f"Environment: SANDBOX")
print(f"Data: {json.dumps(test_data, indent=2)}")

try:
    response = requests.post(url, json=test_data, headers={
        'Content-Type': 'application/json'
    })
    
    print(f"\n📊 Response Status: {response.status_code}")
    print(f"📊 Response Headers: {dict(response.headers)}")
    print(f"📊 Response Body: {response.text}")
    
    if response.status_code == 200:
        print("✅ Sandbox callback test SUCCESS!")
        print("💳 Credits should be added to user account")
        print("📊 Check Supabase database for payment record")
    else:
        print("❌ Sandbox callback test FAILED!")
        
except Exception as e:
    print(f"❌ Error testing sandbox callback: {e}")

print("\n🔍 Check Render logs for detailed processing info...")
print("📊 Check Supabase database for user credits update...") 