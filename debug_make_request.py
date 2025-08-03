#!/usr/bin/env python3
"""
Debug script untuk test _make_request method
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules_client.supabase_client import SupabaseClient

def test_make_request():
    """Test _make_request method directly"""
    print("🧪 Testing _make_request method...")
    
    try:
        # Initialize Supabase client
        supabase = SupabaseClient()
        
        email = "mursalinasrul@gmail.com"
        
        print(f"📧 Testing with email: {email}")
        
        # 1. Test GET request
        print("\n1️⃣ Testing GET request...")
        try:
            get_result = supabase._make_request(
                'GET',
                f"/rest/v1/user_profiles?email=eq.{email}",
                use_service_role=True
            )
            print(f"GET result: {get_result}")
        except Exception as e:
            print(f"❌ GET failed: {e}")
            return False
        
        # 2. Test PATCH request
        print("\n2️⃣ Testing PATCH request...")
        try:
            patch_data = {
                "credits": 17620,  # Reduce credits
                "updated_at": "2025-07-23T15:31:25.916614+00:00"
            }
            
            patch_result = supabase._make_request(
                'PATCH',
                f"/rest/v1/user_profiles?email=eq.{email}",
                patch_data,
                use_service_role=True
            )
            print(f"PATCH result: {patch_result}")
        except Exception as e:
            print(f"❌ PATCH failed: {e}")
            return False
        
        # 3. Test deduct_credits method
        print("\n3️⃣ Testing deduct_credits method...")
        try:
            deduct_result = supabase.deduct_credits(
                email=email,
                amount=100000,
                credit_type="credits",
                component="test",
                description="Test deduction"
            )
            print(f"Deduct result: {deduct_result}")
        except Exception as e:
            print(f"❌ Deduct failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 _make_request Debug Test")
    print("=" * 50)
    
    success = test_make_request()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!") 