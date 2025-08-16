import os
import json
import time
import requests
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Import ConfigManager - server butuh akses user data juga  
from modules_client.config_manager import ConfigManager

# ✅ SUPABASE-ONLY MODE DETECTION
def _is_supabase_only_mode() -> bool:
    """Check if system should use Supabase-only mode (no VPS calls)"""
    try:
        supabase_config = Path("config/supabase_config.json")
        if supabase_config.exists():
            return True
        return False
    except:
        return False

# PRODUCTION MODE CHECK
import sys

def _is_production_mode():
    """Check if running in production (EXE) mode - FORCE VPS validation"""
    # ENHANCED: Multiple detection methods
    is_exe = getattr(sys, 'frozen', False)  # PyInstaller
    is_bundled = hasattr(sys, '_MEIPASS')   # Bundle detection
    no_source = not Path(__file__).parent.parent.joinpath('main.py').exists()  # Source check
    
    production_mode = is_exe or is_bundled or no_source
    
    if production_mode:
        print("[PRODUCTION] 🚀 EXE Mode Detected - FORCE VPS server validation ONLY")
        print("[PRODUCTION] ❌ Local subscription files DISABLED")
        print("[PRODUCTION] 🌐 VPS Server: http://69.62.79.238:8000")
    
    return production_mode


PRODUCTION_MODE = _is_production_mode()
if PRODUCTION_MODE:
    print("[PRODUCTION] Server-only validation mode enabled")

# EXE CREDIT FIX - Pastikan tidak ada hardcode credit
def _check_exe_environment():
    """Check jika running dalam EXE"""
    return getattr(sys, 'frozen', False)

# FORCE PRODUCTION MODE - NO DEVELOPMENT MODE
FORCE_SERVER_VALIDATION = True
DISABLE_LOCAL_CACHE = True
DEFAULT_CREDIT = 0.0  # Tidak ada kredit default

class LicenseValidator:
    def __init__(self, server_url="https://streammateai.com/api/license", testing_mode=False):
        self.cfg = ConfigManager("config/settings.json")
        self.server_url = server_url
        self.testing_mode = testing_mode  # Ini yang penting!
        self.last_refresh = 0
        self.cache_path = Path("temp/license_cache.json")
        self.cache_path.parent.mkdir(exist_ok=True)
        
        # TAMBAHAN: Set default cache untuk test mode
        if self.testing_mode:
            self._write_cache({
                "is_valid": True,
                "tier": "pro",
                "expire_date": "2099-12-31T23:59:59",  # Far future
                "daily_usage": {},
                "last_check": time.time()
            })

    def _is_dev_user(self):
        """PRODUCTION MODE: No developer users allowed"""
        # Always return False in production mode
        return False

    def _read_cache(self):
        """Baca cache lisensi dari file."""
        try:
            if self.cache_path.exists():
                return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[DEBUG] Gagal baca cache: {e}")
        return {}

    def _write_cache(self, data):
        """Tulis cache lisensi ke file."""
        try:
            self.cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[DEBUG] Gagal tulis cache: {e}")

    def _local_validation(self):
        """Validasi lisensi dari file lokal (fallback)."""
        try:
            local_path = Path("config/subscription_status.json")
            if local_path.exists():
                data = json.loads(local_path.read_text(encoding="utf-8"))
                expire_str = data.get("expired_at")
                if expire_str:
                    expire_date = datetime.fromisoformat(expire_str)
                    is_valid = expire_date > datetime.now()
                    return {
                        "is_valid": is_valid,
                        "tier": data.get("tier", "demo"),
                        "expire_date": expire_str,
                        "daily_usage": data.get("daily_usage", {}),
                        "last_check": time.time()
                    }
        except Exception as e:
            print(f"[DEBUG] Fallback validation error: {e}")
        
        # Default data jika tidak ada file
        return {
            "is_valid": False,
            "tier": "demo",
            "expire_date": None,
            "daily_usage": {},
            "last_check": time.time()
        }

    def _generate_hardware_id(self):
        """Generate hardware ID unik untuk client."""
        try:
            import uuid
            # Get machine-specific identifiers
            mac = uuid.getnode()
            # Combine with additional system info
            hw_string = f"{mac}-{os.name}-{os.getenv('USERNAME', '')}"
            # Create hash
            return hashlib.md5(hw_string.encode()).hexdigest()
        except Exception:
            # Fallback to random UUID if hardware ID generation fails
            return str(uuid.uuid4())

    def clear_all_caches_for_logout(self):
        """CLEAR ALL CACHES saat logout - untuk mengatasi bug EXE cache persistence"""
        print("[LOGOUT] Clearing ALL caches and session data...")
        
        try:
            # 1. Clear license cache file
            if self.cache_path.exists():
                self.cache_path.unlink()
                print(f"  [CLEAR] License cache: {self.cache_path}")
            
            # 2. Clear subscription status file
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                subscription_file.unlink()
                print(f"  [CLEAR] Subscription status: {subscription_file}")
            
            # 3. Clear temp session files
            temp_files = [
                "temp/license_cache.json",
                "temp/current_session.json",
                "temp/daily_usage.json",
                "temp/last_sync.json",
                "temp/vps_cache.json",
                "temp/user_session.json",
                "temp/last_logout_email.txt"
            ]
            
            for temp_file in temp_files:
                temp_path = Path(temp_file)
                if temp_path.exists():
                    temp_path.unlink()
                    print(f"  [CLEAR] Temp file: {temp_file}")
            
            # 4. Clear config files that might cache data
            config_files = [
                "config/current_user.json",
                "config/session_cache.json"
            ]
            
            for config_file in config_files:
                config_path = Path(config_file)
                if config_path.exists():
                    config_path.unlink()
                    print(f"  [CLEAR] Config file: {config_file}")
            
            # 5. Clear any in-memory caches
            if hasattr(self, '_cached_validation'):
                delattr(self, '_cached_validation')
                print(f"  [CLEAR] In-memory validation cache")
            
            if hasattr(self, '_last_vps_response'):
                delattr(self, '_last_vps_response')
                print(f"  [CLEAR] VPS response cache")
            
            if hasattr(self, '_last_sync_data'):
                delattr(self, '_last_sync_data')
                print(f"  [CLEAR] Last sync data cache")
            
            # 6. Reset instance variables
            self.last_refresh = 0
            
            # 7. Clear config manager cache
            try:
                if hasattr(self.cfg, '_cache'):
                    self.cfg._cache = {}
                    print(f"  [CLEAR] Config manager cache")
            except:
                pass
            
            # 8. Create logout marker file to prevent stale data reads
            self._create_logout_marker()
            
            print("[LOGOUT] All caches cleared successfully!")
            
        except Exception as e:
            print(f"[LOGOUT-ERROR] Failed to clear caches: {e}")
            import traceback
            traceback.print_exc()

    def _create_logout_marker(self):
        """Buat file penanda logout untuk mencegah data basi saat startup cepat"""
        try:
            marker_path = Path("temp/logout_marker.json")
            marker_path.parent.mkdir(exist_ok=True)
            marker_path.write_text(json.dumps({"logout_at": datetime.now().isoformat()}), encoding="utf-8")
            print("[LOGOUT] Created logout marker.")
        except Exception as e:
            print(f"[LOGOUT-ERROR] Could not create logout marker: {e}")

    def _remove_logout_marker(self):
        """Hapus file penanda logout setelah data sinkron."""
        try:
            marker_path = Path("temp/logout_marker.json")
            if marker_path.exists():
                marker_path.unlink()
                print("[LOGIN] Removed logout marker.")
        except Exception as e:
            print(f"[LOGIN-ERROR] Could not remove logout marker: {e}")
    
    def _create_logout_marker(self):
        """Create logout marker to prevent stale cache reads"""
        
        # Empty subscription status with logout marker
        empty_subscription = {
            "email": "",
            "status": "logged_out",
            "package": "none",
            "hours_credit": 0.0,
            "hours_used": 0.0,
            "tier": "none",
            "is_valid": False,
            "expire_date": None,
            "logout_timestamp": datetime.now().isoformat(),
            "cleared_for_logout": True,
            "session_invalidated": True,
            "production_mode": PRODUCTION_MODE
        }
        
        subscription_file = Path("config/subscription_status.json")
        subscription_file.parent.mkdir(exist_ok=True)
        
        with open(subscription_file, 'w', encoding='utf-8') as f:
            json.dump(empty_subscription, f, indent=2, ensure_ascii=False)
        
        print(f"  [CREATE] Logout marker created")
        
        # Empty license cache
        empty_cache = {
            "is_valid": False,
            "tier": "none",
            "logout_cleared": True,
            "session_invalidated": True,
            "last_check": 0
        }
        
        self.cache_path.parent.mkdir(exist_ok=True)
        self._write_cache(empty_cache)
        print(f"  [CREATE] Empty license cache created")

    def validate(self, force_refresh=False):
        """Validasi lisensi dengan logika demo-aware yang lebih baik."""
        print(f"[LICENSE] Validating... (Force refresh: {force_refresh})")
        email = self.cfg.get("user_data", {}).get("email", "")
        
        # PERBAIKAN: Coba ambil email dari subscription file jika tidak ada di config
        if not email:
            try:
                subscription_file = Path("config/subscription_status.json")
                if subscription_file.exists():
                    with open(subscription_file, 'r', encoding='utf-8') as f:
                        sub_data = json.load(f)
                    email = sub_data.get("email", "")
                    if email:
                        print(f"[LICENSE] Email found in subscription file: {email}")
            except Exception as e:
                print(f"[LICENSE] Error reading subscription file for email: {e}")
        
        if not email:
            print("[LICENSE] Error: No email found for validation.")
            return {"is_valid": False, "tier": "none", "message": "Email tidak ditemukan"}

        # --- PERBAIKAN INTI ADA DI SINI ---
        # 1. Cek status demo LOKAL terlebih dahulu sebelum ke server.
        try:
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                sub_data = json.loads(subscription_file.read_text(encoding="utf-8"))
                if sub_data.get("status") == "demo":
                    expire_str = sub_data.get("expire_date")
                    if expire_str:
                        expire_date = datetime.fromisoformat(expire_str)
                        # Beri sedikit toleransi waktu
                        if datetime.now(timezone.utc) < expire_date + timedelta(seconds=10):
                            print("[LICENSE] Demo mode is active. Skipping server validation to protect demo session.")
                            return {
                                "is_valid": True,
                                "tier": "basic",
                                "source": "demo_active",
                                "message": "Demo mode sedang aktif.",
                                "demo_remaining": int((expire_date - datetime.now(timezone.utc)).total_seconds() / 60)
                            }
        except Exception as e:
            print(f"[LICENSE] Error checking local demo status, proceeding with validation: {e}")
        # --- AKHIR DARI BLOK PERBAIKAN ---

        # 2. Lanjutkan ke validasi server jika demo tidak aktif.
        print(f"[LICENSE] Validating {email} with Supabase server...")
        
        # Try Supabase first
        try:
            from modules_client.supabase_client import get_supabase_client
            supabase_client = get_supabase_client()
            
            hardware_id = self._generate_hardware_id()
            supabase_data = supabase_client.validate_license(email, hardware_id)
            
            if supabase_data.get("status") == "success":
                print(f"[LICENSE] Supabase response: {supabase_data}")
                
                # Sinkronkan data dari Supabase ke file lokal
                self._sync_supabase_to_subscription_file(supabase_data, email)
                self._remove_logout_marker() # Hapus marker setelah sync berhasil
                
                # Kembalikan hasil dari data Supabase yang sudah disinkronkan
                supabase_data['source'] = 'supabase_server'
                return supabase_data
            else:
                print(f"[LICENSE] Supabase error: {supabase_data.get('message')}")
                
        except Exception as e:
            print(f"[LICENSE] Supabase validation failed: {e}")
        
        # Fallback to VPS server - SKIP IN SUPABASE-ONLY MODE
        if not _is_supabase_only_mode():
            print(f"[LICENSE] Fallback to VPS server...")
            vps_url = "http://69.62.79.238:8000/api/license/validate"
            hardware_id = self._generate_hardware_id()
            payload = {"email": email, "hardware_id": hardware_id}

            try:
                response = requests.post(vps_url, json=payload, timeout=10)
                if response.status_code == 200:
                    vps_data = response.json()
                    print(f"[LICENSE] VPS response: {vps_data}")
                    
                    # Sinkronkan data dari VPS ke file lokal
                    self._sync_vps_to_subscription_file(vps_data, email)
                    self._remove_logout_marker() # Hapus marker setelah sync berhasil
                    
                    # Kembalikan hasil dari data VPS yang sudah disinkronkan
                    vps_data['source'] = 'vps_server'
                    return vps_data
                else:
                    print(f"[LICENSE] VPS error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"[LICENSE] Cannot connect to license server: {e}")
            except Exception as e:
                print(f"[LICENSE] An unexpected error occurred: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"✅ Supabase-only mode: Skipping VPS license validation fallback")

    def _sync_supabase_to_subscription_file(self, supabase_data, email):
        """
        Sinkronkan data dari Supabase ke file subscription lokal.
        """
        try:
            # Akses data dari dalam kunci 'data' yang benar dari respons Supabase
            license_info = supabase_data.get('data', supabase_data)

            # Ambil nilai dengan aman menggunakan .get()
            credit_balance = float(license_info.get('credit_balance', license_info.get('hours_credit', 0.0)))
            credit_used = float(license_info.get('credit_used', license_info.get('hours_used', 0.0)))
            is_active = license_info.get('is_active', False)
            tier = license_info.get('tier', 'none')
            expire_date = license_info.get('expire_date')

            # Log untuk debugging
            print(f"[SYNC] Processing Supabase data: is_active='{is_active}', Credits={credit_balance}, Used={credit_used}")

            subscription_file = Path("config/subscription_status.json")
            
            # Buat data baru untuk disimpan
            new_sub_data = {
                "email": email,
                "status": "active" if is_active else "inactive",
                "package": tier,
                "credit_balance": credit_balance,
                "credit_used": credit_used,
                "hours_credit": credit_balance,     # Untuk legacy compatibility
                "hours_used": credit_used,          # Untuk legacy compatibility
                "tier": tier,
                "is_valid": is_active,
                "expire_date": expire_date,
                "synced_from_supabase": True,
                "supabase_source_only": True,
                "last_sync": datetime.now(timezone.utc).isoformat(),
            }
            
            subscription_file.write_text(
                json.dumps(new_sub_data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            
            print(f"[SYNC] ✅ Successfully synced Supabase data to local file. Credits are now: {credit_balance}")
            
        except Exception as e:
            print(f"[SYNC] ❌ Error syncing Supabase data: {e}")

    def _sync_vps_to_subscription_file(self, vps_data, email):
        """
        FIXED: Sinkronkan data dari VPS ke file subscription lokal dengan benar.
        Ini memperbaiki bug di mana kredit menjadi 0 setelah pembelian.
        """
        try:
            # --- PERBAIKAN INTI ADA DI SINI ---
            # 1. Akses data dari dalam kunci 'data' yang benar dari respons server.
            license_info = vps_data.get('data', vps_data)

            # 2. Ambil nilai dengan aman menggunakan .get() FIELD BARU
            credit_balance = float(license_info.get('credit_balance', license_info.get('hours_credit', 0.0)))
            credit_used = float(license_info.get('credit_used', license_info.get('hours_used', 0.0)))
            is_active = license_info.get('is_active', False)
            tier = license_info.get('tier', 'none')
            expire_date = license_info.get('expire_date')

            # Log untuk debugging yang lebih jelas
            print(f"[SYNC] Processing server data: is_active='{is_active}', Credits={credit_balance}, Used={credit_used}")

            subscription_file = Path("config/subscription_status.json")
            
            # Buat data baru untuk disimpan
            new_sub_data = {
                "email": email,
                "status": "active" if is_active else "inactive",
                "package": tier,
                "credit_balance": credit_balance,   # FIELD BARU
                "credit_used": credit_used,         # FIELD BARU
                "hours_credit": credit_balance,     # Untuk legacy compatibility
                "hours_used": credit_used,          # Untuk legacy compatibility
                "tier": tier,
                "is_valid": is_active,
                "expire_date": expire_date,
                "synced_from_vps": True,
                "vps_source_only": True,
                "last_sync": datetime.now(timezone.utc).isoformat(),
            }
            
            subscription_file.write_text(
                json.dumps(new_sub_data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            
            print(f"[SYNC] ✅ Successfully synced server data to local file. Credits are now: {credit_balance}")

        except Exception as e:
            print(f"[SYNC-ERROR] Failed to sync VPS data to local file: {e}")
            import traceback
            traceback.print_exc()

    def track_usage(self, minutes=1):
        """Track usage minutes and update to server."""
        if self.testing_mode:
            return  # Skip tracking untuk testing mode
            
        def send_usage():
            try:
                user_data = self.cfg.get("user_data", {})
                email = user_data.get("email", "")
                if not email:
                    return
                
                # Send to VPS server
                requests.post(
                    f"{self.server_url}/track_usage",
                    json={"email": email, "minutes": minutes},
                    timeout=10
                )
            except Exception as e:
                print(f"[DEBUG] Error tracking usage: {e}")
        
        # Send in background thread to avoid blocking
        import threading
        threading.Thread(target=send_usage, daemon=True).start()

    def get_today_usage(self):
        """Get today's usage statistics."""
        try:
            user_data = self.cfg.get("user_data", {})
            email = user_data.get("email", "")
            if not email:
                return {"used_hours": 0, "limit_hours": 5}
            
            response = requests.get(
                f"{self.server_url}/usage/{email}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"used_hours": 0, "limit_hours": 5}
                
        except Exception as e:
            print(f"[DEBUG] Error getting usage: {e}")
            return {"used_hours": 0, "limit_hours": 5}

    def _is_logout_cleared(self):
        """Check if cache was cleared due to logout"""
        try:
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                with open(subscription_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    is_logout = (data.get("cleared_for_logout", False) or 
                               data.get("status") == "logged_out" or
                               data.get("session_invalidated", False))
                    if is_logout:
                        print(f"[LOGOUT-DETECT] Logout state detected in subscription file")
                    return is_logout
        except:
            pass
        return False