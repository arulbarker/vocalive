"""
Secure Credentials Manager - Mengelola kredensial penting di Supabase
Sistem keamanan tingkat enterprise untuk menyimpan API keys, OAuth tokens, dll.
"""

import os
import json
import hashlib
import base64
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger('StreamMate')

class SecureCredentialsManager:
    """Manager untuk kredensial aman di Supabase"""
    
    def __init__(self):
        """Initialize dengan koneksi Supabase"""
        try:
            from modules_client.supabase_client import SupabaseClient
            self.supabase = SupabaseClient()
            self.encryption_key = self._get_encryption_key()
            logger.info("[SECURE-CREDS] Initialized with Supabase backend")
        except Exception as e:
            logger.error(f"[SECURE-CREDS] Failed to initialize: {e}")
            raise
    
    def _get_encryption_key(self) -> str:
        """Generate atau ambil encryption key yang konsisten"""
        # Gunakan kombinasi dari beberapa faktor untuk membuat key yang unik tapi konsisten
        machine_id = os.environ.get('COMPUTERNAME', 'default')
        app_secret = "StreamMateAI_SecureKey_2024"
        
        # Buat hash yang konsisten
        combined = f"{machine_id}_{app_secret}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    def store_credential(self, key: str, value: str, credential_type: str, description: str = None) -> Dict[str, Any]:
        """
        Simpan kredensial secara aman di Supabase
        
        Args:
            key: Nama unik untuk kredensial (contoh: 'GOOGLE_OAUTH_CLIENT_ID')
            value: Nilai kredensial yang akan dienkripsi
            credential_type: Jenis kredensial ('api_key', 'oauth', 'database', 'payment')
            description: Deskripsi opsional
        """
        try:
            # Panggil fungsi Supabase untuk menyimpan kredensial terenkripsi
            endpoint = "/rest/v1/rpc/store_secure_credential"
            data = {
                "p_key": key,
                "p_value": value,
                "p_type": credential_type,
                "p_description": description,
                "p_encryption_key": self.encryption_key
            }
            
            response = self.supabase._make_request("POST", endpoint, data, use_service_role=True)
            
            if response.get("status") == "success":
                logger.info(f"[SECURE-CREDS] ✅ Stored credential: {key}")
                return {
                    "status": "success",
                    "message": f"Credential '{key}' stored securely",
                    "key": key
                }
            else:
                logger.error(f"[SECURE-CREDS] ❌ Failed to store {key}: {response.get('message')}")
                return {
                    "status": "error",
                    "message": response.get("message", "Unknown error"),
                    "key": key
                }
                
        except Exception as e:
            logger.error(f"[SECURE-CREDS] ❌ Exception storing {key}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "key": key
            }
    
    def get_credential(self, key: str) -> Dict[str, Any]:
        """
        Ambil dan dekripsi kredensial dari Supabase
        
        Args:
            key: Nama kredensial yang ingin diambil
            
        Returns:
            Dict dengan status, value (jika berhasil), dan metadata
        """
        try:
            # Panggil fungsi Supabase untuk mengambil kredensial
            endpoint = "/rest/v1/rpc/get_secure_credential"
            data = {
                "p_key": key,
                "p_encryption_key": self.encryption_key
            }
            
            response = self.supabase._make_request("POST", endpoint, data, use_service_role=True)
            
            if response.get("status") == "success":
                logger.info(f"[SECURE-CREDS] ✅ Retrieved credential: {key}")
                return {
                    "status": "success",
                    "key": key,
                    "value": response.get("value"),
                    "type": response.get("type")
                }
            else:
                logger.warning(f"[SECURE-CREDS] ⚠️ Credential not found: {key}")
                return {
                    "status": "error",
                    "message": response.get("message", "Credential not found"),
                    "key": key
                }
                
        except Exception as e:
            logger.error(f"[SECURE-CREDS] ❌ Exception retrieving {key}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "key": key
            }
    
    def list_credentials(self) -> Dict[str, Any]:
        """Ambil daftar semua kredensial (tanpa nilai, hanya metadata)"""
        try:
            endpoint = "/rest/v1/rpc/list_secure_credentials"
            response = self.supabase._make_request("POST", endpoint, {}, use_service_role=True)
            
            if response.get("status") == "success":
                credentials = response.get("data", [])
                logger.info(f"[SECURE-CREDS] ✅ Listed {len(credentials)} credentials")
                return {
                    "status": "success",
                    "data": credentials,
                    "count": len(credentials)
                }
            else:
                logger.error(f"[SECURE-CREDS] ❌ Failed to list credentials: {response.get('message')}")
                return {
                    "status": "error",
                    "message": response.get("message", "Unknown error")
                }
                
        except Exception as e:
            logger.error(f"[SECURE-CREDS] ❌ Exception listing credentials: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def delete_credential(self, key: str) -> Dict[str, Any]:
        """Hapus kredensial (soft delete)"""
        try:
            endpoint = "/rest/v1/rpc/delete_secure_credential"
            data = {"p_key": key}
            
            response = self.supabase._make_request("POST", endpoint, data, use_service_role=True)
            
            if response.get("status") == "success":
                logger.info(f"[SECURE-CREDS] ✅ Deleted credential: {key}")
                return {
                    "status": "success",
                    "message": f"Credential '{key}' deleted",
                    "key": key
                }
            else:
                logger.error(f"[SECURE-CREDS] ❌ Failed to delete {key}: {response.get('message')}")
                return {
                    "status": "error",
                    "message": response.get("message", "Unknown error"),
                    "key": key
                }
                
        except Exception as e:
            logger.error(f"[SECURE-CREDS] ❌ Exception deleting {key}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "key": key
            }
    
    def migrate_env_to_supabase(self, env_file_path: str = ".env") -> Dict[str, Any]:
        """
        Migrasi kredensial dari file .env ke Supabase
        
        Args:
            env_file_path: Path ke file .env
        """
        try:
            env_path = Path(env_file_path)
            if not env_path.exists():
                return {
                    "status": "error",
                    "message": f"File .env tidak ditemukan: {env_file_path}"
                }
            
            # Daftar kredensial penting yang perlu diamankan
            important_credentials = {
                "SUPABASE_ANON_KEY": "database",
                "SUPABASE_SERVICE_ROLE_KEY": "database", 
                "GOOGLE_OAUTH_CLIENT_ID": "oauth",
                "GOOGLE_OAUTH_CLIENT_SECRET": "oauth",
                "STRIPE_SECRET_KEY": "payment",
                "STRIPE_PUBLISHABLE_KEY": "payment",
                "IPAYMU_API_KEY": "payment",
                "OPENAI_API_KEY": "api_key",
                "GOOGLE_CLOUD_API_KEY": "api_key",
                "JWT_SECRET": "security",
                "ENCRYPTION_KEY": "security"
            }
            
            # Baca file .env
            env_vars = {}
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
            
            # Migrasi kredensial penting
            migrated = []
            skipped = []
            errors = []
            
            for key, cred_type in important_credentials.items():
                if key in env_vars:
                    value = env_vars[key]
                    
                    # Skip jika masih placeholder
                    if value.startswith('your_') and value.endswith('_here'):
                        skipped.append(f"{key} (placeholder)")
                        continue
                    
                    # Store di Supabase
                    result = self.store_credential(
                        key=key,
                        value=value,
                        credential_type=cred_type,
                        description=f"Migrated from .env - {cred_type} credential"
                    )
                    
                    if result.get("status") == "success":
                        migrated.append(key)
                    else:
                        errors.append(f"{key}: {result.get('message')}")
                else:
                    skipped.append(f"{key} (not found)")
            
            logger.info(f"[SECURE-CREDS] Migration completed: {len(migrated)} migrated, {len(skipped)} skipped, {len(errors)} errors")
            
            return {
                "status": "success",
                "migrated": migrated,
                "skipped": skipped,
                "errors": errors,
                "summary": f"Migrated {len(migrated)} credentials to Supabase"
            }
            
        except Exception as e:
            logger.error(f"[SECURE-CREDS] ❌ Migration failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_credential_value(self, key: str, fallback: str = None) -> Optional[str]:
        """
        Helper method untuk mendapatkan nilai kredensial dengan fallback
        
        Args:
            key: Nama kredensial
            fallback: Nilai fallback jika kredensial tidak ditemukan
            
        Returns:
            Nilai kredensial atau fallback
        """
        result = self.get_credential(key)
        if result.get("status") == "success":
            return result.get("value")
        
        # Fallback ke environment variable
        env_value = os.environ.get(key, fallback)
        if env_value and not (env_value.startswith('your_') and env_value.endswith('_here')):
            return env_value
            
        return fallback
    
    def setup_environment_from_supabase(self) -> Dict[str, Any]:
        """
        Setup environment variables dari kredensial Supabase
        Berguna untuk aplikasi yang masih menggunakan os.environ
        """
        try:
            credentials_result = self.list_credentials()
            if credentials_result.get("status") != "success":
                return credentials_result
            
            credentials = credentials_result.get("data", [])
            loaded = []
            errors = []
            
            for cred in credentials:
                key = cred.get("key")
                if key:
                    result = self.get_credential(key)
                    if result.get("status") == "success":
                        value = result.get("value")
                        os.environ[key] = value
                        loaded.append(key)
                    else:
                        errors.append(f"{key}: {result.get('message')}")
            
            logger.info(f"[SECURE-CREDS] Environment setup: {len(loaded)} variables loaded")
            
            return {
                "status": "success",
                "loaded": loaded,
                "errors": errors,
                "summary": f"Loaded {len(loaded)} environment variables from Supabase"
            }
            
        except Exception as e:
            logger.error(f"[SECURE-CREDS] ❌ Environment setup failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

# Global instance
secure_credentials = SecureCredentialsManager()

# Helper functions untuk kemudahan penggunaan
def store_credential(key: str, value: str, credential_type: str, description: str = None) -> Dict[str, Any]:
    """Store credential securely in Supabase"""
    return secure_credentials.store_credential(key, value, credential_type, description)

def get_credential(key: str) -> Dict[str, Any]:
    """Get credential from Supabase"""
    return secure_credentials.get_credential(key)

def get_credential_value(key: str, fallback: str = None) -> Optional[str]:
    """Get credential value with fallback"""
    return secure_credentials.get_credential_value(key, fallback)

def migrate_env_to_supabase(env_file_path: str = ".env") -> Dict[str, Any]:
    """Migrate .env credentials to Supabase"""
    return secure_credentials.migrate_env_to_supabase(env_file_path)

def setup_environment_from_supabase() -> Dict[str, Any]:
    """Setup environment variables from Supabase"""
    return secure_credentials.setup_environment_from_supabase()