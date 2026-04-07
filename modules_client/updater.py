#!/usr/bin/env python3
"""
VocaLive - Auto Updater
Cek versi via AppScript → download ZIP dari GitHub → replace EXE via batch script.

Cara rilis versi baru (developer):
1. Upload VocaLive-vX.X.X.zip ke GitHub Releases
2. Update AppScript: VERSION_INFO["vocalive"]["latest"] dan ["url"]
3. Deploy AppScript → user otomatis dapat notifikasi saat buka app
"""

import os
import sys
import json
import zipfile
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple

import requests
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger('VocaLive.Updater')

# ============================================================
CURRENT_VERSION = "1.0.3"
APPSCRIPT_URL   = "https://script.google.com/macros/s/AKfycbzPixa15u3SyndcKTcusIpxChqepUsgGfxTm1_nIaD1RHo-3TpLRbkHmesm-p2QkgWjEA/exec"
APP_SECRET      = "TKD-2025-s3cr3t-k3y-9xKm2pQr7nVw4L"
PRODUCT_ID      = "vocalive"
# ============================================================


def _load_url_override():
    """Baca AppScript URL dari config/license_config.json jika ada."""
    global APPSCRIPT_URL, APP_SECRET
    try:
        root = (Path(sys.executable).parent if getattr(sys, 'frozen', False)
                else Path(__file__).parent.parent)
        cfg = root / "config" / "license_config.json"
        if cfg.exists():
            data = json.loads(cfg.read_text(encoding='utf-8'))
            if data.get("appscript_url"):
                APPSCRIPT_URL = data["appscript_url"]
            if data.get("app_secret"):
                APP_SECRET = data["app_secret"]
    except Exception:
        pass

_load_url_override()


def _parse_version(v: str) -> Tuple[int, ...]:
    """'1.2.3' → (1, 2, 3)"""
    try:
        return tuple(int(x) for x in v.strip().lstrip('v').split('.'))
    except Exception:
        return (0,)


def check_for_update() -> Tuple[bool, Optional[dict]]:
    """
    Cek AppScript apakah ada versi baru.
    Return: (ada_update, info_dict)
    info_dict keys: latest, notes, url
    """
    try:
        resp = requests.get(
            APPSCRIPT_URL,
            params={"action": "version", "product": PRODUCT_ID, "app_secret": APP_SECRET},
            timeout=15
        )
        resp.raise_for_status()
        info = resp.json()
        latest = info.get("latest", "0.0.0")
        if _parse_version(latest) > _parse_version(CURRENT_VERSION):
            logger.info(f"Update tersedia: {CURRENT_VERSION} → {latest}")
            return True, info
        logger.info(f"Sudah versi terbaru: {CURRENT_VERSION}")
        return False, None
    except Exception as e:
        logger.warning(f"Gagal cek update: {e}")
        return False, None


class UpdateCheckThread(QThread):
    """Cek update di background — tidak block UI."""
    update_available = pyqtSignal(dict)   # emit jika ada versi baru
    no_update        = pyqtSignal(str)    # emit "vX.X.X" jika sudah terbaru
    check_error      = pyqtSignal(str)    # emit pesan error jika gagal cek

    def run(self):
        try:
            has_update, info = check_for_update()
            if has_update and info:
                self.update_available.emit(info)
            elif not has_update and info is None:
                # Cek apakah error atau memang up-to-date
                # Coba get versi sekali lagi untuk bedakan
                try:
                    resp = requests.get(
                        APPSCRIPT_URL,
                        params={"action": "version", "product": PRODUCT_ID, "app_secret": APP_SECRET},
                        timeout=15
                    )
                    data = resp.json()
                    latest = data.get("latest", CURRENT_VERSION)
                    self.no_update.emit(latest)
                except Exception as e:
                    self.check_error.emit(str(e))
            else:
                self.no_update.emit(CURRENT_VERSION)
        except Exception as e:
            self.check_error.emit(str(e))


class DownloadThread(QThread):
    """Download ZIP update di background thread."""

    progress = pyqtSignal(int)   # 0-100
    finished = pyqtSignal(str)   # path ZIP yang didownload
    error    = pyqtSignal(str)   # pesan error

    def __init__(self, url: str, dest_path: str):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            resp = requests.get(self.url, stream=True, timeout=120,
                                allow_redirects=True)
            resp.raise_for_status()

            total = int(resp.headers.get('content-length', 0))
            downloaded = 0

            with open(self.dest_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            self.progress.emit(int(downloaded * 100 / total))

            self.progress.emit(100)
            self.finished.emit(self.dest_path)
        except Exception as e:
            self.error.emit(str(e))


def install_update(zip_path: str) -> bool:
    """
    Install update dari ZIP:
    1. Extract EXE baru ke temp folder
    2. Tulis batch script (PID-based wait → copy → restart)
    3. Launch batch → return True → caller harus quit app

    Batch script berjalan SETELAH app tutup, bukan saat masih jalan.
    """
    try:
        temp_dir = tempfile.mkdtemp(prefix="vocalive_upd_")

        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_dir)

        # Cari EXE di ZIP (ambil yang pertama)
        new_exe = None
        for f in Path(temp_dir).rglob("*.exe"):
            # Skip updater helper jika ada
            if "updater" not in f.name.lower():
                new_exe = str(f)
                break
        # Fallback: ambil EXE apapun
        if not new_exe:
            for f in Path(temp_dir).rglob("*.exe"):
                new_exe = str(f)
                break

        if not new_exe:
            logger.error("Tidak ada .exe di dalam ZIP update")
            return False

        # Mode DEV — tidak frozen EXE
        if not getattr(sys, 'frozen', False):
            logger.info(f"[DEV MODE] EXE baru tersedia di: {new_exe}")
            logger.info("Di production: EXE lama akan diganti otomatis")
            return True

        current_exe = sys.executable
        current_pid = os.getpid()

        bat_path = os.path.join(temp_dir, "do_update.bat")

        # Batch yang solid:
        # - Tunggu berdasarkan PID (bukan nama file — lebih reliable)
        # - Backup EXE lama sebelum replace
        # - Self-delete setelah selesai
        bat_content = (
            "@echo off\n"
            "title VocaLive Updater\n"
            "echo ================================\n"
            "echo  VocaLive Update Installer\n"
            "echo ================================\n"
            "echo.\n"
            "echo Menunggu aplikasi selesai...\n"
            "echo.\n"
            "\n"
            ":wait_pid\n"
            f"tasklist /FI \"PID eq {current_pid}\" 2>NUL | find \"{current_pid}\" >NUL\n"
            "if not errorlevel 1 (\n"
            "    timeout /t 1 /nobreak >NUL\n"
            "    goto wait_pid\n"
            ")\n"
            "\n"
            "echo Menginstall update...\n"
            "\n"
            ":: Backup EXE lama\n"
            f"copy /Y \"{current_exe}\" \"{current_exe}.bak\" >NUL 2>&1\n"
            "\n"
            ":: Copy EXE baru\n"
            f"copy /Y \"{new_exe}\" \"{current_exe}\"\n"
            "if errorlevel 1 (\n"
            "    echo.\n"
            "    echo GAGAL mengganti EXE!\n"
            "    echo Kemungkinan penyebab:\n"
            "    echo  1. File masih terkunci - tunggu beberapa detik lalu coba lagi\n"
            "    echo  2. Tidak ada izin - jalankan sebagai Administrator\n"
            "    echo.\n"
            "    :: Restore backup\n"
            f"    copy /Y \"{current_exe}.bak\" \"{current_exe}\" >NUL 2>&1\n"
            "    pause\n"
            "    exit /b 1\n"
            ")\n"
            "\n"
            "echo.\n"
            "echo Update berhasil! Meluncurkan VocaLive versi terbaru...\n"
            "timeout /t 1 /nobreak >NUL\n"
            f"start \"\" \"{current_exe}\"\n"
            "\n"
            ":: Cleanup: hapus backup dan folder temp\n"
            f"del \"{current_exe}.bak\" >NUL 2>&1\n"
            f"rd /s /q \"{temp_dir}\" >NUL 2>&1\n"
            "\n"
            ":: Self-delete batch script\n"
            "(goto) 2>NUL & del \"%~f0\"\n"
        )

        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)

        # Launch batch script dalam console terpisah
        # CREATE_NEW_CONSOLE: user bisa lihat progress
        # Tidak tunggu (Popen, bukan run)
        subprocess.Popen(
            ['cmd.exe', '/c', bat_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            close_fds=True
        )

        logger.info(f"Update installer diluncurkan (PID target: {current_pid})")
        return True

    except Exception as e:
        logger.error(f"Gagal install update: {e}")
        return False
    finally:
        # Hapus ZIP (file besar, tidak perlu disimpan)
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception:
            pass
