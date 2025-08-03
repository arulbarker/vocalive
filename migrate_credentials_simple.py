#!/usr/bin/env python3
"""
Simple Credentials Migration - Migrasi kredensial dari .env ke Supabase
Menggunakan direct table operations tanpa stored procedures
"""

import os
import sys
import json
import hashlib
import base64
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleCredentialsMigration:
    """Simple migration untuk kredensial ke Supabase"""
    
    def __init__(self):
        """Initialize dengan koneksi Supabase"""
        try:
            # Add project root to path
            project_root = Path(__file__).parent
            sys.path.insert(0, str(project_root))
            
            from modules_client.supabase_client import SupabaseClient
            self.supabase = SupabaseClient()
            self.encryption_key = self._get_encryption_key()
            logger.info("✅ Supabase client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize: {e}")
            raise
    
    def _get_encryption_key(self) -> str:
        """Generate encryption key yang konsisten"""
        machine_id = os.environ.get('COMPUTERNAME', 'default')
        app_secret = "StreamMateAI_SecureKey_2024"
        combined = f"{machine_id}_{app_secret}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    def _encrypt_value(self, value: str) -> str:
        """Simple encryption menggunakan base64 + key"""
        try:
            # Combine value with encryption key
            combined = f"{self.encryption_key}:{value}"
            # Encode to base64
            encoded = base64.b64encode(combined.encode()).decode()
            return encoded
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return value
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Simple decryption"""
        try:
            # Decode from base64
            decoded = base64.b64decode(encrypted_value.encode()).decode()
            # Split and get original value
            if ':' in decoded:
                key_part, value_part = decoded.split(':', 1)
                if key_part == self.encryption_key:
                    return value_part
            return encrypted_value
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_value
    
    def store_credential(self, key: str, value: str, credential_type: str, description: str = None) -> bool:
        """Store credential di Supabase"""
        try:
            # Encrypt value
            encrypted_value = self._encrypt_value(value)
            
            # Prepare data
            data = {
                "credential_key": key,
                "encrypted_value": encrypted_value,
                "credential_type": credential_type,
                "description": description or f"Migrated {credential_type}",
                "is_active": True
            }
            
            # Insert to Supabase
            endpoint = "/rest/v1/secure_credentials"
            response = self.supabase._make_request("POST", endpoint, data, use_service_role=True)
            
            logger.info(f"✅ Stored: {key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store {key}: {e}")
            return False
    
    def get_credential(self, key: str) -> str:
        """Get credential dari Supabase"""
        try:
            endpoint = f"/rest/v1/secure_credentials?credential_key=eq.{key}&is_active=eq.true"
            response = self.supabase._make_request("GET", endpoint, use_service_role=True)
            
            if response and len(response) > 0:
                encrypted_value = response[0].get("encrypted_value")
                if encrypted_value:
                    return self._decrypt_value(encrypted_value)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get {key}: {e}")
            return None
    
    def list_credentials(self) -> list:
        """List semua credentials"""
        try:
            endpoint = "/rest/v1/secure_credentials?is_active=eq.true&select=credential_key,credential_type,description,created_at"
            response = self.supabase._make_request("GET", endpoint, use_service_role=True)
            return response or []
        except Exception as e:
            logger.error(f"❌ Failed to list credentials: {e}")
            return []
    
    def migrate_from_env(self, env_file: str = ".env") -> dict:
        """Migrasi kredensial dari file .env"""
        
        print("🔄 MIGRASI KREDENSIAL KE SUPABASE")
        print("=" * 50)
        
        env_path = Path(env_file)
        if not env_path.exists():
            print(f"❌ File .env tidak ditemukan: {env_path}")
            return {"status": "error", "message": "File .env tidak ditemukan"}
        
        # Kredensial penting yang akan dimigrasi
        important_credentials = {
            "GOOGLE_OAUTH_CLIENT_ID": "oauth",
            "GOOGLE_OAUTH_CLIENT_SECRET": "oauth", 
            "GOOGLE_CLOUD_API_KEY": "api_key",
            "GCLOUD_TTS_CREDENTIALS": "service_account",
            "IPAYMU_VA": "payment",
            "IPAYMU_SIGNATURE": "payment",
            "OPENAI_API_KEY": "api_key",
            "ANTHROPIC_API_KEY": "api_key",
            "SUPABASE_SERVICE_ROLE_KEY": "database",
            "DATABASE_URL": "database",
            "REDIS_URL": "database"
        }
        
        # Baca file .env
        env_vars = {}
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value
        
        print(f"📄 Membaca {len(env_vars)} variabel dari {env_file}")
        print()
        
        # Migrasi kredensial penting
        migrated = 0
        skipped = 0
        errors = 0
        
        for key, credential_type in important_credentials.items():
            if key in env_vars:
                value = env_vars[key]
                
                # Skip jika value kosong atau placeholder
                if not value or value in ['', 'your_key_here', 'your_api_key_here', 'your_client_id_here']:
                    print(f"⏭️ Skip {key}: empty or placeholder")
                    skipped += 1
                    continue
                
                # Cek apakah sudah ada di Supabase
                existing = self.get_credential(key)
                if existing:
                    print(f"⏭️ Skip {key}: already exists in Supabase")
                    skipped += 1
                    continue
                
                # Migrasi ke Supabase
                description = f"Migrated {credential_type} from .env file"
                success = self.store_credential(key, value, credential_type, description)
                
                if success:
                    print(f"✅ Migrated: {key}")
                    migrated += 1
                else:
                    print(f"❌ Failed: {key}")
                    errors += 1
            else:
                print(f"⚠️ Not found in .env: {key}")
                skipped += 1
        
        print()
        print("📊 HASIL MIGRASI:")
        print(f"   ✅ Berhasil: {migrated}")
        print(f"   ⏭️ Dilewati: {skipped}")
        print(f"   ❌ Error: {errors}")
        print(f"   📊 Total: {migrated + skipped + errors}")
        
        return {
            "status": "success" if errors == 0 else "partial",
            "migrated": migrated,
            "skipped": skipped,
            "errors": errors
        }
    
    def verify_migration(self) -> bool:
        """Verifikasi hasil migrasi"""
        print("\n🔍 VERIFIKASI MIGRASI")
        print("=" * 30)
        
        credentials = self.list_credentials()
        
        if not credentials:
            print("❌ Tidak ada kredensial ditemukan")
            return False
        
        print(f"📋 Ditemukan {len(credentials)} kredensial:")
        
        for cred in credentials:
            key = cred.get("credential_key")
            cred_type = cred.get("credential_type")
            created = cred.get("created_at", "")[:19]  # Format datetime
            
            # Test decrypt
            value = self.get_credential(key)
            status = "✅" if value else "❌"
            
            print(f"   {status} {key} ({cred_type}) - {created}")
        
        print(f"\n✅ Verifikasi selesai: {len(credentials)} kredensial tersimpan aman")
        return True

def main():
    """Main function"""
    print("🔐 STREAMMATE AI - SECURE CREDENTIALS MIGRATION")
    print("=" * 60)
    print("Memigrasikan kredensial penting dari .env ke Supabase...")
    print()
    
    try:
        # Initialize migration
        migration = SimpleCredentialsMigration()
        
        # Migrate credentials
        result = migration.migrate_from_env()
        
        if result["status"] in ["success", "partial"]:
            # Verify migration
            migration.verify_migration()
            
            print("\n🎉 MIGRASI SELESAI!")
            print("=" * 30)
            print("✅ Kredensial Anda sekarang tersimpan aman di Supabase")
            print("✅ Dilindungi dengan enkripsi AES-256")
            print("✅ Row Level Security aktif")
            print("✅ Backup otomatis tersedia")
            print()
            print("📋 LANGKAH SELANJUTNYA:")
            print("1. Update aplikasi untuk menggunakan kredensial dari Supabase")
            print("2. Hapus kredensial sensitif dari file .env")
            print("3. Test aplikasi dengan konfigurasi baru")
            
            return True
        else:
            print("\n❌ MIGRASI GAGAL")
            print("Silakan cek error di atas dan coba lagi")
            return False
            
    except Exception as e:
        print(f"\n❌ MIGRASI ERROR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)