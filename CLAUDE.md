# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This App Does

**VocaLive** is a Windows desktop application for live streaming automation. It listens to YouTube/TikTok live chat, generates AI replies (ChatGPT/DeepSeek), converts them to speech (Google Cloud TTS / gTTS), and plays them during the stream. It is distributed as a licensed Windows EXE.

## Running the App

```bash
# Development mode
python main.py

# Build production EXE (Windows)
python build_production_exe_fixed.py
```

No test suite exists. Manual testing is done by running `python main.py` directly.

## Architecture

### Entry Point Flow
`main.py` → license validation (Google Sheets) → `ui/main_window.py` (MainWindow) → tabs created

### Module Split: `modules_client/` vs `modules_server/`
- **`modules_client/`** — runs in the GUI process: config, AI calls, TTS wrapper, listeners, analytics, license
- **`modules_server/`** — heavier services: `tts_engine.py` (Google Cloud TTS + pygame playback), `tts_google.py` (provider logic)
- `modules_client/tts_engine.py` is a thin wrapper that delegates to `modules_server/tts_engine.py`

### Comment Processing Pipeline
Chat message → `UnifiedCommentProcessor` (in `main_window.py`) → blacklist/whitelist → toxic filter → spam detection → cooldown → `CohostTabBasic.generate_cohost_reply()` → AI (ChatGPT/DeepSeek via `modules_client/api.py`) → TTS

### Listeners Run as Separate Processes
`listeners/pytchat_listener.py` and `listeners/tiktok_runner.py` are spawned as subprocesses to avoid blocking the PyQt6 GUI thread. They communicate back via signals/queues.

### Config System
All settings live in `config/settings.json` (user config). `config/settings_default.json` is the template/fallback. `modules_client/config_manager.py` handles read/write with a dict-like interface (`cfg.get(key, default)` / `cfg.set(key, value)`).

### UI Tabs (all in `ui/`)
| File | Tab name |
|------|----------|
| `cohost_tab_basic.py` | Cohost Basic (main feature) |
| `config_tab.py` | Konfigurasi |
| `analytics_tab.py` | Analytics |
| `user_management_tab.py` | User Management |
| `developer_tab.py` | Developer |

`config_tab.py` depends on `sales_templates.py` (root level) — if that import fails, the tab silently disappears because imports are wrapped in try/except in `main_window.py`.

### License System
- Hardware-locked: device fingerprint stored in `config/device.hash`, encrypted license in `config/license.enc`
- Validated against Google Sheets (`config/sheet.json` credentials)
- `modules_client/license_monitor.py` continuously monitors license validity at runtime

### TTS Flow
`speak(text)` → `modules_server/tts_engine.py` → Google Cloud TTS (if `config/gcloud_tts_credentials.json` present) → fallback to gTTS → plays via pygame

### AI Call Flow
`modules_client/api.py` → `http://localhost:8888` (local FastAPI) OR direct ChatGPT/DeepSeek API call depending on config. `fast_mode=True` uses aggressive timeout (80 tokens max) for quick responses.

## Protected Files (Do Not Modify Without Care)

Per `.cursorrules`:
- `modules_server/tts_engine.py` — TTS engine is stable
- `modules_client/pytchat_listener.py` — YouTube listener working
- `modules_client/license_manager.py` — license validation
- `modules_client/config_manager.py` — central config system

## Key Config Fields (`config/settings.json`)

```json
{
  "platform": "YouTube",          // or "TikTok"
  "paket": "basic",               // "basic" or "pro"
  "reply_language": "Indonesia",  // "Indonesia", "English", "Malaysian"
  "trigger_words": ["bro", "bang", "min"],
  "viewer_cooldown_minutes": 3,
  "OPENAI_API_KEY": "...",
  "DEEPSEEK_API_KEY": "..."
}
```

## Sensitive Files (Never Commit)

`config/gcloud_tts_credentials.json`, `config/google_token.json`, `config/sheet.json`, `config/license.enc`, `config/settings.json`, `.env`

## Frozen EXE Considerations

- `getattr(sys, 'frozen', False)` is used throughout to detect EXE mode and adjust paths
- `main.py` has a UTF-8 encoding fix for `stdout`/`stderr` that must run before any other import
- Resource paths use `ROOT = os.path.dirname(sys.executable)` in EXE mode
- Splash screen is disabled (`splash = None`) to prevent QPaintDevice segfault

---

# RULES OF ENGAGEMENT

> Baca dan ikuti seluruh aturan ini sebelum melakukan tindakan apapun.
> Aturan ini TIDAK BISA diabaikan kecuali ada instruksi eksplisit dari user.

## Git Workflow

### Branch
- **SELALU** buat branch baru sebelum melakukan perubahan apapun yang berarti
- Format nama branch:
  - Fitur baru → `feat/nama-fitur`
  - Bug fix → `fix/nama-bug`
  - Hotfix mendesak → `hotfix/nama-issue`
  - Eksperimen → `experiment/nama-percobaan`
- JANGAN pernah coding langsung di branch `main` atau `master`

### Commit
- Lakukan commit setiap kali ada perubahan yang bermakna
- Format pesan commit wajib:
  ```
  type: deskripsi singkat dalam bahasa Indonesia

  - Detail perubahan 1
  - Detail perubahan 2
  ```
  Type yang valid: `feat`, `fix`, `refactor`, `style`, `docs`, `test`, `chore`, `security`
- Commit harus atomic — satu commit = satu perubahan logis

### Push & Merge
- Setelah commit, **selalu push** ke remote branch yang sama
- **JANGAN PERNAH merge** ke `main`/`master` tanpa perintah eksplisit dari user
- **JANGAN PERNAH** jalankan `git merge`, `git rebase main`, atau `git push --force` tanpa izin

## Konfirmasi Sebelum Eksekusi

Untuk tindakan berikut, **WAJIB tanya user dulu** dan tunggu persetujuan:

- Menghapus file atau folder apapun
- Mengubah struktur database / schema migration
- Menginstall dependency baru
- Mengubah konfigurasi environment (`.env`, `config.js`, dll)
- Melakukan perubahan yang mempengaruhi lebih dari 3 file sekaligus
- Refactor besar yang mengubah arsitektur aplikasi
- Mengubah authentication / authorization logic

Format tanya: `"⚠️ Saya akan [tindakan]. Ini akan mempengaruhi [dampak]. Boleh lanjut?"`

## Keamanan

- **TIDAK PERNAH** hardcode API key, password, token, atau secret ke dalam kode
- Semua credential HARUS menggunakan environment variable
- Selalu cek apakah `.env` sudah ada di `.gitignore` sebelum commit
- Semua input dari user HARUS divalidasi dan di-sanitize sebelum diproses
- Gunakan parameterized query untuk semua operasi database (anti SQL injection)

## Struktur & Kualitas Kode

- Jangan ubah struktur folder yang sudah ada tanpa konfirmasi
- Setiap fungsi/komponen baru harus disertai komentar tujuannya
- Hindari fungsi yang terlalu panjang (>50 baris) — pecah menjadi fungsi kecil
- Hapus `print()` / `console.log` debugging sebelum commit
- Setiap API call WAJIB punya error handling

## Laporan Setiap Sesi

Di akhir setiap sesi atau setelah selesai task, berikan ringkasan:

```
## ✅ Yang Sudah Dikerjakan
- [list perubahan]

## 🌿 Branch & Commit
- Branch aktif: nama-branch
- Commit terakhir: pesan commit

## ⚡ Yang Perlu Diperhatikan
- [risiko, hal yang belum selesai, atau keputusan yang butuh input]

## 🔜 Langkah Selanjutnya (rekomendasi)
- [saran opsional]
```

## Larangan Keras

- JANGAN merge ke main tanpa izin
- JANGAN hapus file tanpa izin
- JANGAN commit credential/secret
- JANGAN abaikan error — selalu tangani atau laporkan
- JANGAN install dependency tanpa konfirmasi
- JANGAN push --force tanpa izin eksplisit
