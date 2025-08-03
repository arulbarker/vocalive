#!/usr/bin/env python3
"""
Script untuk setup .env file dengan kredensial yang ada
"""

import os
import json
import re

def extract_supabase_credentials():
    """Extract Supabase credentials dari file yang ada"""
    print("🔍 Extracting Supabase Credentials")
    print("=" * 60)
    
    supabase_url = "https://nivwxqojwljihoybzgkc.supabase.co"
    service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzE3NDY0NywiZXhwIjoyMDY4NzUwNjQ3fQ.r3sftfPQsHkWjK-xQhosh1IS7PSMi5tn4qtsxa5I9CY"
    
    print(f"✅ Supabase URL: {supabase_url}")
    print(f"✅ Service Role Key: {service_role_key[:20]}...")
    
    return {
        "SUPABASE_URL": supabase_url,
        "SUPABASE_SERVICE_ROLE_KEY": service_role_key
    }

def extract_google_oauth_credentials():
    """Extract Google OAuth credentials"""
    print("\n🔍 Extracting Google OAuth Credentials")
    print("=" * 60)
    
    google_creds = {}
    
    # Check google_oauth.json
    if os.path.exists("config/google_oauth.json"):
        try:
            with open("config/google_oauth.json", "r") as f:
                data = json.load(f)
                print("✅ Found google_oauth.json")
                
                if "client_id" in data:
                    google_creds["GOOGLE_OAUTH_CLIENT_ID"] = data["client_id"]
                    print(f"   Client ID: {data['client_id'][:20]}...")
                
                if "client_secret" in data:
                    google_creds["GOOGLE_OAUTH_CLIENT_SECRET"] = data["client_secret"]
                    print(f"   Client Secret: {data['client_secret'][:20]}...")
        except Exception as e:
            print(f"❌ Error reading google_oauth.json: {e}")
    
    # Check google_oauth.py
    if os.path.exists("modules_client/google_oauth.py"):
        try:
            with open("modules_client/google_oauth.py", "r") as f:
                content = f.read()
                
                # Extract client ID
                client_id_match = re.search(r'client_id["\']?\s*[:=]\s*["\']([^"\']+)["\']', content)
                if client_id_match:
                    google_creds["GOOGLE_OAUTH_CLIENT_ID"] = client_id_match.group(1)
                    print(f"✅ Found Client ID in google_oauth.py: {client_id_match.group(1)[:20]}...")
                
                # Extract client secret
                client_secret_match = re.search(r'client_secret["\']?\s*[:=]\s*["\']([^"\']+)["\']', content)
                if client_secret_match:
                    google_creds["GOOGLE_OAUTH_CLIENT_SECRET"] = client_secret_match.group(1)
                    print(f"✅ Found Client Secret in google_oauth.py: {client_secret_match.group(1)[:20]}...")
        except Exception as e:
            print(f"❌ Error reading google_oauth.py: {e}")
    
    return google_creds

def extract_payment_credentials():
    """Extract payment gateway credentials"""
    print("\n🔍 Extracting Payment Gateway Credentials")
    print("=" * 60)
    
    payment_creds = {}
    
    # Check for Stripe keys in main.py
    if os.path.exists("main.py"):
        try:
            with open("main.py", "r") as f:
                content = f.read()
                
                # Extract Stripe keys
                stripe_secret_match = re.search(r'sk_[a-zA-Z0-9]+', content)
                if stripe_secret_match:
                    payment_creds["STRIPE_SECRET_KEY"] = stripe_secret_match.group(0)
                    print(f"✅ Found Stripe Secret Key: {stripe_secret_match.group(0)[:20]}...")
                
                stripe_publishable_match = re.search(r'pk_[a-zA-Z0-9]+', content)
                if stripe_publishable_match:
                    payment_creds["STRIPE_PUBLISHABLE_KEY"] = stripe_publishable_match.group(0)
                    print(f"✅ Found Stripe Publishable Key: {stripe_publishable_match.group(0)[:20]}...")
        except Exception as e:
            print(f"❌ Error reading main.py: {e}")
    
    # Check for iPaymu keys
    if os.path.exists("modules_server/ipaymu_handler.py"):
        try:
            with open("modules_server/ipaymu_handler.py", "r") as f:
                content = f.read()
                
                # Extract iPaymu API key
                ipaymu_match = re.search(r'api_key["\']?\s*[:=]\s*["\']([^"\']+)["\']', content)
                if ipaymu_match:
                    payment_creds["IPAYMU_API_KEY"] = ipaymu_match.group(1)
                    print(f"✅ Found iPaymu API Key: {ipaymu_match.group(1)[:20]}...")
        except Exception as e:
            print(f"❌ Error reading ipaymu_handler.py: {e}")
    
    return payment_creds

def update_env_file(credentials):
    """Update .env file dengan kredensial yang ditemukan"""
    print("\n📝 Updating .env File")
    print("=" * 60)
    
    if not os.path.exists(".env"):
        print("❌ .env file not found. Please run: copy .env.template .env")
        return False
    
    try:
        # Read current .env content
        with open(".env", "r") as f:
            env_content = f.read()
        
        # Update with found credentials
        updated_content = env_content
        
        for key, value in credentials.items():
            # Replace placeholder with real value
            placeholder = f"{key}=your_{key.lower()}_here"
            replacement = f"{key}={value}"
            
            if placeholder in updated_content:
                updated_content = updated_content.replace(placeholder, replacement)
                print(f"✅ Updated {key}")
            else:
                # Add new line if not found
                updated_content += f"\n{replacement}"
                print(f"✅ Added {key}")
        
        # Write updated content
        with open(".env", "w") as f:
            f.write(updated_content)
        
        print("✅ .env file updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def verify_env_file():
    """Verify .env file content"""
    print("\n🔍 Verifying .env File")
    print("=" * 60)
    
    if not os.path.exists(".env"):
        print("❌ .env file not found")
        return False
    
    try:
        with open(".env", "r") as f:
            content = f.read()
        
        # Check for real credentials (not placeholders)
        real_credentials = []
        placeholder_credentials = []
        
        lines = content.split('\n')
        for line in lines:
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                if 'your_' in value or value.strip() == '':
                    placeholder_credentials.append(key)
                else:
                    real_credentials.append(key)
        
        print("✅ Real credentials found:")
        for cred in real_credentials:
            print(f"   • {cred}")
        
        if placeholder_credentials:
            print("\n⚠️  Placeholder credentials (need to be filled):")
            for cred in placeholder_credentials:
                print(f"   • {cred}")
        
        return len(real_credentials) > 0
        
    except Exception as e:
        print(f"❌ Error verifying .env file: {e}")
        return False

def main():
    """Main function"""
    print("🔐 SETUP .env FILE WITH CREDENTIALS")
    print("=" * 60)
    
    # Extract all credentials
    all_credentials = {}
    
    # Supabase credentials
    supabase_creds = extract_supabase_credentials()
    all_credentials.update(supabase_creds)
    
    # Google OAuth credentials
    google_creds = extract_google_oauth_credentials()
    all_credentials.update(google_creds)
    
    # Payment credentials
    payment_creds = extract_payment_credentials()
    all_credentials.update(payment_creds)
    
    print(f"\n📊 Found {len(all_credentials)} credentials")
    
    # Update .env file
    if all_credentials:
        success = update_env_file(all_credentials)
        if success:
            print("\n✅ .env file updated successfully!")
        else:
            print("\n❌ Failed to update .env file")
    else:
        print("\n⚠️  No credentials found. Please add them manually.")
    
    # Verify the result
    verify_env_file()
    
    print("\n" + "=" * 60)
    print("📋 NEXT STEPS:")
    print("-" * 30)
    print("1. ✅ .env file created and updated")
    print("2. 🔧 Update code to use environment variables")
    print("3. 🧪 Test application functionality")
    print("4. 🔒 Commit security improvements")
    print("5. 📊 Monitor for any issues")

if __name__ == "__main__":
    main() 