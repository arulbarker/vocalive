#!/usr/bin/env python3
"""
VocaLive - License Manager
Secure license validation dengan Google Sheets integration
"""

import os
import sys
import json
import hashlib
import platform
import uuid
import socket
import subprocess
from datetime import datetime, timedelta
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

# Google Sheets imports
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("Missing Google Sheets libraries. Install: pip install gspread google-auth")
    sys.exit(1)

import requests
import time

class LicenseManager:
    """Secure License Manager dengan Google Sheets validation"""
    
    def __init__(self, root_dir: str = None):
        """Initialize License Manager"""
        if root_dir:
            self.root_dir = root_dir
        else:
            # Handle both regular Python and frozen EXE modes
            if getattr(sys, 'frozen', False):
                # Running as frozen EXE
                self.root_dir = os.path.dirname(sys.executable)
            else:
                # Running as regular Python script
                self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.config_dir = Path(self.root_dir) / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # File paths
        self.sheet_credentials_path = self.config_dir / "sheet.json"
        self.license_file_path = self.config_dir / "license.enc"
        self.device_hash_path = self.config_dir / "device.hash"
        
        # Google Sheets config
        self.sheet_id = "1KcYcRIOWGw-EQXa6zY8EfrQsVnKg_VTTF_sQyeDG-ss"
        self.sheet_name = "Sheet1"  # Use actual worksheet name (tab name)
        
        # Setup logging
        self.logger = logging.getLogger('LicenseManager')
        self.logger.setLevel(logging.INFO)
        
        # Security settings
        self.max_retries = 3
        self.retry_delay = 2
        
        # Device fingerprint cache
        self._device_id = None
        self._encryption_key = None
    
    def _get_device_fingerprint(self) -> str:
        """Generate unique device fingerprint"""
        if self._device_id:
            return self._device_id
            
        try:
            # Collect system information
            system_info = []
            
            # MAC Address (primary network interface)
            try:
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                              for elements in range(0, 2*6, 2)][::-1])
                system_info.append(f"MAC:{mac}")
            except Exception:
                system_info.append("MAC:unknown")
            
            # CPU information
            try:
                if platform.system() == "Windows":
                    cpu_info = subprocess.check_output(
                        "wmic cpu get ProcessorId /value", 
                        shell=True, text=True, timeout=5
                    ).strip()
                    cpu_id = [line.split('=')[1] for line in cpu_info.split('\n') 
                             if 'ProcessorId=' in line]
                    if cpu_id:
                        system_info.append(f"CPU:{cpu_id[0].strip()}")
                    else:
                        system_info.append(f"CPU:{platform.processor()}")
                else:
                    system_info.append(f"CPU:{platform.processor()}")
            except Exception:
                system_info.append(f"CPU:{platform.machine()}")
            
            # Disk serial (Windows only)
            try:
                if platform.system() == "Windows":
                    disk_info = subprocess.check_output(
                        "wmic diskdrive get SerialNumber /value", 
                        shell=True, text=True, timeout=5
                    ).strip()
                    disk_serial = [line.split('=')[1] for line in disk_info.split('\n') 
                                  if 'SerialNumber=' in line and line.split('=')[1].strip()]
                    if disk_serial:
                        system_info.append(f"DISK:{disk_serial[0].strip()}")
                    else:
                        system_info.append(f"DISK:{platform.node()}")
                else:
                    system_info.append(f"DISK:{platform.node()}")
            except Exception:
                system_info.append(f"DISK:{platform.node()}")
            
            # Platform info
            system_info.append(f"OS:{platform.system()}_{platform.release()}")
            
            # Create fingerprint
            fingerprint_data = "|".join(system_info)
            device_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
            
            self._device_id = device_hash[:32]  # First 32 chars
            
            self.logger.info(f"Generated device fingerprint: {self._device_id}")
            return self._device_id
            
        except Exception as e:
            self.logger.error(f"Error generating device fingerprint: {e}")
            # Fallback to node + MAC
            fallback = f"{platform.node()}_{uuid.getnode()}"
            self._device_id = hashlib.md5(fallback.encode()).hexdigest()
            return self._device_id
    
    def _get_encryption_key(self) -> bytes:
        """Generate encryption key from device fingerprint"""
        if self._encryption_key:
            return self._encryption_key
            
        device_id = self._get_device_fingerprint()
        password = f"StreamMateAI_{device_id}_License".encode()
        salt = b"StreamMateAI_Salt_2024"
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self._encryption_key = key
        return key
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        key = self._get_encryption_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt license data")
    
    def _save_device_hash(self) -> None:
        """Save device hash to file"""
        try:
            device_id = self._get_device_fingerprint()
            device_hash = hashlib.sha256(device_id.encode()).hexdigest()
            
            with open(self.device_hash_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "device_hash": device_hash,
                    "created": datetime.now().isoformat(),
                    "platform": platform.system()
                }, f, indent=2)
                
            self.logger.info("Device hash saved")
        except Exception as e:
            self.logger.error(f"Failed to save device hash: {e}")
    
    def _load_device_hash(self) -> Optional[str]:
        """Load device hash from file"""
        try:
            if not self.device_hash_path.exists():
                return None
                
            with open(self.device_hash_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("device_hash")
        except Exception as e:
            self.logger.error(f"Failed to load device hash: {e}")
            return None
    
    def _connect_to_sheets(self) -> gspread.Worksheet:
        """Connect to Google Sheets"""
        try:
            if not self.sheet_credentials_path.exists():
                raise FileNotFoundError("Google Sheets credentials file not found")
            
            # Load service account credentials
            credentials = Credentials.from_service_account_file(
                self.sheet_credentials_path,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            
            # Connect to Google Sheets
            client = gspread.authorize(credentials)
            spreadsheet = client.open_by_key(self.sheet_id)
            
            # Try to get worksheet - handle case sensitivity
            try:
                worksheet = spreadsheet.worksheet(self.sheet_name)
            except gspread.WorksheetNotFound:
                # Try with different case variations
                worksheets = spreadsheet.worksheets()
                worksheet_names = [ws.title for ws in worksheets]
                self.logger.error(f"Worksheet '{self.sheet_name}' not found. Available sheets: {worksheet_names}")
                
                # Try case-insensitive match
                for ws in worksheets:
                    if ws.title.lower() == self.sheet_name.lower():
                        worksheet = ws
                        self.logger.info(f"Found worksheet with case variation: '{ws.title}'")
                        break
                else:
                    raise gspread.WorksheetNotFound(f"No worksheet found matching '{self.sheet_name}'")
            
            self.logger.info("Connected to Google Sheets successfully")
            return worksheet
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Google Sheets: {e}")
            raise ConnectionError(f"Google Sheets connection failed: {e}")
    
    def _validate_license_format(self, license_key: str) -> bool:
        """Validate license key format (minimal validation)"""
        # Only check if license key is not empty
        if not license_key or not license_key.strip():
            return False
        
        # Any non-empty string is valid
        return True
    
    def validate_license_online(self, license_key: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate license key with Google Sheets
        Returns: (is_valid, message, license_data)
        """
        try:
            # Format validation
            if not self._validate_license_format(license_key):
                return False, "Invalid license key format", {}
            
            # Connect to Google Sheets with retries
            worksheet = None
            for attempt in range(self.max_retries):
                try:
                    worksheet = self._connect_to_sheets()
                    break
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise e
                    time.sleep(self.retry_delay * (attempt + 1))
            
            if not worksheet:
                return False, "Unable to connect to license server", {}
            
            # Get all records
            records = worksheet.get_all_records()
            
            # Find license key
            license_record = None
            row_index = None
            
            for idx, record in enumerate(records):
                if record.get('LICENSE_KEY', '').strip().upper() == license_key.strip().upper():
                    license_record = record
                    row_index = idx + 2  # +2 because sheets are 1-indexed and header is row 1
                    break
            
            if not license_record:
                return False, "License key not found", {}
            
            # Check status
            status = license_record.get('STATUS', '').strip().upper()
            if status != 'ACTIVE':
                return False, f"License is {status.lower()}", license_record
            
            # Check expiry date
            expiry_str = license_record.get('EXPIRY_DATE', '').strip()
            if expiry_str and expiry_str.upper() not in ['NA', 'N/A', 'NEVER', 'UNLIMITED']:
                try:
                    # Support multiple date formats
                    expiry_date = None
                    date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                    
                    for date_format in date_formats:
                        try:
                            expiry_date = datetime.strptime(expiry_str, date_format)
                            break
                        except ValueError:
                            continue
                    
                    if expiry_date is None:
                        return False, "Invalid expiry date format in license", license_record
                    
                    if datetime.now() > expiry_date:
                        # Update status to EXPIRED in sheet
                        try:
                            worksheet.update_cell(row_index, 2, 'EXPIRED')  # Column B (STATUS)
                        except Exception:
                            pass
                        return False, "License has expired", license_record
                        
                except Exception as e:
                    self.logger.error(f"Error parsing expiry date: {e}")
                    return False, "Invalid expiry date in license", license_record
            elif expiry_str and expiry_str.upper() in ['NA', 'N/A', 'NEVER', 'UNLIMITED']:
                # License with unlimited duration
                self.logger.info(f"License has unlimited duration: {expiry_str}")
            else:
                # Empty expiry date - treat as unlimited
                self.logger.info("License has no expiry date (unlimited)")
            
            # Get current device ID
            current_device_id = self._get_device_fingerprint()
            stored_device_id = license_record.get('DEVICE_ID', '').strip()
            
            # Check device binding
            if stored_device_id:
                if stored_device_id != current_device_id:
                    return False, "License is bound to another device", license_record
            else:
                # First activation - bind to current device
                try:
                    worksheet.update_cell(row_index, 3, current_device_id)  # Column C (DEVICE_ID)
                    license_record['DEVICE_ID'] = current_device_id
                    self.logger.info("License bound to current device")
                except Exception as e:
                    self.logger.error(f"Failed to bind license to device: {e}")
                    return False, "Failed to activate license", license_record
            
            self.logger.info(f"License validation successful for: {license_key}")
            return True, "License is valid", license_record
            
        except ConnectionError as e:
            return False, f"Connection error: {str(e)}", {}
        except Exception as e:
            self.logger.error(f"License validation error: {e}")
            return False, f"Validation error: {str(e)}", {}
    
    def save_license_data(self, license_key: str, license_data: Dict[str, Any]) -> bool:
        """Save encrypted license data locally"""
        try:
            license_info = {
                "license_key": license_key,
                "device_id": self._get_device_fingerprint(),
                "validated_at": datetime.now().isoformat(),
                "status": license_data.get('STATUS', ''),
                "expiry_date": license_data.get('EXPIRY_DATE', ''),
                "notes": license_data.get('NOTES', '')
            }
            
            # Encrypt and save
            encrypted_data = self._encrypt_data(json.dumps(license_info))
            
            with open(self.license_file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "data": encrypted_data,
                    "created": datetime.now().isoformat()
                }, f, indent=2)
            
            # Save device hash
            self._save_device_hash()
            
            self.logger.info("License data saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save license data: {e}")
            return False
    
    def load_license_data(self) -> Optional[Dict[str, Any]]:
        """Load and decrypt local license data"""
        try:
            if not self.license_file_path.exists():
                return None
            
            with open(self.license_file_path, 'r', encoding='utf-8') as f:
                encrypted_file = json.load(f)
            
            encrypted_data = encrypted_file.get('data')
            if not encrypted_data:
                return None
            
            # Decrypt data
            decrypted_json = self._decrypt_data(encrypted_data)
            license_data = json.loads(decrypted_json)
            
            # Verify device ID
            stored_device_id = license_data.get('device_id')
            current_device_id = self._get_device_fingerprint()
            
            if stored_device_id != current_device_id:
                self.logger.warning("Device ID mismatch in stored license")
                return None
            
            self.logger.info("License data loaded successfully")
            return license_data
            
        except Exception as e:
            self.logger.error(f"Failed to load license data: {e}")
            return None
    
    def is_license_valid(self, force_online_check=False) -> Tuple[bool, str]:
        """Check if current license is valid with optional real-time validation"""
        try:
            license_data = self.load_license_data()
            if not license_data:
                return False, "No license found"

            # CRITICAL: Real-time status check to prevent manual UNACTIVE bypass
            if force_online_check:
                license_key = license_data.get('license_key', '')
                if license_key:
                    try:
                        # Check online status to detect manual changes
                        is_valid_online, message_online, data_online = self.validate_license_online(license_key)
                        if not is_valid_online:
                            # License manually disabled or expired online
                            self.logger.warning(f"License invalidated online: {message_online}")
                            # Clear local cache to prevent bypass
                            self.clear_license_data()
                            return False, f"License status changed: {message_online}"
                    except Exception as e:
                        self.logger.warning(f"Online validation failed, using local: {e}")

            # Check local expiry date
            expiry_str = license_data.get('expiry_date', '').strip()
            if expiry_str and expiry_str.upper() not in ['NA', 'N/A', 'NEVER', 'UNLIMITED']:
                try:
                    date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%d.%m.%Y']
                    expiry_date = None

                    for date_format in date_formats:
                        try:
                            expiry_date = datetime.strptime(expiry_str, date_format)
                            break
                        except ValueError:
                            continue

                    if expiry_date and datetime.now() > expiry_date:
                        # Clear cache on expiry
                        self.clear_license_data()
                        return False, "License has expired"

                except Exception:
                    return False, "Invalid expiry date"

            # Check local status
            local_status = license_data.get('status', '').upper()
            if local_status in ['EXPIRED', 'INACTIVE', 'DISABLED', 'UNACTIVE']:
                # Clear cache if manually disabled
                self.clear_license_data()
                return False, f"License is {local_status.lower()}"

            return True, "License is valid"

        except Exception as e:
            self.logger.error(f"Error checking license validity: {e}")
            return False, f"License check failed: {str(e)}"
    
    def clear_license_data(self) -> bool:
        """Clear stored license data"""
        try:
            if self.license_file_path.exists():
                os.remove(self.license_file_path)
                
            if self.device_hash_path.exists():
                os.remove(self.device_hash_path)
                
            self.logger.info("License data cleared")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear license data: {e}")
            return False
    
    def get_license_info(self) -> Dict[str, Any]:
        """Get current license information"""
        license_data = self.load_license_data()
        if not license_data:
            return {}
        
        info = {
            "license_key": license_data.get('license_key', ''),
            "status": license_data.get('status', ''),
            "expiry_date": license_data.get('expiry_date', ''),
            "device_id": license_data.get('device_id', ''),
            "validated_at": license_data.get('validated_at', ''),
            "notes": license_data.get('notes', '')
        }
        
        # Add days remaining if expiry date exists
        expiry_str = info.get('expiry_date', '').strip()
        if expiry_str:
            if expiry_str.upper() in ['NA', 'N/A', 'NEVER', 'UNLIMITED']:
                # Unlimited license
                info['days_remaining'] = -1  # Special value for unlimited
                info['is_expired'] = False
                info['is_unlimited'] = True
            else:
                try:
                    date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                    expiry_date = None
                    
                    for date_format in date_formats:
                        try:
                            expiry_date = datetime.strptime(expiry_str, date_format)
                            break
                        except ValueError:
                            continue
                    
                    if expiry_date:
                        days_remaining = (expiry_date - datetime.now()).days
                        info['days_remaining'] = max(0, days_remaining)
                        info['is_expired'] = days_remaining < 0
                        info['is_unlimited'] = False
                    else:
                        info['days_remaining'] = 0
                        info['is_expired'] = True
                        info['is_unlimited'] = False
                        
                except Exception:
                    info['days_remaining'] = 0
                    info['is_expired'] = True
                    info['is_unlimited'] = False
        else:
            # No expiry date - treat as unlimited
            info['days_remaining'] = -1
            info['is_expired'] = False
            info['is_unlimited'] = True
        
        return info


# Test function untuk development
def test_license_manager():
    """Test function for license manager"""
    print("Testing License Manager...")
    
    license_manager = LicenseManager()
    
    print(f"Device fingerprint: {license_manager._get_device_fingerprint()}")
    
    # Test license validation dengan dummy key
    test_key = "TEST-KEY-12345"
    is_valid, message, data = license_manager.validate_license_online(test_key)
    print(f"Test validation: {is_valid}, {message}")


if __name__ == "__main__":
    test_license_manager()