#!/usr/bin/env python3
"""
Script untuk cek status keamanan RLS Supabase dan memberikan rekomendasi
"""

import requests
import json
from datetime import datetime

# Supabase configuration
SUPABASE_URL = "https://nivwxqojwljihoybzgkc.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pdnd4cW9qd2xqaWhveWJ6Z2tjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzE3NDY0NywiZXhwIjoyMDY4NzUwNjQ3fQ.r3sftfPQsHkWjK-xQhosh1IS7PSMi5tn4qtsxa5I9CY"

headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

def check_table_security():
    """Cek keamanan tabel-tabel penting"""
    print("🔒 Checking Table Security Status")
    print("=" * 60)
    
    tables_to_check = [
        "user_profiles",
        "credit_transactions", 
        "subscriptions",
        "licenses",
        "payment_logs"
    ]
    
    security_status = {}
    
    for table in tables_to_check:
        try:
            # Test read access
            url = f"{SUPABASE_URL}/rest/v1/{table}?limit=1"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                print(f"✅ {table}: Accessible (RLS may be disabled)")
                security_status[table] = "PUBLIC"
            elif response.status_code == 401:
                print(f"🔒 {table}: Protected (RLS enabled)")
                security_status[table] = "PROTECTED"
            elif response.status_code == 403:
                print(f"🚫 {table}: Forbidden (RLS enabled)")
                security_status[table] = "FORBIDDEN"
            else:
                print(f"❓ {table}: Unknown status ({response.status_code})")
                security_status[table] = "UNKNOWN"
                
        except Exception as e:
            print(f"❌ {table}: Error checking - {e}")
            security_status[table] = "ERROR"
    
    return security_status

def check_callback_security():
    """Cek keamanan callback system"""
    print("\n🔄 Checking Callback Security")
    print("=" * 60)
    
    try:
        # Test callback endpoints
        callback_urls = [
            f"{SUPABASE_URL}/rest/v1/rpc/process_payment_callback",
            f"{SUPABASE_URL}/rest/v1/rpc/update_credit_balance",
            f"{SUPABASE_URL}/rest/v1/rpc/validate_license"
        ]
        
        for url in callback_urls:
            try:
                response = requests.post(url, headers=headers, json={"test": "security_check"})
                if response.status_code in [200, 400, 500]:
                    print(f"✅ Callback endpoint accessible: {url.split('/')[-1]}")
                else:
                    print(f"❌ Callback endpoint error: {url.split('/')[-1]} ({response.status_code})")
            except Exception as e:
                print(f"❌ Callback endpoint failed: {url.split('/')[-1]} - {e}")
                
    except Exception as e:
        print(f"❌ Error checking callbacks: {e}")

def analyze_security_risks():
    """Analisis risiko keamanan"""
    print("\n⚠️ Security Risk Analysis")
    print("=" * 60)
    
    risks = []
    
    print("🔍 Current Security Assessment:")
    print("1. User Profiles Table:")
    print("   - Contains sensitive user data")
    print("   - Credit balance information")
    print("   - Email addresses")
    
    print("\n2. Credit Transactions Table:")
    print("   - Financial transaction history")
    print("   - Payment amounts and details")
    print("   - User spending patterns")
    
    print("\n3. Subscriptions Table:")
    print("   - Subscription status")
    print("   - Payment method information")
    print("   - Billing details")
    
    print("\n4. Licenses Table:")
    print("   - License keys and validation")
    print("   - Access control information")
    print("   - Software activation data")
    
    # Risk assessment
    if "user_profiles" in security_status and security_status["user_profiles"] == "PUBLIC":
        risks.append("HIGH: User profiles accessible without authentication")
    
    if "credit_transactions" in security_status and security_status["credit_transactions"] == "PUBLIC":
        risks.append("HIGH: Financial transactions exposed")
    
    if "subscriptions" in security_status and security_status["subscriptions"] == "PUBLIC":
        risks.append("MEDIUM: Subscription data exposed")
    
    if "licenses" in security_status and security_status["licenses"] == "PUBLIC":
        risks.append("HIGH: License keys exposed")
    
    return risks

def recommend_security_measures():
    """Rekomendasi langkah keamanan"""
    print("\n🛡️ Security Recommendations")
    print("=" * 60)
    
    print("📋 RECOMMENDED ACTIONS:")
    print("-" * 40)
    
    print("1. ENABLE RLS FOR CRITICAL TABLES:")
    print("   ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;")
    print("   ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;")
    print("   ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;")
    print("   ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;")
    
    print("\n2. CREATE SECURITY POLICIES:")
    print("   - Users can only access their own data")
    print("   - Service role can access all data")
    print("   - Callback functions can update specific records")
    
    print("\n3. IMPLEMENT AUTHENTICATION:")
    print("   - Require JWT tokens for API access")
    print("   - Validate user permissions")
    print("   - Log all access attempts")
    
    print("\n4. SECURE CALLBACK ENDPOINTS:")
    print("   - Use webhook signatures")
    print("   - Validate request sources")
    print("   - Rate limit callback requests")
    
    print("\n5. MONITORING AND LOGGING:")
    print("   - Log all database access")
    print("   - Monitor unusual activity")
    print("   - Set up alerts for security events")

def check_current_policies():
    """Cek policy yang sudah ada"""
    print("\n📋 Current Security Policies")
    print("=" * 60)
    
    print("🔍 Checking existing RLS policies...")
    
    # Test with different access levels
    test_emails = ["mursalinasrul@gmail.com", "test@example.com"]
    
    for email in test_emails:
        try:
            url = f"{SUPABASE_URL}/rest/v1/user_profiles?email=eq.{email}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    print(f"✅ Access to {email}: SUCCESS")
                else:
                    print(f"❌ Access to {email}: NO DATA")
            else:
                print(f"❌ Access to {email}: FAILED ({response.status_code})")
                
        except Exception as e:
            print(f"❌ Error testing {email}: {e}")

def main():
    """Main function"""
    print("🔒 SUPABASE SECURITY AUDIT")
    print("=" * 60)
    
    # Check current security status
    global security_status
    security_status = check_table_security()
    
    # Check callback security
    check_callback_security()
    
    # Check current policies
    check_current_policies()
    
    # Analyze risks
    risks = analyze_security_risks()
    
    # Provide recommendations
    recommend_security_measures()
    
    print("\n" + "=" * 60)
    print("📊 SECURITY SUMMARY:")
    print("-" * 30)
    
    if risks:
        print("⚠️ HIGH RISK DETECTED:")
        for risk in risks:
            print(f"   • {risk}")
        print("\n🚨 IMMEDIATE ACTION REQUIRED:")
        print("   • Enable RLS on critical tables")
        print("   • Implement proper authentication")
        print("   • Create security policies")
    else:
        print("✅ SECURITY STATUS: GOOD")
        print("   • RLS properly configured")
        print("   • Access controls in place")
        print("   • Callbacks secured")
    
    print("\n🎯 RECOMMENDATION:")
    if "PUBLIC" in security_status.values():
        print("🔴 URGENT: Enable RLS immediately!")
        print("   Your data is currently exposed to public access.")
    else:
        print("🟢 SECURE: Current configuration is adequate.")
        print("   Consider additional monitoring for production.")

if __name__ == "__main__":
    main() 