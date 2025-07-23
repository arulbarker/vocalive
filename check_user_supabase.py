import requests
import json
import os

# Supabase configuration
SUPABASE_URL = "https://nivwxqojwljihoybzgkc.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMzI3NjQwMCwiZXhwIjoyMDQ4ODUyNDAwfQ.Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8"

headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

def check_user_profiles():
    """Check user_profiles table"""
    print("🔍 Checking user_profiles table...")
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/user_profiles",
            headers=headers
        )
        
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            print(f"📊 Found {len(users)} users:")
            for user in users:
                print(f"  - {user.get('email', 'No email')}: {user.get('credits', 0)} credits")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking user_profiles: {e}")

def check_payments():
    """Check payments table"""
    print("\n🔍 Checking payments table...")
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/payments",
            headers=headers
        )
        
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            payments = response.json()
            print(f"📊 Found {len(payments)} payments:")
            for payment in payments:
                print(f"  - {payment.get('transaction_id', 'No ID')}: {payment.get('amount', 0)} - {payment.get('status', 'No status')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking payments: {e}")

def check_specific_user():
    """Check specific user mursalinasrul@gmail.com"""
    print("\n🔍 Checking specific user: mursalinasrul@gmail.com...")
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.mursalinasrul@gmail.com",
            headers=headers
        )
        
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            if users:
                user = users[0]
                print(f"✅ User found:")
                print(f"  - Email: {user.get('email')}")
                print(f"  - Credits: {user.get('credits', 0)}")
                print(f"  - ID: {user.get('id')}")
            else:
                print("❌ User not found!")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking specific user: {e}")

def create_user_if_not_exists():
    """Create user if not exists"""
    print("\n🔧 Creating user if not exists...")
    
    user_data = {
        "email": "mursalinasrul@gmail.com",
        "credits": 0,
        "created_at": "2025-07-23T20:30:00.000Z"
    }
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/user_profiles",
            headers=headers,
            json=user_data
        )
        
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 201:
            print("✅ User created successfully!")
        elif response.status_code == 409:
            print("ℹ️ User already exists")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")

if __name__ == "__main__":
    print("🔍 Supabase Database Check")
    print("=" * 50)
    
    check_user_profiles()
    check_payments()
    check_specific_user()
    create_user_if_not_exists()
    
    print("\n" + "=" * 50)
    print("✅ Check completed!") 