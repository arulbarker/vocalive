#!/usr/bin/env python3
"""
Test Supabase Connection
Quick test to verify Supabase is accessible before migration
"""

import sys
import json
from pathlib import Path
from supabase import create_client, Client

def test_supabase_connection():
    """Test connection to Supabase"""
    try:
        # Load config
        config_path = Path("../config/supabase_config.json")
        if not config_path.exists():
            print("❌ Supabase config file not found!")
            return False
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"🔗 Testing connection to: {config['url']}")
        
        # Create client
        supabase: Client = create_client(
            config['url'],
            config['service_role_key']
        )
        
        # Test simple query
        result = supabase.table('licenses').select('*').limit(1).execute()
        
        print("✅ Supabase connection successful!")
        print(f"📊 Database accessible, ready for migration")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("🔧 Please check:")
        print("  1. Supabase project is active")
        print("  2. Database schema has been created")
        print("  3. Service role key is correct")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1) 