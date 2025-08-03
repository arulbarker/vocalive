#!/usr/bin/env python3
"""
Add DeepSeek API Key to Supabase Secure Storage
"""

import sys
import os
import json
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migrate_credentials_simple import SimpleCredentialsMigration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_deepseek_api_key():
    """Add DeepSeek API key to Supabase"""
    try:
        # Initialize migration client
        migration = SimpleCredentialsMigration()
        
        # Read API key from settings.json
        settings_path = "config/settings.json"
        if not os.path.exists(settings_path):
            logger.error(f"❌ Settings file not found: {settings_path}")
            return False
        
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        deepseek_key = settings.get('api_keys', {}).get('DEEPSEEK_API_KEY')
        
        if not deepseek_key:
            logger.error("❌ DEEPSEEK_API_KEY not found in settings.json")
            return False
        
        logger.info(f"🔑 Found DEEPSEEK_API_KEY: {deepseek_key[:10]}...")
        
        # Store in Supabase
        logger.info("🔄 Storing DEEPSEEK_API_KEY in Supabase...")
        success = migration.store_credential(
            key="DEEPSEEK_API_KEY",
            value=deepseek_key,
            credential_type="api_key",
            description="DeepSeek AI API key for chat completions"
        )
        
        if success:
            logger.info("✅ DEEPSEEK_API_KEY successfully stored in Supabase")
            
            # Verify storage
            logger.info("🔍 Verifying storage...")
            retrieved_key = migration.get_credential("DEEPSEEK_API_KEY")
            
            if retrieved_key == deepseek_key:
                logger.info("✅ Verification successful - API key matches")
                return True
            else:
                logger.error("❌ Verification failed - API key mismatch")
                return False
        else:
            logger.error("❌ Failed to store DEEPSEEK_API_KEY")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error adding DeepSeek API key: {e}")
        return False

def main():
    """Main function"""
    logger.info("🔐 ADDING DEEPSEEK API KEY TO SUPABASE")
    logger.info("=" * 50)
    
    success = add_deepseek_api_key()
    
    if success:
        logger.info("\n🎉 SUCCESS!")
        logger.info("✅ DEEPSEEK_API_KEY is now securely stored in Supabase")
        logger.info("✅ Protected with AES-256 encryption")
        logger.info("✅ Row Level Security enabled")
        logger.info("\n📋 Next steps:")
        logger.info("1. Test DeepSeek API connection")
        logger.info("2. Update applications to use secure credentials")
    else:
        logger.error("\n❌ FAILED!")
        logger.error("Could not add DEEPSEEK_API_KEY to Supabase")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())