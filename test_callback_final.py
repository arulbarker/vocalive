#!/usr/bin/env python3
"""
Final Test Script untuk iPaymu Callback
Test dengan data real dari iPaymu
"""

import requests
import json

# Test callback dengan data yang sama seperti user
callback_data = {
    "trx_id": "172834",
    "sid": "7bbbb4c8-2b84-4712-8fa9-c9dbc97c1d3d",
    "reference_id": "mursalinasrul@gmail.com_1753276815",
    "status": "berhasil",
    "status_code": "1",
    "sub_total": "50000",
    "total": "52500",
    "amount": "52500",
    "fee": "6000",
    "paid_off": "46500",
    "created_at": "2025-07-23 20:20:35",
    "expired_at": "2025-07-24 20:20:35",
    "paid_at": "2025-07-23 20:20:47",
    "settlement_status": "settled",
    "transaction_status_code": "1",
    "is_escrow": "false",
    "system_notes": "Sandbox notify",
    "via": "va",
    "channel": "bag",
    "payment_no": "000089181211",
    "buyer_name": "xzxz",
    "buyer_email": "mursalinasrul@gmail.com",
    "buyer_phone": "xzxzx",
    "additional_info": "[]",
    "url": "https://streammate-callback.onrender.com/ipaymu-callback",
    "va": "000089181211"
}

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json"
}

print("🔧 Testing callback dengan data yang sama...")
print(f"📤 Sending to: https://streammate-callback.onrender.com/ipaymu-callback")
print(f"📦 Data: {json.dumps(callback_data, indent=2)}")

try:
    response = requests.post(
        "https://streammate-callback.onrender.com/ipaymu-callback",
        data=callback_data,
        headers=headers
    )
    
    print(f"📥 Response Status: {response.status_code}")
    print(f"📥 Response Text: {response.text}")
    
    if response.status_code == 200:
        print("✅ Callback berhasil!")
    else:
        print("❌ Callback gagal!")
        
except Exception as e:
    print(f"❌ Error: {e}") 