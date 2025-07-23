import os
from supabase import create_client, Client

# Test Supabase connection dengan service role key yang baru
print("🧪 Testing Supabase Connection dengan Service Role Key Baru...")

# Environment variables dengan key yang benar
SUPABASE_URL = "https://nivwxqojwljihoybzgkc.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzE3NDY0NywiZXhwIjoyMDY4NzUwNjQ3fQ.r3sftfPQsHkWjK-xQhosh1IS7PSMi5tn4qtsxa5I9CY"

print(f"URL: {SUPABASE_URL}")
print(f"Service Role Key: {SUPABASE_SERVICE_ROLE_KEY[:50]}...")

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
        
        # Test update credits (simulasi payment)
        print(f"\n🧪 Testing credit update...")
        new_credits = user['credits'] + 10
        update_response = supabase.table('user_profiles').update({'credits': new_credits}).eq('id', user['id']).execute()
        
        if update_response.data:
            print(f"✅ Credit update successful! New credits: {new_credits}")
        else:
            print("❌ Credit update failed")
            
    else:
        print("❌ User not found in database")
        print("💡 Create user first or check email spelling")
    
except Exception as e:
    print(f"❌ Supabase connection error: {e}")
    print("💡 Check your SUPABASE_SERVICE_ROLE_KEY")

print("\n📋 Next steps:")
print("1. Update SUPABASE_SERVICE_ROLE_KEY in Render environment variables")
print("2. Manual deploy di Render")
print("3. Test callback dengan user yang ada") 