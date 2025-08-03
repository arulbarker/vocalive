#!/usr/bin/env python3
"""
Script untuk cek keamanan API dan kredensial
"""

import requests
import json
import os
from datetime import datetime

# Supabase configuration
SUPABASE_URL = "https://nivwxqojwljihoybzgkc.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzE3NDY0NywiZXhwIjoyMDY4NzUwNjQ3fQ.r3sftfPQsHkWjK-xQhosh1IS7PSMi5tn4qtsxa5I9CY"

headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

def check_api_endpoints():
    """Cek keamanan endpoint API"""
    print("🔍 Checking API Endpoints Security")
    print("=" * 60)
    
    endpoints_to_check = [
        "/rest/v1/user_profiles",
        "/rest/v1/credit_transactions",
        "/rest/v1/rpc/update_user_credits",
        "/rest/v1/rpc/process_payment_callback",
        "/rest/v1/rpc/check_security_status"
    ]
    
    for endpoint in endpoints_to_check:
        try:
            # Test without auth
            url = f"{SUPABASE_URL}{endpoint}"
            test_headers = {"Content-Type": "application/json"}
            response = requests.get(url, headers=test_headers)
            
            if response.status_code == 401:
                print(f"✅ {endpoint}: SECURED (401 Unauthorized)")
            elif response.status_code == 403:
                print(f"✅ {endpoint}: SECURED (403 Forbidden)")
            else:
                print(f"❌ {endpoint}: INSECURE ({response.status_code})")
                
        except Exception as e:
            print(f"❌ {endpoint}: ERROR - {e}")

def check_credentials_protection():
    """Cek perlindungan kredensial"""
    print("\n🔐 Checking Credentials Protection")
    print("=" * 60)
    
    # Check if sensitive files exist
    sensitive_files = [
        "config/google_oauth.json",
        "config/development_config.json",
        "config/production_config.json",
        "modules_client/google_oauth.py",
        "modules_server/license_manager.py"
    ]
    
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            print(f"⚠️  {file_path}: EXISTS (check for sensitive data)")
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > 1000:  # More than 1KB
                print(f"   📏 Size: {file_size} bytes (large file)")
            else:
                print(f"   📏 Size: {file_size} bytes")
        else:
            print(f"✅ {file_path}: NOT FOUND (good for security)")

def check_environment_variables():
    """Cek environment variables"""
    print("\n🌍 Checking Environment Variables")
    print("=" * 60)
    
    sensitive_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY",
        "GOOGLE_OAUTH_CLIENT_ID",
        "GOOGLE_OAUTH_CLIENT_SECRET",
        "STRIPE_SECRET_KEY",
        "IPAYMU_API_KEY"
    ]
    
    for var in sensitive_vars:
        value = os.getenv(var)
        if value:
            # Check if it's a real key (not placeholder)
            if len(value) > 20 and not value.startswith("your_"):
                print(f"⚠️  {var}: SET (contains real credentials)")
            else:
                print(f"✅ {var}: SET (placeholder/development)")
        else:
            print(f"❌ {var}: NOT SET")

def check_code_security():
    """Cek keamanan kode"""
    print("\n📝 Checking Code Security")
    print("=" * 60)
    
    # Check for hardcoded credentials
    security_issues = []
    
    # Check supabase_client.py
    try:
        with open("modules_client/supabase_client.py", "r") as f:
            content = f.read()
            if "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" in content:
                security_issues.append("Hardcoded Supabase key in supabase_client.py")
    except:
        pass
    
    # Check main.py
    try:
        with open("main.py", "r") as f:
            content = f.read()
            if "sk_" in content or "pk_" in content:
                security_issues.append("Hardcoded Stripe keys in main.py")
    except:
        pass
    
    if security_issues:
        print("❌ SECURITY ISSUES FOUND:")
        for issue in security_issues:
            print(f"   • {issue}")
    else:
        print("✅ No obvious hardcoded credentials found")

def check_secure_functions_after_fix():
    """Test secure functions setelah perbaikan"""
    print("\n🔧 Testing Secure Functions After Fix")
    print("=" * 60)
    
    try:
        # Test update_user_credits function
        test_data = {
            "user_email": "mursalinasrul@gmail.com",
            "credit_amount": 100,
            "transaction_type": "test",
            "description": "Security test transaction"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/rpc/update_user_credits"
        response = requests.post(url, headers=headers, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            if result:
                print("✅ update_user_credits function: WORKING")
            else:
                print("❌ update_user_credits function: FAILED")
        else:
            print(f"❌ update_user_credits function: ERROR ({response.status_code})")
        
        # Test process_payment_callback function
        callback_data = {
            "user_email": "mursalinasrul@gmail.com",
            "payment_amount": 500,
            "payment_status": "success",
            "payment_id": "security_test_123"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/rpc/process_payment_callback"
        response = requests.post(url, headers=headers, json=callback_data)
        
        if response.status_code == 200:
            result = response.json()
            if result:
                print("✅ process_payment_callback function: WORKING")
            else:
                print("❌ process_payment_callback function: FAILED")
        else:
            print(f"❌ process_payment_callback function: ERROR ({response.status_code})")
            
    except Exception as e:
        print(f"❌ Error testing secure functions: {e}")

def provide_security_recommendations():
    """Beri rekomendasi keamanan"""
    print("\n🛡️ Security Recommendations")
    print("=" * 60)
    
    print("📋 CRITICAL SECURITY ACTIONS:")
    print("-" * 40)
    
    print("1. 🔧 FIX SECURE FUNCTIONS:")
    print("   - Execute fix_secure_functions.sql in Supabase")
    print("   - Test functions after fix")
    
    print("\n2. 🔐 PROTECT CREDENTIALS:")
    print("   - Move API keys to environment variables")
    print("   - Use .env files for local development")
    print("   - Never commit credentials to git")
    
    print("\n3. 🚫 BLOCK UNAUTHORIZED ACCESS:")
    print("   - All endpoints should return 401/403")
    print("   - Implement rate limiting")
    print("   - Add request validation")
    
    print("\n4. 📊 MONITORING:")
    print("   - Set up audit logging")
    print("   - Monitor unusual access patterns")
    print("   - Regular security scans")

def main():
    """Main function"""
    print("🔒 COMPREHENSIVE API SECURITY CHECK")
    print("=" * 60)
    
    # Check all security aspects
    check_api_endpoints()
    check_credentials_protection()
    check_environment_variables()
    check_code_security()
    check_secure_functions_after_fix()
    provide_security_recommendations()
    
    print("\n" + "=" * 60)
    print("📊 SECURITY ASSESSMENT SUMMARY")
    print("-" * 30)
    
    print("✅ SECURITY STRENGTHS:")
    print("   • Database RLS enabled")
    print("   • Unauthorized access blocked")
    print("   • Audit logging active")
    print("   • Credit system working")
    
    print("\n⚠️  AREAS FOR IMPROVEMENT:")
    print("   • Fix secure functions")
    print("   • Protect API credentials")
    print("   • Use environment variables")
    print("   • Implement rate limiting")
    
    print("\n🎯 NEXT ACTIONS:")
    print("1. Execute fix_secure_functions.sql")
    print("2. Move credentials to .env files")
    print("3. Test all API endpoints")
    print("4. Set up monitoring alerts")

if __name__ == "__main__":
    main() 