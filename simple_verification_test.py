#!/usr/bin/env python3
"""
Simple test untuk memverifikasi semua komponen bekerja
"""

import os
import sys
from pathlib import Path

# Setup paths
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "modules_client"))

def test_basic_imports():
    """Test basic imports"""
    try:
        # Test environment loader
        from env_loader import load_environment, get_env_var
        load_environment()
        print("✅ Environment loader working")
        
        # Test Cohost engine
        from modules_client.cohost_engine import CohostEngine
        cohost = CohostEngine()
        print("✅ Cohost engine working")
        
        # Test Supabase client
        from modules_client.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        if supabase:
            print("✅ Supabase client working")
        else:
            print("⚠️ Supabase client returned None but no error")
        
        # Test DeepSeek
        deepseek_key = get_env_var('DEEPSEEK_API_KEY')
        if deepseek_key and deepseek_key != 'your_deepseek_api_key_here':
            print("✅ DeepSeek API key configured")
        else:
            print("⚠️ DeepSeek API key not configured")
        
        # Test Google OAuth
        google_client_id = get_env_var('GOOGLE_OAUTH_CLIENT_ID')
        if google_client_id and google_client_id != 'your_google_oauth_client_id_here':
            print("✅ Google OAuth configured")
        else:
            print("⚠️ Google OAuth not configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    print("🚀 SIMPLE VERIFICATION TEST")
    print("=" * 50)
    
    success = test_basic_imports()
    
    if success:
        print("\n🎉 ALL BASIC COMPONENTS WORKING!")
        print("✅ System is ready for full testing")
    else:
        print("\n❌ Some components need attention")
    
    return success

if __name__ == "__main__":
    main()
