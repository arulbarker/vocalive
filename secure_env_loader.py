#!/usr/bin/env python3
"""
Secure Environment Loader - Load kredensial dari Supabase
Menggantikan fungsi os.environ dengan akses aman ke Supabase
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger('StreamMate')

class SecureEnvLoader:
    """Loader untuk kredensial aman dari Supabase"""
    
    def __init__(self):
        """Initialize dengan cache untuk performa"""
        self._cache = {}
        self._migration = None
        self._initialized = False
        
    def _get_migration(self):
        """Lazy loading untuk migration client"""
        if self._migration is None:
            try:
                # Add project root to path
                project_root = Path(__file__).parent
                sys.path.insert(0, str(project_root))
                
                from migrate_credentials_simple import SimpleCredentialsMigration
                self._migration = SimpleCredentialsMigration()
                self._initialized = True
                logger.info("[SECURE-ENV] ✅ Initialized secure environment loader")
            except Exception as e:
                logger.error(f"[SECURE-ENV] ❌ Failed to initialize: {e}")
                self._migration = None
        
        return self._migration
    
    def get(self, key: str, default: str = None, use_cache: bool = True) -> Optional[str]:
        """
        Ambil kredensial dari Supabase dengan fallback ke environment variable
        
        Args:
            key: Nama kredensial
            default: Nilai default jika tidak ditemukan
            use_cache: Gunakan cache untuk performa
        """
        # Cek cache dulu jika enabled
        if use_cache and key in self._cache:
            return self._cache[key]
        
        # Coba ambil dari Supabase
        migration = self._get_migration()
        if migration:
            try:
                value = migration.get_credential(key)
                if value:
                    # Cache untuk performa
                    if use_cache:
                        self._cache[key] = value
                    logger.debug(f"[SECURE-ENV] ✅ Retrieved from Supabase: {key}")
                    return value
            except Exception as e:
                logger.warning(f"[SECURE-ENV] ⚠️ Failed to get {key} from Supabase: {e}")
        
        # Fallback ke environment variable
        env_value = os.environ.get(key, default)
        if env_value and env_value != default:
            logger.debug(f"[SECURE-ENV] 📄 Retrieved from .env: {key}")
            return env_value
        
        # Return default jika tidak ditemukan
        if default is not None:
            logger.debug(f"[SECURE-ENV] 🔄 Using default for: {key}")
            return default
        
        logger.warning(f"[SECURE-ENV] ❌ Credential not found: {key}")
        return None
    
    def get_required(self, key: str) -> str:
        """
        Ambil kredensial yang wajib ada (akan raise error jika tidak ditemukan)
        """
        value = self.get(key)
        if not value:
            error_msg = f"Required credential '{key}' not found in Supabase or environment"
            logger.error(f"[SECURE-ENV] ❌ {error_msg}")
            raise ValueError(error_msg)
        return value
    
    def get_multiple(self, keys: list, required: bool = False) -> Dict[str, str]:
        """
        Ambil beberapa kredensial sekaligus
        
        Args:
            keys: List nama kredensial
            required: Jika True, akan raise error jika ada yang tidak ditemukan
        """
        result = {}
        missing = []
        
        for key in keys:
            value = self.get(key)
            if value:
                result[key] = value
            else:
                missing.append(key)
        
        if required and missing:
            error_msg = f"Required credentials not found: {', '.join(missing)}"
            logger.error(f"[SECURE-ENV] ❌ {error_msg}")
            raise ValueError(error_msg)
        
        logger.info(f"[SECURE-ENV] ✅ Retrieved {len(result)}/{len(keys)} credentials")
        return result
    
    def set_env_variables(self, keys: list = None) -> int:
        """
        Set environment variables dari Supabase untuk kompatibilitas
        
        Args:
            keys: List kredensial yang akan di-set. Jika None, ambil semua
        """
        if keys is None:
            # Ambil semua kredensial dari Supabase
            migration = self._get_migration()
            if migration:
                try:
                    credentials = migration.list_credentials()
                    keys = [cred.get("credential_key") for cred in credentials]
                except Exception as e:
                    logger.error(f"[SECURE-ENV] ❌ Failed to list credentials: {e}")
                    return 0
            else:
                return 0
        
        set_count = 0
        for key in keys:
            value = self.get(key, use_cache=False)  # Fresh fetch
            if value:
                os.environ[key] = value
                set_count += 1
                logger.debug(f"[SECURE-ENV] ✅ Set env var: {key}")
        
        logger.info(f"[SECURE-ENV] ✅ Set {set_count} environment variables")
        return set_count
    
    def clear_cache(self):
        """Clear cache untuk refresh kredensial"""
        self._cache.clear()
        logger.info("[SECURE-ENV] 🔄 Cache cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Check kesehatan sistem kredensial"""
        migration = self._get_migration()
        if not migration:
            return {
                "status": "error",
                "message": "Failed to initialize Supabase connection",
                "supabase_connected": False,
                "credentials_count": 0
            }
        
        try:
            credentials = migration.list_credentials()
            return {
                "status": "healthy",
                "message": "Secure credentials system is working",
                "supabase_connected": True,
                "credentials_count": len(credentials),
                "cache_size": len(self._cache)
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Health check failed: {e}",
                "supabase_connected": False,
                "credentials_count": 0
            }

# Global instance untuk kemudahan penggunaan
secure_env = SecureEnvLoader()

# Helper functions untuk kompatibilitas
def get_secure_env(key: str, default: str = None) -> Optional[str]:
    """Helper function untuk mengambil kredensial aman"""
    return secure_env.get(key, default)

def get_required_env(key: str) -> str:
    """Helper function untuk kredensial wajib"""
    return secure_env.get_required(key)

def setup_secure_environment(keys: list = None) -> int:
    """Setup environment variables dari Supabase"""
    return secure_env.set_env_variables(keys)

def main():
    """Test function"""
    print("🔐 SECURE ENVIRONMENT LOADER TEST")
    print("=" * 50)
    
    # Health check
    health = secure_env.health_check()
    print(f"📊 Status: {health['status']}")
    print(f"🔗 Supabase: {'✅' if health['supabase_connected'] else '❌'}")
    print(f"📋 Credentials: {health['credentials_count']}")
    print()
    
    if health['status'] == 'healthy':
        # Test beberapa kredensial
        test_keys = [
            'GOOGLE_OAUTH_CLIENT_ID',
            'OPENAI_API_KEY', 
            'SUPABASE_SERVICE_ROLE_KEY'
        ]
        
        print("🧪 Testing credential retrieval:")
        for key in test_keys:
            value = secure_env.get(key)
            status = "✅" if value else "❌"
            masked_value = f"{value[:10]}..." if value and len(value) > 10 else "Not found"
            print(f"   {status} {key}: {masked_value}")
        
        print()
        print("🔄 Setting up environment variables...")
        count = secure_env.set_env_variables()
        print(f"✅ Set {count} environment variables")
        
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()