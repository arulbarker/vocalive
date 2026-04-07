#!/usr/bin/env python3
"""
VocaLive - License Manager (AppScript Edition)
Validasi lisensi via email + Google AppScript — tanpa service account key.
"""

import os
import sys
import json
import hashlib
import platform
import uuid
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging

# Encryption imports
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
except ImportError:
    print("Missing cryptography library. Install: pip install cryptography")
    sys.exit(1)

import requests
import time

# ============================================================
# KONFIGURASI — Update URL saat deploy AppScript baru
# ============================================================
APPSCRIPT_URL = "https://script.google.com/macros/s/PASTE_APPSCRIPT_DEPLOYMENT_URL_HERE/exec"
APP_SECRET = "TKD-2025-s3cr3t-k3y-9xKm2pQr7nVw4L"
PRODUCT_ID = "vocalive"
REQUEST_TIMEOUT = 15  # detik
# ============================================================


class LicenseManager:
    """License Manager berbasis email + AppScript HTTP endpoint."""

    def __init__(self, root_dir: str = None):
        if root_dir:
            self.root_dir = root_dir
        else:
            if getattr(sys, 'frozen', False):
                self.root_dir = os.path.dirname(sys.executable)
            else:
                self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.config_dir = Path(self.root_dir) / "config"
        self.config_dir.mkdir(exist_ok=True)

        self.license_file_path = self.config_dir / "license.enc"
        self.device_hash_path = self.config_dir / "device.hash"

        self.logger = logging.getLogger('LicenseManager')
        self.logger.setLevel(logging.INFO)

        self._device_id = None
        self._encryption_key = None

        # Baca URL override dari config jika ada
        self._load_url_override()

    def _load_url_override(self):
        """Izinkan override URL via config/license_config.json."""
        try:
            cfg_path = self.config_dir / "license_config.json"
            if cfg_path.exists():
                with open(cfg_path, 'r') as f:
                    cfg = json.load(f)
                global APPSCRIPT_URL, APP_SECRET
                if cfg.get("appscript_url"):
                    APPSCRIPT_URL = cfg["appscript_url"]
                if cfg.get("app_secret"):
                    APP_SECRET = cfg["app_secret"]
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Device fingerprint (tetap sama seperti versi lama)
    # ------------------------------------------------------------------

    def _get_device_fingerprint(self) -> str:
        if self._device_id:
            return self._device_id
        try:
            system_info = []
            try:
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                for elements in range(0, 2 * 6, 2)][::-1])
                system_info.append(f"MAC:{mac}")
            except Exception:
                system_info.append("MAC:unknown")

            try:
                if platform.system() == "Windows":
                    cpu_info = subprocess.check_output(
                        "wmic cpu get ProcessorId /value",
                        shell=True, text=True, timeout=5
                    ).strip()
                    cpu_id = [line.split('=')[1] for line in cpu_info.split('\n')
                              if 'ProcessorId=' in line]
                    system_info.append(f"CPU:{cpu_id[0].strip()}" if cpu_id else f"CPU:{platform.processor()}")
                else:
                    system_info.append(f"CPU:{platform.processor()}")
            except Exception:
                system_info.append(f"CPU:{platform.machine()}")

            try:
                if platform.system() == "Windows":
                    disk_info = subprocess.check_output(
                        "wmic diskdrive get SerialNumber /value",
                        shell=True, text=True, timeout=5
                    ).strip()
                    disk_serial = [line.split('=')[1] for line in disk_info.split('\n')
                                   if 'SerialNumber=' in line and line.split('=')[1].strip()]
                    system_info.append(f"DISK:{disk_serial[0].strip()}" if disk_serial else f"DISK:{platform.node()}")
                else:
                    system_info.append(f"DISK:{platform.node()}")
            except Exception:
                system_info.append(f"DISK:{platform.node()}")

            system_info.append(f"OS:{platform.system()}_{platform.release()}")
            fingerprint_data = "|".join(system_info)
            self._device_id = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
            return self._device_id
        except Exception as e:
            self.logger.error(f"Error generating device fingerprint: {e}")
            fallback = f"{platform.node()}_{uuid.getnode()}"
            self._device_id = hashlib.md5(fallback.encode()).hexdigest()
            return self._device_id

    # ------------------------------------------------------------------
    # Enkripsi lokal (hardware-locked, sama seperti versi lama)
    # ------------------------------------------------------------------

    def _get_encryption_key(self) -> bytes:
        if self._encryption_key:
            return self._encryption_key
        device_id = self._get_device_fingerprint()
        password = f"StreamMateAI_{device_id}_License".encode()
        salt = b"StreamMateAI_Salt_2024"
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        self._encryption_key = base64.urlsafe_b64encode(kdf.derive(password))
        return self._encryption_key

    def _encrypt_data(self, data: str) -> str:
        fernet = Fernet(self._get_encryption_key())
        return base64.urlsafe_b64encode(fernet.encrypt(data.encode())).decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        try:
            fernet = Fernet(self._get_encryption_key())
            return fernet.decrypt(base64.urlsafe_b64decode(encrypted_data.encode())).decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt license data")

    # ------------------------------------------------------------------
    # AppScript HTTP helpers
    # ------------------------------------------------------------------

    def _call_appscript(self, params: dict) -> Optional[dict]:
        """Kirim GET request ke AppScript dan kembalikan JSON response."""
        try:
            base_params = {
                "app_secret": APP_SECRET,
                "product": PRODUCT_ID,
            }
            base_params.update(params)
            resp = requests.get(APPSCRIPT_URL, params=base_params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            self.logger.error("AppScript request timed out")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.error("Cannot reach AppScript — no internet?")
            return None
        except Exception as e:
            self.logger.error(f"AppScript call error: {e}")
            return None

    # ------------------------------------------------------------------
    # Public API — digunakan oleh main.py dan license_monitor.py
    # ------------------------------------------------------------------

    def validate_license_online(self, email: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Login email ke AppScript.
        Return: (is_valid, message, data)
        data keys: 'nama', 'email', 'expired_date' (opsional)
        """
        email = email.strip().lower()
        if not email or "@" not in email:
            return False, "Format email tidak valid", {}

        device_token = self._get_device_fingerprint()
        result = self._call_appscript({
            "action": "login",
            "email": email,
            "token": device_token,
        })

        if result is None:
            return False, "Tidak bisa terhubung ke server lisensi. Periksa koneksi internet.", {}

        if result.get("status") == "SUKSES":
            data = {
                "email": email,
                "nama": result.get("nama", ""),
                "expired_date": result.get("expired_date", ""),
                "maxDevices": result.get("maxDevices", 1),
            }
            self.logger.info(f"Login sukses: {email}")
            return True, "Login berhasil!", data
        else:
            msg = result.get("message", "Login gagal.")
            self.logger.warning(f"Login gagal [{email}]: {msg}")
            return False, msg, {}

    def check_session_online(self, email: str) -> Tuple[bool, str]:
        """
        Cek session aktif via AppScript (action=cek).
        Dipakai oleh license_monitor untuk validasi berkala.
        """
        device_token = self._get_device_fingerprint()
        result = self._call_appscript({
            "action": "cek",
            "email": email,
            "token": device_token,
        })

        if result is None:
            # Network error — jangan paksa logout, biarkan offline cache berlaku
            return True, "Offline — menggunakan cache lokal"

        if result.get("status") == "VALID":
            # Update expired_date di cache lokal jika server kirim yang baru
            new_exp = result.get("expired_date")
            if new_exp:
                self._update_cached_expiry(new_exp)
            return True, "Sesi valid"
        else:
            msg = result.get("message", "Sesi tidak valid.")
            return False, msg

    def logout_online(self, email: str) -> bool:
        """Kirim logout ke AppScript."""
        device_token = self._get_device_fingerprint()
        result = self._call_appscript({
            "action": "logout",
            "email": email,
            "token": device_token,
        })
        return result is not None and result.get("status") == "SUKSES"

    # ------------------------------------------------------------------
    # Local session cache
    # ------------------------------------------------------------------

    def save_license_data(self, email: str, license_data: Dict[str, Any]) -> bool:
        """Simpan data sesi terenkripsi ke disk."""
        try:
            session_info = {
                "email": email.strip().lower(),
                "nama": license_data.get("nama", ""),
                "device_id": self._get_device_fingerprint(),
                "validated_at": datetime.now().isoformat(),
                "expired_date": license_data.get("expired_date", ""),
                "status": "AKTIF",
            }
            encrypted = self._encrypt_data(json.dumps(session_info))
            with open(self.license_file_path, 'w', encoding='utf-8') as f:
                json.dump({"data": encrypted, "created": datetime.now().isoformat()}, f, indent=2)

            # Simpan device hash
            device_hash = hashlib.sha256(self._get_device_fingerprint().encode()).hexdigest()
            with open(self.device_hash_path, 'w', encoding='utf-8') as f:
                json.dump({"device_hash": device_hash, "created": datetime.now().isoformat()}, f, indent=2)

            self.logger.info("Session data saved")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
            return False

    def load_license_data(self) -> Optional[Dict[str, Any]]:
        """Load dan decrypt data sesi lokal."""
        try:
            if not self.license_file_path.exists():
                return None
            with open(self.license_file_path, 'r', encoding='utf-8') as f:
                enc_file = json.load(f)
            encrypted = enc_file.get('data')
            if not encrypted:
                return None
            session = json.loads(self._decrypt_data(encrypted))

            # Verifikasi device fingerprint
            if session.get('device_id') != self._get_device_fingerprint():
                self.logger.warning("Device ID mismatch in stored session")
                return None
            return session
        except Exception as e:
            self.logger.error(f"Failed to load session: {e}")
            return None

    def _update_cached_expiry(self, new_expired_date: str):
        """Update expired_date di cache lokal tanpa mengubah field lain."""
        try:
            session = self.load_license_data()
            if session:
                session["expired_date"] = new_expired_date
                encrypted = self._encrypt_data(json.dumps(session))
                with open(self.license_file_path, 'r') as f:
                    enc_file = json.load(f)
                enc_file["data"] = encrypted
                with open(self.license_file_path, 'w', encoding='utf-8') as f:
                    json.dump(enc_file, f, indent=2)
        except Exception:
            pass

    def is_license_valid(self, force_online_check=False) -> Tuple[bool, str]:
        """
        Cek apakah sesi lokal valid.
        force_online_check=True → cek tambahan ke AppScript.
        """
        try:
            session = self.load_license_data()
            if not session:
                return False, "Belum login. Silakan masukkan email pembelian."

            # Cek expired_date lokal
            expired_str = session.get("expired_date", "").strip()
            if expired_str:
                try:
                    for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"]:
                        try:
                            exp_date = datetime.strptime(expired_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        exp_date = None
                    if exp_date and datetime.now() > exp_date:
                        self.clear_license_data()
                        return False, f"Masa aktif berlangganan habis pada {expired_str}. Silakan perpanjang."
                except Exception:
                    pass

            # Online check jika diminta
            if force_online_check:
                email = session.get("email", "")
                if email:
                    is_valid, message = self.check_session_online(email)
                    if not is_valid:
                        self.logger.warning(f"Online session check gagal: {message}")
                        self.clear_license_data()
                        return False, message

            return True, "Lisensi valid"

        except Exception as e:
            self.logger.error(f"License check error: {e}")
            return False, f"Error: {str(e)}"

    def clear_license_data(self) -> bool:
        """Hapus data sesi lokal (logout lokal)."""
        try:
            if self.license_file_path.exists():
                os.remove(self.license_file_path)
            if self.device_hash_path.exists():
                os.remove(self.device_hash_path)
            self.logger.info("Session data cleared")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear session: {e}")
            return False

    def get_license_info(self) -> Dict[str, Any]:
        """Info lisensi untuk ditampilkan di UI / monitor."""
        session = self.load_license_data()
        if not session:
            return {}

        info = {
            "email": session.get("email", ""),
            "nama": session.get("nama", ""),
            "status": session.get("status", ""),
            "expired_date": session.get("expired_date", ""),
            "validated_at": session.get("validated_at", ""),
            # Compat lama
            "license_key": session.get("email", ""),
            "notes": "",
        }

        expired_str = info.get("expired_date", "").strip()
        if not expired_str:
            info["days_remaining"] = -1
            info["is_expired"] = False
            info["is_unlimited"] = True
        else:
            try:
                exp_date = None
                for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"]:
                    try:
                        exp_date = datetime.strptime(expired_str, fmt)
                        break
                    except ValueError:
                        continue
                if exp_date:
                    days = (exp_date - datetime.now()).days
                    info["days_remaining"] = max(0, days)
                    info["is_expired"] = days < 0
                    info["is_unlimited"] = False
                else:
                    info["days_remaining"] = -1
                    info["is_expired"] = False
                    info["is_unlimited"] = True
            except Exception:
                info["days_remaining"] = -1
                info["is_expired"] = False
                info["is_unlimited"] = True

        return info
