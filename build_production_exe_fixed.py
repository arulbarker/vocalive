#!/usr/bin/env python3
"""
VocaLive — Production Build Script
Menghasilkan VocaLive-vX.X.X.zip siap upload ke GitHub Releases.
"""

import os
import sys
import shutil
import subprocess
import json
import zipfile
from pathlib import Path
from datetime import datetime

# Fix encoding Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Versi dari satu sumber kebenaran ────────────────────────────────
try:
    from version import VERSION as APP_VERSION, VERSION_WIN
except Exception:
    APP_VERSION = "1.0.3"
    VERSION_WIN = "1.0.3.0"


# ════════════════════════════════════════════════════════════════════
#  LANGKAH 1 — BERSIHKAN dist/ DAN build/
# ════════════════════════════════════════════════════════════════════

def clean_build():
    print("[CLEAN] Membersihkan folder build lama...")
    for dirname in ["build", "dist", "__pycache__"]:
        p = Path(dirname)
        if p.exists():
            shutil.rmtree(p)
            print(f"  ✓ Hapus: {dirname}/")
    for spec in Path(".").glob("*.spec"):
        spec.unlink()
        print(f"  ✓ Hapus: {spec.name}")
    for txt in ["version_info.txt"]:
        if Path(txt).exists():
            Path(txt).unlink()


# ════════════════════════════════════════════════════════════════════
#  LANGKAH 2 — BUILD EXE VIA PYINSTALLER
# ════════════════════════════════════════════════════════════════════

def build_exe():
    print(f"\n[BUILD] Membangun VocaLive v{APP_VERSION} EXE...")

    # ── Buat version_info.txt untuk metadata Windows EXE ────────────
    vt = tuple(int(x) for x in APP_VERSION.split(".")) + (0,)
    version_info_txt = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={vt},
    prodvers={vt},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(u'040904B0', [
        StringStruct(u'CompanyName', u'VocaLive'),
        StringStruct(u'FileDescription', u'VocaLive - Live Streaming AI'),
        StringStruct(u'FileVersion', u'{VERSION_WIN}'),
        StringStruct(u'InternalName', u'VocaLive'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2025 VocaLive'),
        StringStruct(u'OriginalFilename', u'VocaLive.exe'),
        StringStruct(u'ProductName', u'VocaLive'),
        StringStruct(u'ProductVersion', u'{VERSION_WIN}'),
      ])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""
    Path("version_info.txt").write_text(version_info_txt, encoding="utf-8")
    print("  ✓ Buat version_info.txt")

    # ── Buat spec file ───────────────────────────────────────────────
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None

# Kumpulkan file pytchat_ng
pytchat_datas = []
pytchat_path = Path("thirdparty/pytchat_ng")
if pytchat_path.exists():
    for f in pytchat_path.rglob("*"):
        if f.is_file() and f.suffix not in (".pyc", ".pyo"):
            rel = f.relative_to("thirdparty/pytchat_ng")
            pytchat_datas.append((str(f), f"pytchat/{rel.parent}"))

a = Analysis(
    ["main.py"],
    pathex=[".", "thirdparty", "thirdparty/pytchat_ng"],
    binaries=[],
    datas=[
        ("config/settings_default.json", "config"),
        ("config/voices.json",           "config"),
        ("config/packages.json",         "config"),
        ("ui",             "ui"),
        ("modules_client", "modules_client"),
        ("modules_server", "modules_server"),
        ("listeners",      "listeners"),
        ("icon.ico",       "."),
        ("version.py",     "."),
    ] + pytchat_datas,
    hiddenimports=[
        # pytchat
        "pytchat", "pytchat.core", "pytchat.core.pytchat",
        "pytchat.config", "pytchat.parser", "pytchat.parser.live",
        "pytchat.processors", "pytchat.processors.default",
        "pytchat.exceptions", "pytchat.paramgen", "pytchat.paramgen.liveparam",
        # network
        "requests", "urllib3", "certifi",
        "websockets", "websockets.client", "websockets.server",
        "aiohttp", "aiohttp.client", "aiohttp.client_ws",
        "async_timeout", "multidict", "yarl",
        # crypto (untuk license) — HARUS lengkap sesuai license_manager.py
        "cryptography", "cryptography.fernet",
        "cryptography.hazmat", "cryptography.hazmat.primitives",
        "cryptography.hazmat.primitives.hashes",
        "cryptography.hazmat.primitives.kdf",
        "cryptography.hazmat.primitives.kdf.pbkdf2",
        "cryptography.hazmat.backends",
        "cryptography.hazmat.backends.default",
        # UI
        "PyQt6", "PyQt6.QtCore", "PyQt6.QtWidgets", "PyQt6.QtGui",
        "PyQt6.QtMultimedia", "PyQt6.QtMultimediaWidgets",
        # audio
        "pygame", "pygame.mixer",
        # misc
        "keyboard", "psutil", "packaging",
        # TTS
        "gtts",
        # Monitoring & Error Tracking
        "posthog",
        "sentry_sdk",
        "sentry_sdk.integrations",
        "sentry_sdk.integrations.stdlib",
        "sentry_sdk.integrations.excepthook",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["whisper", "torch", "transformers", "speech_recognition",
              "customtkinter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="VocaLive",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="icon.ico",
    version="version_info.txt",
)
'''
    Path("VocaLive.spec").write_text(spec_content, encoding="utf-8")
    print("  ✓ Buat VocaLive.spec")

    # ── Jalankan PyInstaller ─────────────────────────────────────────
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "VocaLive.spec"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"\n[ERROR] PyInstaller gagal:\n{result.stderr[-3000:]}")
        return False

    exe_out = Path("dist/VocaLive.exe")
    if not exe_out.exists():
        print("[ERROR] dist/VocaLive.exe tidak ditemukan setelah build!")
        return False

    size_mb = exe_out.stat().st_size / (1024 * 1024)
    print(f"  ✓ dist/VocaLive.exe ({size_mb:.1f} MB)")
    return True


# ════════════════════════════════════════════════════════════════════
#  LANGKAH 3 — BUAT PAKET ZIP SIAP UPLOAD
# ════════════════════════════════════════════════════════════════════

def create_zip():
    print(f"\n[PACKAGE] Membuat VocaLive-v{APP_VERSION}.zip...")

    pkg_dir  = Path("dist") / f"VocaLive-v{APP_VERSION}"
    zip_path = Path("dist") / f"VocaLive-v{APP_VERSION}.zip"

    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir(parents=True)

    # ── 1. Copy EXE ──────────────────────────────────────────────────
    shutil.copy2("dist/VocaLive.exe", pkg_dir / "VocaLive.exe")
    print("  ✓ VocaLive.exe")

    # ── 2. Config (template bersih saja) ────────────────────────────
    cfg_dst = pkg_dir / "config"
    cfg_dst.mkdir()

    # Salin template bersih dari settings_default.json → settings.json
    settings_default = Path("config/settings_default.json")
    if settings_default.exists():
        shutil.copy2(settings_default, cfg_dst / "settings.json")
        shutil.copy2(settings_default, cfg_dst / "settings_default.json")
        print("  ✓ config/settings.json (template bersih)")
    else:
        # Fallback: buat minimal template
        minimal = {
            "platform": "TikTok",
            "paket": "basic",
            "ai_provider": "gemini",
            "output_language": "Indonesia",
            "debug_mode": False,
            "tiktok_nickname": "",
            "trigger_words": ["bro", "bang", "min"],
            "cohost_cooldown": 2,
            "viewer_cooldown_minutes": 3,
            "tts_voice": "Gemini-Puck (MALE)",
            "tts_key_type": "",
            "google_tts_api_key": "",
            "api_keys": {"GEMINI_API_KEY": "", "DEEPSEEK_API_KEY": ""},
            "user_context": ""
        }
        (cfg_dst / "settings.json").write_text(json.dumps(minimal, indent=2), encoding="utf-8")
        (cfg_dst / "settings_default.json").write_text(json.dumps(minimal, indent=2), encoding="utf-8")

    for safe_cfg in ["voices.json", "packages.json"]:
        src = Path("config") / safe_cfg
        if src.exists():
            shutil.copy2(src, cfg_dst / safe_cfg)
            print(f"  ✓ config/{safe_cfg}")

    # ── 4. Zip seluruh folder ────────────────────────────────────────
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for f in pkg_dir.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(pkg_dir))

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"\n  ✅ {zip_path}  ({size_mb:.1f} MB)")
    return zip_path


# ════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print(f"  VocaLive Build — v{APP_VERSION}")
    print("=" * 60)

    clean_build()

    if not build_exe():
        print("\n[GAGAL] Build EXE tidak berhasil.")
        sys.exit(1)

    zip_path = create_zip()

    print("\n" + "=" * 60)
    print(f"  BUILD SELESAI ✅")
    print(f"  ZIP siap upload: {zip_path}")
    print(f"  Upload ke: https://github.com/arulbarker/vocalive-release/releases")
    print(f"  Tag: v{APP_VERSION}  |  File: VocaLive-v{APP_VERSION}.zip")
    print("=" * 60)
