#!/usr/bin/env python3
"""
VocaLive - Auto Updater
Cek versi via AppScript → download ZIP dari GitHub → replace EXE via batch script.

Cara rilis versi baru (developer):
1. Upload VocaLive-vX.X.X.zip ke GitHub Releases
2. Update AppScript: VERSION_INFO["vocalive"]["latest"] dan ["url"]
3. User akan otomatis dapat notifikasi saat buka app
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, Callable

import requests
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger('VocaLive.Updater')

# ============================================================
CURRENT_VERSION = "1.0.1"
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
            data = json.loads(cfg.read_text())
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
            timeout=10
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


class DownloadThread(QThread):
    """Download ZIP update di background thread."""

    progress = pyqtSignal(int)        # 0-100
    finished = pyqtSignal(str)        # path file ZIP yang didownload
    error    = pyqtSignal(str)        # pesan error

    def __init__(self, url: str, dest_path: str):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            resp = requests.get(self.url, stream=True, timeout=60)
            resp.raise_for_status()

            total = int(resp.headers.get('content-length', 0))
            downloaded = 0

            with open(self.dest_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
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
    2. Tulis batch script yang replace EXE lama setelah app tutup
    3. Launch batch script → app tutup sendiri
    """
    try:
        temp_dir = tempfile.mkdtemp(prefix="vocalive_update_")

        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_dir)

        # Cari EXE di dalam ZIP
        new_exe = None
        for f in Path(temp_dir).rglob("*.exe"):
            new_exe = str(f)
            break

        if not new_exe:
            logger.error("Tidak ada .exe di dalam ZIP update")
            return False

        # Path EXE yang sedang berjalan
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
        else:
            # Mode development — tidak perlu replace EXE
            logger.info(f"[DEV MODE] Update tersedia di: {new_exe}")
            logger.info("Jalankan ulang app secara manual untuk test update")
            return True

        bat_path = os.path.join(temp_dir, "do_update.bat")
        bat_content = f"""@echo off
title VocaLive Updater
echo Menunggu aplikasi selesai...
timeout /t 2 /nobreak >nul

:wait_loop
tasklist /FI "IMAGENAME eq {os.path.basename(current_exe)}" 2>NUL | find /I /N "{os.path.basename(current_exe)}" >NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak >nul
    goto wait_loop
)

echo Menginstall update...
copy /Y "{new_exe}" "{current_exe}"
if errorlevel 1 (
    echo Gagal meng-copy file. Coba jalankan sebagai Administrator.
    pause
    exit /b 1
)

echo Update berhasil! Meluncurkan VocaLive...
start "" "{current_exe}"
exit /b 0
"""
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)

        # Jalankan batch script sebagai proses terpisah (tidak tunggu)
        subprocess.Popen(
            ['cmd.exe', '/c', bat_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            close_fds=True
        )

        logger.info(f"Update installer diluncurkan: {bat_path}")
        return True

    except Exception as e:
        logger.error(f"Gagal install update: {e}")
        return False
    finally:
        # Hapus ZIP setelah ekstrak
        try:
            os.remove(zip_path)
        except Exception:
            pass
