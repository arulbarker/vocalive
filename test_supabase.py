import os
from supabase import create_client, Client

# Test Supabase connection
print("🧪 Testing Supabase Connection...")

# Environment variables (set these manually for testing)
SUPABASE_URL = "https://nivwxqojwljihoybzgkc.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "your_service_role_key_here"  # Ganti dengan key yang benar

print(f"URL: {SUPABASE_URL}")
print(f"Key: {SUPABASE_SERVICE_ROLE_KEY[:10]}...")

try:
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    print("✅ Supabase client created successfully")
    
    # Test connection by querying user_profiles
    print("\n🔍 Testing database connection...")
    
    response = supabase.table('user_profiles').select('id, email, credits').limit(5).execute()
    
    print(f"✅ Database query successful!")
    print(f"📊 Found {len(response.data)} users:")
    
    for user in response.data:
        print(f"  - {user.get('email', 'N/A')} (ID: {user.get('id', 'N/A')}, Credits: {user.get('credits', 0)})")
    
    # Check specific user
    print(f"\n🔍 Checking user: mursalinasrul@gmail.com")
    
    user_response = supabase.table('user_profiles').select('id, email, credits').eq('email', 'mursalinasrul@gmail.com').execute()
    
    if user_response.data:
        user = user_response.data[0]
        print(f"✅ User found: {user['email']} (ID: {user['id']}, Credits: {user['credits']})")
    else:
        print("❌ User not found in database")
        print("💡 Create user first or check email spelling")
    
except Exception as e:
    print(f"❌ Supabase connection error: {e}")
    print("💡 Check your SUPABASE_SERVICE_ROLE_KEY")

print("\n📋 Next steps:")
print("1. Set correct SUPABASE_SERVICE_ROLE_KEY in Render")
print("2. Create user in database if not exists")
print("3. Test callback again") 