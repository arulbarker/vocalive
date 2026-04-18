# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Branding Colors — Ocean Blue 🌊

Palet warna resmi VocaLive. **Jangan ganti tanpa konfirmasi eksplisit dari user.**

| Token | Nilai | Kegunaan |
|-------|-------|---------|
| Primary | `#2563EB` | Biru cerah — CTA button, active state |
| Secondary | `#1E3A5F` | Biru tua — depth, hover, border |
| Accent | `#60A5FA` | Biru muda — badge, notifikasi, highlight |
| BG Base | `#0F1623` | Dark navy background utama |
| BG Surface | `#162032` | Card / panel surface |
| BG Elevated | `#1E2A3B` | Elevated card / header |
| Text | `#F0F6FF` | Putih biru — teks utama |
| Border Radius | `10px` | Rounded medium semua komponen |

## Version History

> Selalu cek tabel ini sebelum rilis. Versi dikelola di `version.py` — **satu-satunya tempat mengubah nomor versi**.

| Versi | Tanggal | Deskripsi |
|-------|---------|-----------|
| **v1.0.0** | 2026-04-05 | Versi awal — hapus Avatar Lip-sync & OBS Overlay, fokus Cohost AI + TTS |
| **v1.0.1** | 2026-04-07 | Tambah suara Malaysia (ms-MY), fix TTS preview, fix Gemini WAV header |
| **v1.0.2** | 2026-04-07 | Product popup: QVideoSink+QLabel, chroma key, drag/resize, toggle ON/OFF |
| **v1.0.3** | 2026-04-07 | Email login via AppScript, auto-update system, voice selector + API key detection |
| **v1.0.4** | 2026-04-08 | Greeting AI: 10 sapaan unik via Gemini tiap 2 jam, TTS cache, anti-spam TikTok |
| **v1.0.5** | 2026-04-08 | Fix: DLL error setelah auto-update, login ulang setiap restart, Enter di login dialog |
| **v1.0.6** | 2026-04-08 | Fix: auto-update gagal copy EXE — tambah delay 3s + retry 15x otomatis |
| **v1.0.7** | 2026-04-08 | Fix: DLL error setelah auto-update — launch EXE baru dari direktori yang benar |
| **v1.0.8** | 2026-04-08 | Fix: ganti start ke explorer untuk launch EXE baru (os.startfile equivalent) |
| **v1.0.9** | 2026-04-08 | Fix FINAL: os.startfile untuk batch update (ShellExecute, zero inherited handles), revert runtime_tmpdir ke None |
| **v1.0.10** | 2026-04-08 | Fix: Access Denied saat startup EXE — greeting_cache & config/analytics pakai path absolut |
| **v1.0.11** | 2026-04-08 | Fix: DLL error setelah update — batch hapus _MEI* lama sebelum launch EXE baru |
| **v1.0.12** | 2026-04-08 | Fix: hapus auto-launch dari batch — start "" menyebabkan DLL error PyInstaller |
| **v1.0.13** | 2026-04-08 | Fix ROOT CAUSE: quit langsung (100ms) bukan 2.5s — _MEI cleanup sebelum batch start |
| **v1.0.14** | 2026-04-16 | Fix: listener hanya baca komentar LIVE (grace period 3s), sembunyikan Ukuran Popup |
| **v1.0.15** | 2026-04-18 | Bilingual UI support (Indonesia / English), OS locale detection, migration user existing |

**Versi saat ini: v1.0.15**

Versioning: `MAJOR` = breaking change, `MINOR` = fitur baru backward-compatible, `PATCH` = bug fix.

---

## What This App Does

**VocaLive** adalah Windows desktop app untuk live streaming automation. Mendengarkan chat **TikTok Live**, menghasilkan balasan AI (DeepSeek / Gemini Flash Lite), mengubahnya ke suara (Google Cloud TTS / Gemini TTS), lalu memutarnya selama siaran. Didistribusikan sebagai EXE berlisensi berbasis email.

## Running & Building

```bash
# Development mode
python main.py

# Build production EXE + ZIP siap upload (output: dist/VocaLive-vX.X.X.zip)
python build_production_exe_fixed.py

# Verify telemetry (PostHog + Sentry) kirim ke server
python vtest_telemetry.py
```

### Testing

```bash
# Run semua test (WAJIB sebelum commit)
python -m pytest tests/ -v --tb=short

# Run satu test file
python -m pytest tests/test_version.py -v

# Run satu test function
python -m pytest tests/test_analytics_manager.py::TestKeywordExtraction::test_product_keywords -v

# Run dengan coverage report
python -m pytest tests/ --cov=modules_client --cov=modules_server --cov-report=term-missing

# Verify telemetry (PostHog + Sentry) kirim ke server
python vtest_telemetry.py
```

**WAJIB: Setiap perubahan file harus diikuti `python -m pytest tests/ -v --tb=short`.** Jika ada test FAIL, fix dulu sebelum lanjut. Jangan commit jika ada test gagal.

Test suite: **213 tests di 20 files** (`tests/`). Empat tier:
- **Tier 1** = pure logic (version, templates, theme, logger) — tidak butuh external
- **Tier 2** = mocked I/O (config, user_list, product_scene, analytics, greeting, updater, validator, tiktok_listener, virtual_camera_manager)
- **Tier 3** = mocked SDK (telemetry, TTS, API routing dengan isolation ConfigManager patch)
- **Tier 4** = UI widget tests via `pytest-qt` (virtual_camera_tab, license_dialog, config_tab) — 57 tests total

**Pattern mocking penting untuk `test_api_routing.py`**: ConfigManager di-import lokal di dalam fungsi, patch harus ke `modules_client.config_manager.ConfigManager` (bukan `modules_client.api.ConfigManager`) agar efektif.

**Pattern untuk UI test**: gunakan `qtbot.addWidget()` fixture + `MagicMock` untuk manager/dependencies. Untuk check widget visibility di headless mode, pakai `.isHidden()` bukan `.isVisible()` (return False kalau parent belum shown).

Pastikan `config/settings.json` berisi API key yang valid untuk development.

### Dev Tooling: Lint, Format, Pre-commit

Setelah clone repo pertama kali, install dev tooling:

```bash
pip install -r requirements-dev.txt
pre-commit install       # aktifkan pre-commit hooks di .git/hooks
```

Perintah harian:

```bash
# Cek linting (tanpa fix)
ruff check .

# Auto-fix yang aman + format
ruff check --fix .
ruff format .

# Jalankan semua pre-commit hooks manual
pre-commit run --all-files
```

Konfig ruff ada di `pyproject.toml` — mulai dari rule conservative (E/F/I/W). Folder `thirdparty/`, `dwpose/`, `sd-vae-ft-mse/` di-exclude karena dead code / vendored.

**Baseline ruff saat ini** (post cleanup merge): ~107 issue tersisa, mostly E702 (multiple statements, theme.py fallback pattern) dan 17 F401 availability-check patterns (`try: import X`). Sudah ≥92% clean dari baseline awal 1369.

CI pipeline: `.github/workflows/test.yml` (pytest di Windows) + `lint.yml` (ruff di Ubuntu). Push ke branch `main`/`release/**`/`feat/**`/`fix/**`/`chore/**` akan auto-trigger.

**`lint.yml` saat ini set `continue-on-error: true`** — informational only, bukan gating. Setelah baseline 0, remove flag ini supaya lint benar-benar block merge.

### Manual QA Checklist — Smoke Test Sebelum Rilis

**WAJIB** dijalankan sebelum tag release baru. Test otomatis tidak mencakup interaksi real dengan TikTok/driver/Windows — checklist ini bridge gap tersebut.

#### 🧪 Startup & License
- [ ] EXE jalan di Windows 10 (VM atau PC terpisah) tanpa dialog error
- [ ] EXE jalan di Windows 11
- [ ] First-time login: email valid → dashboard muncul
- [ ] Restart app: session cache valid, tidak minta login ulang
- [ ] Offline mode: cache <24 jam → app tetap bisa buka (grace period)

#### 🎙️ TTS
- [ ] Preview Gemini TTS (voice prefix `Gemini-*`) bunyi tanpa error
- [ ] Preview Google Cloud TTS (Chirp3/Standard) bunyi
- [ ] Tombol 🔍 Deteksi API Key → hasil sesuai (gemini/cloud/all)
- [ ] Voice dropdown filter sesuai `tts_key_type`

#### 📡 TikTok Live
- [ ] Konek ke akun TikTok yang sedang live → status hijau
- [ ] Komentar realtime masuk (bukan history) setelah grace period 3s
- [ ] Blacklist user: pesan ter-block
- [ ] Whitelist user: bypass cooldown
- [ ] Toxic word: pesan ter-block
- [ ] Cohost reply AI + TTS berfungsi

#### 🛍️ Product Popup
- [ ] AI reply dengan `scene_id > 0` → popup video muncul
- [ ] Popup ter-capture di OBS/TikTok Live Studio (tidak hitam, chroma key hijau)
- [ ] Drag, resize, toggle ON/OFF berfungsi

#### 🎬 Virtual Camera
- [ ] Deteksi backend: OBS atau UnityCapture muncul di status
- [ ] Panel warning muncul kalau driver tidak terdeteksi
- [ ] Playlist video: tambah, hapus, play sequential/random

#### 🔄 Auto-Update
- [ ] Tombol 🔄 Cek Update: bandingkan dengan AppScript
- [ ] Update tersedia: download ZIP sukses
- [ ] Install: batch script jalan, `_MEI*` dibersihkan, copy EXE sukses
- [ ] **Buka EXE baru MANUAL** (bukan auto-launch) → jalan tanpa DLL error

#### 📊 Telemetry
- [ ] `app_launched` muncul di PostHog dashboard
- [ ] Error test (misal disconnect TikTok) muncul di Sentry
- [ ] Device ID konsisten antara restart

#### 📦 Build Output
- [ ] `dist/VocaLive-vX.X.X.zip` size ~236MB (tidak >500MB)
- [ ] EXE tidak dianggap virus oleh Windows Defender
- [ ] Tidak ada folder `torch`, `nvidia`, `cuda`, `OpenGL` di dist

#### 🌐 Bilingual / i18n
- [ ] Fresh install di Windows id-ID → UI muncul Indonesia
- [ ] Fresh install di Windows en-US → UI muncul English
- [ ] Update dari v1.0.14 → UI tetap Indonesia (migration)
- [ ] Ganti UI lang di Config Tab → restart → semua tab pakai bahasa baru
- [ ] License dialog tampil sesuai UI lang (saat first install sebelum login)
- [ ] Update dialog tampil sesuai UI lang
- [ ] Sales template dropdown: nama dan content sesuai UI lang
- [ ] Template dikirim ke AI sesuai UI lang, tapi AI output tetap ikuti output_language
- [ ] Error TTS ditampilkan dalam UI lang
- [ ] Greeting AI tetap pakai output_language (UI=EN + output=ID → greeting ID)
- [ ] PostHog event `app_launched` menyertakan property `ui_language`

Catat hasil di GitHub Release notes. Kalau ada yang fail, **jangan rilis** — fix dulu atau dokumentasikan sebagai known issue.

### Alur Rilis Versi Baru

1. Buat branch baru dari `main` (misal `release/v1.0.14`)
2. Update `VERSION` di `version.py` (satu-satunya tempat)
3. Update tabel Version History di CLAUDE.md ini
4. Pastikan CI hijau: pytest + ruff lint pass di GitHub Actions
5. Jalankan `python build_production_exe_fixed.py`
6. **Jalankan Manual QA Checklist di atas** — kalau ada yang fail, stop rilis
7. Upload `dist/VocaLive-vX.X.X.zip` ke GitHub Releases: `https://github.com/arulbarker/vocalive-release/releases` dengan tag `vX.X.X`
8. Update `appscript.txt` bagian `VERSION_INFO["vocalive"]` → `latest`, `url` → deploy ulang ke Google Apps Script
9. Merge branch ke `main`

---

## Architecture

### Entry Point Flow

```
main.py
  → setup_validator (cek settings.json ada)
  → LicenseManager.is_license_valid() → AppScript HTTP (email-based)
      → jika gagal → show LicenseDialog (ui/license_dialog.py)
  → telemetry.init(POSTHOG_PROJECT_KEY, SENTRY_DSN, VERSION)
  → telemetry.set_user_context({"platform": "windows", "app_mode": APP_MODE})
  → telemetry.capture("app_launched")
  → QApplication + MainWindow (ui/main_window.py)
      → UpdateCheckThread (5 detik setelah startup)
      → LicenseMonitor (re-check setiap 4 jam)
      → UnifiedCommentProcessor (filter pipeline)
      → Tab: CohostTabBasic, ConfigTab, ProductSceneTab, AnalyticsTab, UserManagementTab
  → [app exit] → telemetry.close()  # flush Sentry session sebagai 'healthy'
```

`main.py` harus **pertama kali** set UTF-8 encoding untuk stdout/stderr sebelum import apapun — kritis di mode EXE.

### Module Split

| Direktori / File | Tanggung Jawab |
|------------------|----------------|
| `modules_client/` | GUI process: config, AI calls, TTS wrapper, license, analytics, updater, telemetry |
| `modules_server/` | TTS engine (Google Cloud REST + Gemini TTS + pygame playback) |
| `listeners/` | **Dead code** — listener aktif ada di `cohost_tab_basic.py` sebagai QThread inline |
| `ui/` | Semua tab PyQt6, design system di `theme.py` |
| `thirdparty/pytchat_ng/` | Fork pytchat yang dimodifikasi — **jangan ganti dengan pytchat dari pip** |
| `comprehensive_cleanup.py` | Cleanup resources saat app exit (pytchat, TTS, cache, storage) |
| `sales_templates.py` | Template prompt AI untuk mode jualan |
| `vtest_telemetry.py` | Verification test: cek koneksi PostHog + Sentry ke server (dev tool) |

**Dead code modules** (ada di disk tapi tidak aktif):
- `modules_client/chatgpt_ai.py` — provider lama, diganti Gemini/DeepSeek
- `ui/developer_tab.py` — tab yang belum diwiring ke MainWindow

`modules_client/tts_engine.py` adalah thin wrapper yang mendelegasikan ke `modules_server/tts_engine.py`.

### Comment Processing Pipeline

```
TikTok chat message
  → SimpleTikTokListener (QThread di cohost_tab_basic.py)
      → timestamp filter (skip history lama)
      → deduplication (hash-based)
  → UnifiedCommentProcessor (main_window.py)
      → blacklist/whitelist check (user_list_manager)
      → toxic keyword filter
      → spam detection (hash-based, 60s window)
      → cooldown check
  → CohostTabBasic.generate_cohost_reply()
  → generate_reply_with_scene() → AI reply + scene_id produk
  → TTS speak() → pygame playback
  → ProductPopupWindow (jika scene_id > 0)
```

### AI Provider Flow

`modules_client/api.py` → routing berdasarkan `ai_provider` di settings:

```
ai_provider == "gemini"   → modules_client/gemini_ai.py
                              → POST generativelanguage.googleapis.com
                              → model: gemini-3.1-flash-lite-preview
ai_provider == "deepseek" → modules_client/deepseek_ai.py
                              → POST api.deepseek.com
                              → model: deepseek-chat
```

Tidak ada fallback antar provider — error ditampilkan langsung ke user. `fast_mode=True` pakai timeout 5s dan max_tokens lebih kecil.

### TTS Flow

```
speak(text, voice_name)
  → modules_server/tts_engine.py
      → strip gender suffix "(FEMALE)"/"(MALE)" dari voice_name
      → voice starts with "Gemini-" → _speak_with_gemini()
          → POST generativelanguage.googleapis.com/gemini-2.5-flash-preview-tts
          → response: raw PCM (audio/L16, 24kHz mono)
          → wrap dengan WAV header via stdlib `wave` module
          → output: .wav temp file
      → else → _speak_with_api_key()
          → POST texttospeech.googleapis.com (Google Cloud TTS REST)
          → output: .mp3 temp file
      → fallback jika tidak ada api_key: pyttsx3
  → pygame playback (unload sebelum & sesudah untuk release file lock)
  → temp file dihapus setelah playback
```

**`_load_settings()` di `tts_engine.py`**: membaca `tts_voice`. Kondisi reload: `if not voice_name:` — bukan `if not voice_name and not language_code:`.

**Nama file temp**: berbasis timestamp millisecond (`tts_1744012345678.mp3`) — bukan hash teks — untuk menghindari Permission Denied saat preview berulang.

### License System (Email-based AppScript)

Sistem lisensi menggunakan **email login via Google Apps Script** — tidak ada service account key.

```
LicenseManager.is_license_valid()
  → load_license_data() → decrypt config/license.enc (Fernet, hardware-locked key)
  → check_session_online(email) → GET AppScript ?action=check&email=...&token=SHA256(device_fp)
      → status "AKTIF" → valid
      → status "EXPIRED" / "TIDAK_DITEMUKAN" → show login dialog
  → jika offline dan cache < 24 jam → allow (grace period)
```

- **`config/license.enc`** — session cache terenkripsi (Fernet). Key = PBKDF2HMAC dari device fingerprint (MAC+CPU+Disk+OS). Plain token tidak pernah disimpan.
- **`config/device.hash`** — hash fingerprint perangkat untuk hardware-lock
- **`config/license_config.json`** — override AppScript URL dan APP_SECRET (tidak di-commit, dibaca saat runtime)
- **`modules_client/license_monitor.py`** — re-check online setiap 4 jam saat runtime
- **`ui/license_dialog.py`** — email input UI, `LoginWorker(QThread)` untuk non-blocking AppScript call

AppScript URL aktif: **di-hardcode langsung di `modules_client/license_manager.py:35`** sebagai default. `config/license_config.json` hanya untuk override jika URL berubah — jika file ini tidak ada, URL default dari kode yang dipakai. Saat URL AppScript berubah, **update `license_manager.py:35` dulu**, baru `license_config.json`.

### Auto-Update System

```
MainWindow.__init__()
  → QTimer.singleShot(5000, _start_update_check)
      → UpdateCheckThread → GET AppScript ?action=version&product=vocalive
          → bandingkan dengan VERSION dari version.py
          → ada update → _on_update_found() → QMessageBox popup
              → user klik "Update Sekarang" → UpdateDialog (ui/update_dialog.py)
                  → DownloadThread → download ZIP dari GitHub
                  → install_update() → os.startfile(bat) → app quit 3s → batch copy EXE
                  → user buka VocaLive.exe MANUAL
```

- **`modules_client/updater.py`** — `check_for_update()`, `UpdateCheckThread`, `DownloadThread`, `install_update()`
- **`ui/update_dialog.py`** — progress bar download, pesan "buka manual", quit setelah 3 detik
- Tombol **"🔄 Cek Update"** di main window untuk cek manual
- Tombol **"⬆️ Update Tersedia!"** muncul di toolbar jika ada versi baru (orange, hidden by default)

**Kritis — Auto-Update: TIDAK ADA auto-launch:**
- Batch script **TIDAK** menjalankan `start "" VocaLive.exe` — menyebabkan DLL error (`_MEI` belum bersih)
- Setelah update, user diminta **buka manual** VocaLive.exe
- `update_dialog.py` quit app setelah **3 detik** (beri waktu user baca pesan)
- Batch tunggu **5 detik** → `taskkill` safety net → bersihkan `_MEI*` → copy EXE → selesai
- **JANGAN tambahkan kembali auto-launch** (`start ""`) di batch — DLL error pada beberapa perangkat

### Version Management

**`version.py`** adalah satu-satunya sumber kebenaran versi:

```python
VERSION = "1.0.14"          # ← SATU-SATUNYA TEMPAT GANTI VERSI
VERSION_WIN = "1.0.14.0"   # untuk EXE metadata Windows
VERSION_TUPLE = (1, 0, 14, 0)
```

Files yang import dari `version.py`: `updater.py`, `ui/main_window.py`, `main.py`, `build_production_exe_fixed.py`. Jangan hardcode versi di tempat lain.

### Product Scene System

Sistem popup video produk saat AI merespons terkait produk tertentu:
1. **`product_scene_manager.py`** — CRUD scenes, build product context string untuk prompt AI
2. **`product_scene_tab.py`** — UI manajemen daftar produk + video path
3. **`generate_reply_with_scene()`** di `api.py` — AI membalas + menentukan `scene_id` dalam satu call (JSON response)
4. **`product_popup_window.py`** — QDialog memutar video via QMediaPlayer

**`scene_id` BUKAN nomor keranjang TikTok** — hanya ID internal. Format daftar scene: `scene_id=N : nama` bukan `N. nama`. `scene_id = 0` = tidak tampilkan popup.

### Telemetry System (PostHog + Sentry)

**`modules_client/telemetry.py`** — never-crash wrapper untuk PostHog analytics + Sentry error tracking.

```python
# Panggil di main.py setelah license valid:
telemetry.init(POSTHOG_PROJECT_KEY, SENTRY_DSN, VERSION)
# → Sentry: set_user(device_id) + set_context("app") otomatis saat init

# Set user context (opsional, untuk enrichment):
telemetry.set_user_context({"platform": "windows", "app_mode": APP_MODE})
# → Sentry: set_context("user_context", extra)
# → PostHog: capture("$set", properties={"$set": extra})

# Kirim event custom:
telemetry.capture("event_name", {"key": "value"})

# Panggil sebelum app.quit():
telemetry.close()  # flush Sentry → session tercatat 'healthy' di Release Health
```

**Prinsip desain:**
- Semua SDK calls dibungkus `try/except Exception` — telemetry **tidak boleh crash app**
- Lazy import: `import posthog` / `import sentry_sdk` di dalam fungsi, bukan top-level
- `distinct_id` PostHog = device_id dari `config/device_id.dat` (sama dengan license system)
- `auto_session_tracking=True` di Sentry untuk Release Health (crash-free sessions %)
- **Korelasi PostHog ↔ Sentry**: kedua service pakai `device_id` yang sama sebagai user identifier
- `sentry_sdk.set_user({"id": device_id})` dipanggil saat init — setiap error ter-identifikasi per device
- `set_user_context()` pakai API modern (`set_context`, bukan `configure_scope` deprecated)

**Keys (di-hardcode di `main.py` sebagai default, bisa override via env var):**
- `POSTHOG_PROJECT_KEY` = `phc_uYwH9ByGUHwcPfnX4ThEUxePHMmycTRWictJoyTBnzSA`
- `SENTRY_DSN` = `https://61478c4ae40ad572269d7e6245405aae@o4511211608211456.ingest.us.sentry.io/4511213925367808`

**PostHog SDK v7 — Breaking Changes:**
- Host ingestion: `https://us.i.posthog.com` (bukan `app.posthog.com`)
- `capture()` signature: `posthog.capture(event, distinct_id=..., properties=...)` (bukan positional args lama)
- `close()` harus panggil `posthog.shutdown()` dulu sebelum `sentry_sdk.flush()` agar background thread selesai kirim
- **Tidak ada `posthog.identify()`** — set user properties via `posthog.capture("$set", properties={"$set": {...}})`

**Events yang di-track:**

| Event | File | Trigger |
|-------|------|---------|
| `app_launched` | `main.py` | Setiap startup berhasil (setelah license valid) |
| `tiktok_connected` | `cohost_tab_basic.py` | TikTok Live terhubung |
| `cohost_reply_generated` | `cohost_tab_basic.py` | AI reply dihasilkan (props: `scene_id`, `scene_name`, `provider`) |
| `tts_played` | `modules_server/tts_engine.py` | TTS berhasil diputar |
| `tts_failed` | `modules_server/tts_engine.py` | TTS gagal |
| `scene_triggered` | `ui/product_popup_window.py` | Popup produk ditampilkan (props: `scene_id`, `scene_name`) |
| `scene_dismissed` | `ui/product_popup_window.py` | Popup produk ditutup |
| `update_installed` | `modules_client/updater.py` | User install update baru |

**Build:** `posthog`, `sentry_sdk`, `sentry_sdk.integrations`, `sentry_sdk.integrations.stdlib`, `sentry_sdk.integrations.excepthook` harus ada di `hiddenimports` PyInstaller.

### Greeting System

1. **`config_tab.py`** — UI untuk mengisi 10 slot teks sapaan
2. **`greeting_tts_cache.py`** — Pre-render TTS tiap slot ke file audio (`greeting_cache/`). Gemini voice → `.wav`, lainnya → `.mp3`
3. **`sequential_greeting_manager.py`** — Timer-based playback, mode random

Interval timer diatur di Cohost Tab (bukan Config Tab).

**Path `greeting_cache/`**: selalu absolut — `Path(sys.executable).parent / "greeting_cache"` (frozen) atau `project_root / "greeting_cache"` (dev). Jangan pakai path relatif → Access Denied di EXE mode.

**Path `config/analytics/`**: sama, pakai `_get_app_root()` di `analytics_manager.py`.

### Internationalization (i18n)

VocaLive support bilingual UI: **Indonesia** dan **English**. UI language terpisah dari `output_language` AI (yang mengontrol bahasa AI ke viewer).

1. **`modules_client/i18n.py`** — JSON dict-based translation manager. API publik: `init()`, `t(key, **kwargs)`, `current_language()`, `set_language(lang)`
2. **`i18n/id.json`** dan **`i18n/en.json`** — flat dotted keys (`<area>.<component>.<element>`)
3. **Detection**: fresh install → deteksi Windows locale (id/ms → ID, en-* → EN). User existing update → force "id" (migrasi cegah kejutan)
4. **Switcher**: di Config Tab, apply setelah restart (bukan hot-reload)
5. **Coverage test**: `tests/test_i18n.py::TestKeyCoverage` memastikan setiap `t("key")` di source ada di kedua JSON

**Pattern refactor string widget:**

```python
from modules_client.i18n import t

# SEBELUM
btn = QPushButton("🚀 Mulai")
# SESUDAH
btn = QPushButton(t("cohost.btn.start"))
```

**Non-UI strings yang di-translate:** sales templates (`sales_templates.py` → `get_templates()` lazy), AI/TTS error messages, license dialog, update dialog.

**Non-UI strings yang TIDAK di-translate:**
- Developer log (`logger.*`) — konsisten untuk Sentry/MCP debugging
- Voice identifier (`Gemini-Puck`, `id-ID-Chirp3-*`)
- User data (greeting slots, product names, trigger_words, user_context, tiktok_nickname)
- `output_language` combo values (tetap literal "Indonesia"/"Malaysia"/"English")

**Special case — Greeting AI Generator prompt:** mengikuti `output_language` (bahasa viewer dengar AI), BUKAN `ui_language` (bahasa app UI). Diimplementasi via dict lookup terpisah di `greeting_ai_generator.py`, bukan lewat `t()`.

### TTS API Key Detection & Voice Filtering

Config tab tombol **🔍 Deteksi** — probe dua endpoint:
- `GET generativelanguage.googleapis.com/v1beta/models?key=...` → deteksi AI Studio key
- `GET texttospeech.googleapis.com/v1/voices?key=...` → deteksi Google Cloud key

Hasil disimpan ke `settings.json` sebagai `tts_key_type: "gemini" | "cloud" | "all"`.

Signal `ConfigTab.tts_key_type_changed(str)` → connect di `main_window.py` → `cohost_tab.update_voice_options()`. Voice dropdown otomatis filter berdasarkan tipe key.

### Config System

- `config/settings.json` — user config (tidak di-commit). Dibuat dari `settings_default.json` saat pertama kali.
- `config/settings_default.json` — template bersih tanpa API key, di-ship bersama EXE
- `config/voices.json` — daftar suara: `gtts_standard`, `chirp3`, `gemini_flash`. Chirp3 HD tidak tersedia untuk `ms-MY`.
- `config/product_scenes.json` — daftar produk + video path untuk popup scene
- `config/cohost_seller_products.json` — daftar produk untuk context prompt AI
- `config/user_lists.json` — blacklist/whitelist user TikTok
- `config/viewer_memory.json` — memory viewer yang pernah chat
- `config/live_state.json` — state sesi live terakhir
- `config/device_id.dat` — device fingerprint (JSON, dibuat license_manager)
- `config/database_maintenance.json` — jadwal maintenance cache/data
- `config/last_cleanup.json` — timestamp cleanup terakhir
- `modules_client/config_manager.py` — interface `cfg.get(key, default)` / `cfg.set(key, value)`

---

## UI Design System

**Semua styling harus menggunakan helper dari `ui/theme.py`.** Jangan hardcode warna di file tab.

```python
from ui.theme import btn_success, btn_danger, status_badge, ERROR, SUCCESS

self.start_button.setStyleSheet(btn_success("font-size: 13px;"))
self.stop_button.setStyleSheet(btn_danger())
self.status_indicator.setStyleSheet(status_badge(ERROR, size=13))
```

Helper tersedia: `btn_primary()`, `btn_success()`, `btn_danger()`, `btn_ghost()`, `btn_accent()`, `btn_secondary()`, `status_badge(color, size)`, `label_title()`, `label_subtitle()`, `label_value()`, `label_muted()`, `CARD_STYLE`, `CARD_ELEVATED_STYLE`, `HEADER_FRAME_STYLE`, `LOG_TEXTEDIT_STYLE`, `GLOBAL_QSS`.

Selalu sertakan fallback di blok `except ImportError` dengan nilai Ocean Blue (bukan gold lama).

---

## Key Config Fields

```json
{
  "platform": "TikTok",
  "ai_provider": "gemini",
  "paket": "basic",
  "output_language": "Indonesia",
  "trigger_words": ["bro", "bang", "min"],
  "viewer_cooldown_minutes": 3,
  "cohost_cooldown": 2,
  "cohost_max_queue": 4,
  "sequential_greeting_interval": 180,
  "greeting_play_mode": "random",
  "tiktok_nickname": "@username",
  "tts_voice": "Gemini-Puck (MALE)",
  "tts_key_type": "gemini",
  "google_tts_api_key": "",
  "api_keys": {
    "GEMINI_API_KEY": "",
    "DEEPSEEK_API_KEY": ""
  },
  "user_context": ""
}
```

`platform` saat ini hanya `"TikTok"` — YouTube di-disable di UI tapi kode tetap ada (dormant).

## Build Pitfalls — Wajib Dibaca Sebelum Modifikasi Build

### Kontrak antara `main.py` dan `build_production_exe_fixed.py`

`check_dependencies()` di `main.py` dan `excludes` di spec file **harus sinkron**. Jika sebuah library ada di `excludes` PyInstaller, jangan masukkan ke `required_modules` di `check_dependencies()` — EXE akan silent exit sebelum window muncul karena `return 1` terjadi tanpa dialog apapun (`console=False`).

Build script punya **dua lapis filter** untuk menjaga ukuran EXE kecil (~236MB):

1. **`excludes`** — mencegah PyInstaller trace import: `torch`, `transformers`, `tensorflow`, `scipy`, `numpy`, `cv2`, `OpenGL`, `langchain`, `sklearn`, `pyqtgraph`, `pytchat`, `pyvirtualcam`, dll.
2. **Post-Analysis bloat filter** (`_is_bloat()`) — menghapus binary/data/pure yang lolos dari excludes via transitive deps. Pattern: `torch`, `cuda`, `nvidia`, `OpenGL`, `cv2`, `onnx`, `transformers`, `langchain`, `Wav2Lip`, `dwpose`, dll.

Library yang wajib ada di `hiddenimports`: `cryptography.hazmat.primitives.*` (license), `pygame.mixer`, `keyboard`, `posthog`, `sentry_sdk.*`, `TikTokLive`, `betterproto`.

**Jangan tambah ke `datas`** folder source code (`ui/`, `modules_client/`, dll) — PyInstaller sudah collect `.py` via Analysis. Menambah folder ke `datas` menyebabkan duplikasi dan size bloat.

**Jangan tambah `thirdparty` ke `pathex`** — folder `thirdparty/` berisi dead code (Wav2Lip, dwpose) yang menarik torch/OpenGL/CUDA ke bundle.

### Silent Crash di EXE

EXE dibangun dengan `console=False` — tidak ada terminal, semua error sebelum window muncul **tidak terlihat user**. Saat debug EXE yang tidak mau terbuka, cek dua file ini setelah jalankan EXE:
- `logs/system.log` — startup log dari `main.py`
- `temp/error_log.txt` — uncaught exception yang di-catch oleh `handle_exception()`

### FFmpeg

FFmpeg **tidak disertakan** dalam build distribusi. Fitur Wav2Lip (lip-sync) sudah dihapus dari v1.0.0. `thirdparty/Wav2Lip/` adalah dead code — jangan ikutkan di build.

---

## Frozen EXE Considerations

- `getattr(sys, 'frozen', False)` dipakai untuk mendeteksi mode EXE dan adjust paths
- UTF-8 encoding fix di `main.py` harus berjalan **sebelum** import apapun
- Resource paths: `ROOT = os.path.dirname(sys.executable)` di mode EXE
- Splash screen di-disable (`splash = None`) untuk mencegah QPaintDevice segfault

## Product Popup Window — Rendering & Capture

**JANGAN pakai `QVideoWidget`** — render via D3D hardware overlay, tidak ter-capture OBS/TikTok Live Studio.
**Pakai `QVideoSink` + `QLabel.setPixmap()`** — frame lewat GDI pipeline, ter-capture normal.

**JANGAN pakai `WA_TranslucentBackground`** — transparent area ter-capture sebagai hitam.
Solusi capturable: **Chroma Key** — background `#00B140`, user apply filter di TikTok Live Studio.

**`QVBoxLayout(self)`** pada top-level widget → Qt auto-fill background → transparency gagal.
Gunakan `setAutoFillBackground(False)` + posisi manual via `setGeometry()` tanpa layout manager.

**`QVideoSink` thread safety**: `videoFrameChanged` emit dari multimedia thread.
Gunakan intermediate `pyqtSignal(QPixmap)` untuk pass frame ke main thread sebelum `setPixmap()`.

---

## Developer Tools — MCP Servers

MCP (Model Context Protocol) server dikonfigurasi di `~/.claude/settings.json` untuk Claude Code.

| Server | URL | Scope |
|--------|-----|-------|
| **Sentry** | `https://mcp.sentry.dev/mcp/arl-group` | Org `arl-group` (HTTP streamable) |
| **PostHog** | `https://mcp.posthog.com/mcp` | OAuth, US region (HTTP streamable) |
| **GitHub** | `npx @modelcontextprotocol/server-github` | PAT via env `GITHUB_PERSONAL_ACCESS_TOKEN` |
| **Chrome DevTools** | `npx chrome-devtools-mcp --autoConnect` | Local browser debugging |

Dengan MCP aktif, bisa tanya langsung ke Claude Code:
- *"Berapa app_launched events hari ini?"* → PostHog MCP
- *"Ada error baru di Sentry minggu ini?"* → Sentry MCP
- *"Buat feature flag baru di PostHog"* → PostHog MCP

**Monitoring**: Pantau langsung dari dashboard PostHog (https://us.posthog.com) dan Sentry (https://sentry.io). Tidak perlu dashboard custom — semua data events dan errors sudah terkirim ke server masing-masing.

---

## Protected Files (Jangan Diubah Tanpa Hati-Hati)

- `modules_server/tts_engine.py` — TTS engine multi-path auth
- `modules_client/license_manager.py` — AppScript email login + Fernet session cache
- `modules_client/config_manager.py` — sistem config pusat
- `thirdparty/pytchat_ng/` — fork custom, jangan replace dengan versi pip

## Sensitive Files (Never Commit)

`config/license.enc`, `config/device.hash`, `config/device_id.dat`, `config/license_config.json`, `config/settings.json`, `config/user_lists.json`, `config/viewer_memory.json`, `config/live_state.json`, `config/analytics/`, `.env`, `vtest_output.txt`

File legacy (masih ada di disk tapi tidak dipakai sistem baru): `config/sheet.json`, `config/gcloud_tts_credentials.json` — jangan commit, tapi juga tidak perlu dihapus.

---

## Setup Gemini API Key (Wajib untuk User Baru)

1. Buka [aistudio.google.com](https://aistudio.google.com) → **Get API Key**
2. Klik API key → bagian **API restrictions** → aktifkan **"Generative Language API"**
3. Tanpa langkah ini: **403 Permission Denied** meski key valid

Satu **Google Cloud Console** API key untuk semua jika di-enable di Restrictions:
- **AI** → `gemini-3.1-flash-lite-preview` via Generative Language API
- **Gemini TTS** → `gemini-2.5-flash-preview-tts` via Generative Language API (prefix `Gemini-*`)
- **Cloud TTS** → `texttospeech.googleapis.com` via Cloud Text-to-Speech API

Google AI Studio key hanya untuk Generative Language API — tidak support Cloud TTS Standard/Chirp3.

### Auth Format Gemini REST API

Gunakan **header** `x-goog-api-key`, bukan query param `?key=`:

```python
headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
payload = {
    "systemInstruction": {"role": "system", "parts": [{"text": system_prompt}]},
    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    "generationConfig": {"maxOutputTokens": 150, "temperature": 0.7},
}
requests.post(f"{GEMINI_API_BASE}/{model}:generateContent", headers=headers, json=payload)
```

---

## Re-enabling YouTube

YouTube di-disable bukan dihapus. Untuk re-enable:
1. `ui/cohost_tab_basic.py` — uncomment baris dropdown `addItems(["YouTube", "TikTok"])` dan blok `if platform == "YouTube":` di `start()`

---

# RULES OF ENGAGEMENT

> Baca dan ikuti seluruh aturan ini sebelum melakukan tindakan apapun.

## Git Workflow

- **Default branch: `main`** (branch `master` dan `versi12-masih-force-close` sudah dihapus)
- **SELALU** buat branch baru sebelum perubahan yang berarti. Format: `feat/`, `fix/`, `hotfix/`, `experiment/`
- **JANGAN** coding langsung di `main`
- Format commit wajib: `type: deskripsi (bahasa Indonesia)` — type valid: `feat fix refactor style docs chore security`
- Setelah commit, **selalu push** ke remote branch yang sama
- **JANGAN PERNAH** jalankan `git merge`, `git rebase main`, atau `git push --force` tanpa izin eksplisit

## Konfirmasi Sebelum Eksekusi

Untuk tindakan berikut, **WAJIB tanya user dulu**:

- Menghapus file atau folder apapun
- Mengubah struktur database / schema
- Menginstall dependency baru
- Mengubah file konfigurasi environment
- Refactor besar yang mengubah arsitektur
- Mengubah authentication / license logic

Format tanya: `"⚠️ Saya akan [tindakan]. Ini akan mempengaruhi [dampak]. Boleh lanjut?"`

## Larangan Keras

- JANGAN merge ke `main` tanpa izin
- JANGAN hapus file tanpa izin
- JANGAN commit credential/secret
- JANGAN install dependency tanpa konfirmasi
- JANGAN push --force tanpa izin eksplisit

## Laporan Setiap Sesi

Di akhir setiap sesi atau setelah selesai task:

```
## ✅ Yang Sudah Dikerjakan
- [list perubahan]

## 🌿 Branch & Commit
- Branch aktif: nama-branch
- Commit terakhir: pesan commit

## ⚡ Yang Perlu Diperhatikan
- [risiko, hal yang belum selesai, keputusan yang butuh input]

## 🔜 Langkah Selanjutnya (rekomendasi)
- [saran opsional]
```
