import requests
import json

# Supabase configuration
SUPABASE_URL = "https://nivwxqojwljihoybzgkc.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzE3NDY0NywiZXhwIjoyMDY4NzUwNjQ3fQ.r3sftfPQsHkWjK-xQhosh1IS7PSMi5tn4qtsxa5I9CY"

headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

def check_user_profiles_structure():
    """Check user_profiles table structure"""
    print("🔍 Checking user_profiles table structure...")
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/user_profiles?select=*&limit=1",
            headers=headers
        )
        
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            if users:
                user = users[0]
                print(f"📊 User fields found:")
                for field, value in user.items():
                    print(f"  - {field}: {value}")
            else:
                print("❌ No users found")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking user_profiles structure: {e}")

def check_specific_user_data():
    """Check specific user data"""
    print("\n🔍 Checking specific user data: mursalinasrul@gmail.com...")
    
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
                print(f"✅ User data:")
                for field, value in user.items():
                    print(f"  - {field}: {value}")
            else:
                print("❌ User not found!")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking specific user: {e}")

def check_payments_structure():
    """Check payments table structure"""
    print("\n🔍 Checking payments table structure...")
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/payments?select=*&limit=1",
            headers=headers
        )
        
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            payments = response.json()
            if payments:
                payment = payments[0]
                print(f"📊 Payment fields found:")
                for field, value in payment.items():
                    print(f"  - {field}: {value}")
            else:
                print("❌ No payments found")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking payments structure: {e}")

if __name__ == "__main__":
    print("🔍 Database Structure Check")
    print("=" * 50)
    
    check_user_profiles_structure()
    check_specific_user_data()
    check_payments_structure()
    
    print("\n" + "=" * 50)
    print("✅ Structure check completed!") 