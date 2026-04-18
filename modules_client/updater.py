#!/usr/bin/env python3
"""
VocaLive - Auto Updater
Cek versi via AppScript → download ZIP dari GitHub → replace EXE via batch script.

Cara rilis versi baru (developer):
1. Upload VocaLive-vX.X.X.zip ke GitHub Releases
2. Update AppScript: VERSION_INFO["vocalive"]["latest"] dan ["url"]
3. Deploy AppScript → user otomatis dapat notifikasi saat buka app
"""

import json
import logging
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import requests
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger('VocaLive.Updater')

# ============================================================
# Versi di-import dari version.py (satu sumber kebenaran)
try:
    import os as _os
    import sys as _sys
    _root = (_os.path.dirname(_sys.executable) if getattr(_sys, 'frozen', False)
             else _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    _sys.path.insert(0, _root)
    from version import VERSION as CURRENT_VERSION
except Exception:
    CURRENT_VERSION = "1.0.3"  # fallback

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
        exe_name    = Path(current_exe).name   # "VocaLive.exe"

        # Taruh batch + VBS di folder yang sama dengan EXE (bukan temp dir)
        # agar working dir batch = folder EXE saat di-startfile
        bat_path = str(Path(current_exe).parent / "_vocalive_update.bat")
        vbs_path = str(Path(current_exe).parent / "_vocalive_update_run.vbs")

        # Resolve UI language untuk pesan GUI akhir (batch jalan setelah app quit,
        # jadi kita embed string langsung ke batch saat tulis)
        try:
            from modules_client import i18n
            _ui_lang = i18n.current_language()
        except Exception:
            _ui_lang = "id"

        # Message text untuk PowerShell MessageBox. Jangan pakai newline escape
        # (`n) karena dibungkus single-quote di PowerShell → escape tidak expand.
        # Satu kalimat cukup, lebih clean.
        if _ui_lang == "en":
            success_title = "VocaLive"
            success_msg = "Update successful. Please open the application manually."
            fail_title = "VocaLive Update"
            fail_msg = "Update failed. Please reinstall VocaLive manually."
        else:
            success_title = "VocaLive"
            success_msg = "Update berhasil, silakan buka aplikasi secara manual."
            fail_title = "VocaLive Update"
            fail_msg = "Update gagal. Silakan install ulang VocaLive manual."

        # Batch script — TIDAK ada auto-launch, GUI popup di akhir via PowerShell MessageBox.
        # PowerShell dipanggil dengan WindowStyle Hidden supaya tidak flash console window.
        bat_content = (
            "@echo off\n"
            "setlocal\n"
            # Tunggu 5 detik — app quit langsung (100ms), PyInstaller cleanup _MEI ~1-2s.
            "timeout /t 5 /nobreak > nul\n"
            # Force-kill sisa proses jika entah kenapa belum mati
            f'taskkill /f /im "{exe_name}" > nul 2>&1\n'
            "timeout /t 1 /nobreak > nul\n"
            # Bersihkan _MEI* lama sebagai safety net
            'for /d %%D in ("%TEMP%\\_MEI*") do rd /s /q "%%D" 2>nul\n'
            # Copy EXE baru — retry kalau masih locked (max 5 attempts)
            "set /a attempts=0\n"
            ":retry\n"
            "set /a attempts+=1\n"
            f'copy /y "{new_exe}" "{current_exe}" > nul 2>&1\n'
            "if errorlevel 1 (\n"
            "    if %attempts% geq 5 goto fail\n"
            "    timeout /t 2 /nobreak > nul\n"
            "    goto retry\n"
            ")\n"
            # SUCCESS: show native Windows MessageBox via PowerShell (bukan CMD echo)
            "powershell -WindowStyle Hidden -Command "
            '"Add-Type -AssemblyName PresentationFramework; '
            f"[System.Windows.MessageBox]::Show('{success_msg}', '{success_title}', 'OK', 'Information') | Out-Null\" > nul 2>&1\n"
            "goto cleanup\n"
            ":fail\n"
            # FAIL: show error dialog
            "powershell -WindowStyle Hidden -Command "
            '"Add-Type -AssemblyName PresentationFramework; '
            f"[System.Windows.MessageBox]::Show('{fail_msg}', '{fail_title}', 'OK', 'Error') | Out-Null\" > nul 2>&1\n"
            ":cleanup\n"
            f'del /f /q "{new_exe}" > nul 2>&1\n'
            f'rd /s /q "{temp_dir}" > nul 2>&1\n'
            f'del /f /q "{vbs_path}" > nul 2>&1\n'
            'del /f /q "%~f0"\n'
        )

        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)

        # VBS wrapper untuk run batch HIDDEN (0 = window hidden).
        # Tanpa ini, os.startfile(.bat) akan open cmd.exe dengan visible window.
        vbs_content = (
            'Set WshShell = CreateObject("WScript.Shell")\r\n'
            f'WshShell.Run """{bat_path}""", 0, False\r\n'
        )
        with open(vbs_path, 'w', encoding='utf-8') as f:
            f.write(vbs_content)

        # KEY: os.startfile(.vbs) = ShellExecute → wscript.exe runs VBS → Run batch hidden.
        # wscript.exe tidak inherit handle ke EXE kita, dan window=0 bikin CMD invisible.
        # Output: user tidak pernah lihat CMD window; hanya lihat native popup di akhir.
        os.startfile(vbs_path)

        # Send PostHog event
        try:
            from modules_client.telemetry import capture as _tel_capture
            _tel_capture("update_installed", {
                "old_version": CURRENT_VERSION,
                "new_version": "unknown",
            })
        except Exception:
            pass

        logger.info("Update installer diluncurkan via os.startfile (detached)")
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
