# ============================================================
# VOCALIVE — SINGLE SOURCE OF TRUTH untuk nomor versi
#
# CARA RILIS VERSI BARU:
# 1. Ganti VERSION di bawah ini (satu-satunya tempat)
# 2. Jalankan build_production_exe_fixed.py → EXE otomatis pakai versi baru
# 3. Upload ZIP ke GitHub Releases dengan nama VocaLive-vX.X.X.zip
# 4. Update AppScript: VERSION_INFO["vocalive"]["latest"] + ["url"] → deploy
#
# Semua file lain (main.py, updater.py, main_window.py, build script)
# import dari sini — tidak ada hardcode versi di tempat lain.
# ============================================================

VERSION = "1.0.19"

# Pecahan untuk kemudahan
_parts = VERSION.split(".")
VERSION_MAJOR = int(_parts[0])
VERSION_MINOR = int(_parts[1])
VERSION_PATCH = int(_parts[2])

# Format untuk EXE metadata Windows (harus 4 angka)
VERSION_WIN = f"{VERSION}.0"          # "1.0.3.0"
VERSION_TUPLE = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH, 0)
