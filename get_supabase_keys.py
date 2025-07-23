import requests
import json

print("🔑 Supabase Keys Helper")
print("=" * 50)

print("\n📋 Untuk mendapatkan Service Role Key yang benar:")
print("1. Buka https://supabase.com/dashboard")
print("2. Pilih project: nivwxqojwljihoybzgkc")
print("3. Go to Settings > API")
print("4. Copy 'service_role' key (bukan anon key)")
print("5. Update di Render environment variables")

print("\n📋 Untuk mendapatkan Anon Key:")
print("1. Di halaman yang sama")
print("2. Copy 'anon' key")
print("3. Gunakan untuk client-side access")

print("\n🔍 Test connection dengan anon key...")

# Test dengan anon key (biasanya lebih mudah diakses)
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzMyNzY0MDAsImV4cCI6MjA0ODg1MjQwMH0.Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8"

headers = {
    "apikey": ANON_KEY,
    "Authorization": f"Bearer {ANON_KEY}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(
        "https://nivwxqojwljihoybzgkc.supabase.co/rest/v1/user_profiles?select=count",
        headers=headers
    )
    
    print(f"📊 Anon Key Test Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Anon key works!")
    else:
        print(f"❌ Anon key error: {response.text}")
        
except Exception as e:
    print(f"❌ Error testing anon key: {e}")

print("\n" + "=" * 50)
print("💡 Tips:")
print("- Service role key dimulai dengan 'eyJ...'")
print("- Jangan share service role key ke public")
print("- Gunakan anon key untuk client-side")
print("- Gunakan service role key untuk server-side") 