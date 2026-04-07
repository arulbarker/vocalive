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

> Selalu cek tabel ini sebelum rilis agar tidak salah penomoran versi.

| Versi | Tanggal | Deskripsi |
|-------|---------|-----------|
| **v1.0.0** | 2026-04-05 | Versi awal — hapus Avatar Lip-sync & OBS Overlay, fokus Cohost AI + TTS |
| **v1.0.1** | 2026-04-07 | Tambah suara Malaysia (ms-MY), fix TTS preview, fix Gemini WAV header, Knowledge Produk AI polish |

**Versi saat ini: v1.0.1**

Versioning: `MAJOR` = breaking change, `MINOR` = fitur baru backward-compatible, `PATCH` = bug fix.

---

## What This App Does

**VocaLive** adalah Windows desktop app untuk live streaming automation. Mendengarkan chat **TikTok Live** (YouTube sementara di-disable), menghasilkan balasan AI (DeepSeek / Gemini 3.1 Flash Lite), mengubahnya ke suara (Google Cloud TTS / Gemini TTS), lalu memutarnya selama siaran. Didistribusikan sebagai EXE berlisensi.

## Running the App

```bash
# Development mode
python main.py

# Build production EXE (Windows)
python build_production_exe_fixed.py
```

Tidak ada test suite. Testing manual via `python main.py`. Pastikan `config/settings.json` berisi API key yang valid.

---

## Architecture

### Entry Point Flow

```
main.py
  → setup_validator (cek file kritis ada)
  → license validation (Google Sheets via config/sheet.json)
  → QApplication + MainWindow (ui/main_window.py)
      → UnifiedCommentProcessor (filter pipeline)
      → Tab: CohostTabBasic, ConfigTab, ProductSceneTab, AnalyticsTab, UserManagementTab, DeveloperTab
```

`main.py` harus **pertama kali** set UTF-8 encoding untuk stdout/stderr (ada di baris awal) sebelum import apapun — ini kritis di mode EXE.

### Module Split

| Direktori | Tanggung Jawab |
|-----------|----------------|
| `modules_client/` | Berjalan di GUI process: config, AI calls, TTS wrapper, listeners, analytics, license |
| `modules_server/` | TTS engine (Google Cloud REST + Gemini TTS + pygame playback) |
| `listeners/` | **Dead code** — `yt_listener_process.py` dan `tiktok_runner.py` tidak dipakai; listener aktif ada di `cohost_tab_basic.py` sebagai QThread inline |
| `ui/` | Semua tab PyQt6, design system di `theme.py` |
| `thirdparty/pytchat_ng/` | Fork pytchat yang dimodifikasi — **jangan ganti dengan pytchat dari pip** |

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

Tidak ada fallback antar provider — error ditampilkan langsung ke user. `fast_mode=True` pakai timeout 5s dan max_tokens lebih kecil untuk respons cepat.

### TTS Flow

```
speak(text, voice_name)
  → modules_server/tts_engine.py
      → strip gender suffix "(FEMALE)"/"(MALE)" dari voice_name
      → voice starts with "Gemini-" → _speak_with_gemini()
          → POST generativelanguage.googleapis.com/gemini-2.5-flash-preview-tts
          → response: raw PCM (audio/L16, 24kHz mono)
          → wrap dengan WAV header via stdlib `wave` module sebelum disimpan
          → output: .wav temp file
      → else → _speak_with_api_key()
          → POST texttospeech.googleapis.com (Google Cloud TTS REST)
          → output: .mp3 temp file
      → fallback jika tidak ada api_key: pyttsx3
  → pygame playback (unload sebelum & sesudah untuk release file lock)
  → temp file dihapus setelah playback
```

**Nama file temp**: berbasis timestamp millisecond (`tts_1744012345678.mp3`) — bukan hash teks — untuk menghindari Permission Denied saat voice sama di-preview berulang.

**Auth Google API key**: Satu **Google Cloud Console** API key bisa dipakai untuk keduanya jika kedua API di-enable di bagian Restrictions:
- `Cloud Text-to-Speech API` → untuk suara Standard (`id-ID-Standard-*`) dan Chirp3 HD
- `Generative Language API` → untuk Gemini AI + Gemini TTS (`Gemini-*` voices)

Google AI Studio key **hanya** berlaku untuk Generative Language API (Gemini), tidak bisa untuk Cloud TTS standard/chirp.

### Product Scene System

Sistem popup video produk saat AI merespons terkait produk tertentu:
1. **`product_scene_manager.py`** — CRUD scenes, build product context string untuk prompt AI
2. **`product_scene_tab.py`** — UI manajemen daftar produk + video path
3. **`generate_reply_with_scene()`** di `api.py` — AI membalas + menentukan `scene_id` dalam satu call (JSON response)
4. **`product_popup_window.py`** — QDialog yang memutar video produk via QMediaPlayer

### Knowledge Produk untuk AI (Config Tab)

Section "🧠 Pengetahuan Produk untuk AI" di Config Tab — user tulis daftar produk yang dijual (keranjang, harga, promo). AI membaca ini untuk menjawab komentar penonton.

Tombol **"✨ Sempurnakan dengan AI"** menjalankan `PolishKnowledgeThread` (QThread):
1. Cari info produk via DuckDuckGo Instant Answer API (gratis, no key)
2. Inject hasil riset ke prompt
3. AI poles teks → output: blok `## PERAN AI HOST` di atas + detail produk terstruktur
4. Tombol "↩️ Kembali ke Teks Asli" muncul untuk revert — teks asli disimpan di `self._original_context`

Teks disimpan ke `config/settings.json` field `user_context`, dibaca oleh `gemini_ai.py` dan `deepseek_ai.py` sebagai system context.

### Greeting System

Sistem sapaan otomatis terdiri dari 3 layer:
1. **`config_tab.py`** — UI untuk mengisi 10 slot teks sapaan
2. **`greeting_tts_cache.py`** — Pre-render TTS tiap slot ke file audio (hash-based caching di `greeting_cache/`). Gemini voice → `.wav`, lainnya → `.mp3`
3. **`sequential_greeting_manager.py`** — Timer-based playback, mode random, satu thread

Interval timer diatur di Cohost Tab (bukan Config Tab).

### Config System

- `config/settings.json` — user config (jangan di-commit)
- `config/settings_default.json` — template fallback
- `config/voices.json` — daftar semua suara per bahasa, dikelompokkan: `gtts_standard`, `chirp3`, `gemini_flash`. Struktur: `{ "section": { "locale": [ {model, gender} ] } }`. Gemini voices berlaku untuk semua bahasa (multilingual). Chirp3 HD **tidak tersedia** untuk `ms-MY` — hanya `id-ID` dan `en-*`. Jika `tts_voice` tersimpan di settings tidak ada di list terbaru, `cohost_tab_basic.py` auto-reset ke voice pertama yang valid.
- `modules_client/config_manager.py` — interface `cfg.get(key, default)` / `cfg.set(key, value)`

### License System

- Hardware-locked: fingerprint di `config/device.hash`, license terenkripsi di `config/license.enc`
- Validasi via Google Sheets (`config/sheet.json` credentials)
- `modules_client/license_monitor.py` — monitoring kontinu saat runtime

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
  "sequential_greeting_interval": 180,
  "tiktok_nickname": "@username",
  "google_tts_api_key": "AIzaSy...",
  "api_keys": {
    "GEMINI_API_KEY": "AIzaSy...",
    "DEEPSEEK_API_KEY": "sk-..."
  }
}
```

`platform` saat ini hanya `"TikTok"` — YouTube di-disable di UI tapi kode `SimpleListener` dan `video_id_input` tetap ada (dormant).

## Frozen EXE Considerations

- `getattr(sys, 'frozen', False)` dipakai untuk mendeteksi mode EXE dan adjust paths
- UTF-8 encoding fix di `main.py` harus berjalan **sebelum** import apapun
- Resource paths: `ROOT = os.path.dirname(sys.executable)` di mode EXE
- Splash screen di-disable (`splash = None`) untuk mencegah QPaintDevice segfault
- Default platform di `build_production_exe_fixed.py` baris ~492 harus `"TikTok"`

## Product Popup Window — Rendering & Capture

**JANGAN pakai `QVideoWidget`** untuk window yang perlu di-capture TikTok Live Studio / OBS.
`QVideoWidget` render via D3D hardware overlay → bypass GDI → tidak ter-capture.
**Pakai `QVideoSink` + `QLabel.setPixmap()`** — frame lewat GDI pipeline, ter-capture normal.

**JANGAN pakai `WA_TranslucentBackground`** untuk window yang di-capture — transparent area
ter-capture sebagai hitam (Windows OS limitation, tidak bisa di-fix via library apapun).
Solusi "tembus pandang" yang capturable: **Chroma Key** — background `#00B140` (broadcast green),
user apply Chroma Key filter di TikTok Live Studio.

**`QVBoxLayout(self)`** pada top-level widget menyebabkan Qt auto-fill background → transparency gagal.
Gunakan `setAutoFillBackground(False)` + posisi manual via `setGeometry()` tanpa layout manager.

**`QVideoSink` thread safety**: `videoFrameChanged` emit dari multimedia thread.
Gunakan intermediate `pyqtSignal(QPixmap)` untuk pass frame ke main thread sebelum `setPixmap()`.

**Toggle ON/OFF popup**: `ProductSceneManager.get_enabled()` / `set_enabled()` — state di `config/product_scenes.json`.
Check `get_enabled()` sebelum `show_product()` di `cohost_tab_basic.py`.

**AI pilih `scene_id`**: `scene_id = 0` = tidak tampilkan popup. AI sudah diinstruksikan untuk
pilih `scene_id > 0` hanya jika penonton bertanya spesifik tentang produk (bukan sapaan umum).

---

## Protected Files (Jangan Diubah Tanpa Hati-Hati)

- `modules_server/tts_engine.py` — TTS engine dengan multi-path auth
- `modules_client/license_manager.py` — validasi lisensi
- `modules_client/config_manager.py` — sistem config pusat
- `thirdparty/pytchat_ng/` — fork custom, jangan replace dengan versi pip

## Sensitive Files (Never Commit)

`config/gcloud_tts_credentials.json`, `config/google_token.json`, `config/sheet.json`, `config/license.enc`, `config/device.hash`, `config/settings.json`, `config/user_lists.json`, `.env`

---

## Setup Gemini API Key (Wajib untuk User Baru)

Gemini API key dari Google AI Studio perlu langkah ekstra sebelum bisa digunakan:

1. Buka [aistudio.google.com](https://aistudio.google.com) → **Get API Key**
2. Klik API key yang dibuat → bagian **API restrictions**
3. Aktifkan **"Generative Language API"** di daftar restrictions
4. Tanpa langkah ini, semua request ke Gemini akan return **403 Permission Denied** meski API key valid

Satu **Google Cloud Console** API key bisa untuk semua jika di-enable di Restrictions:
- **Otak AI** → `gemini-3.1-flash-lite-preview` via Generative Language API (auto-fallback ke `gemini-flash-lite-latest` jika 403)
- **Suara TTS Gemini** → `gemini-2.5-flash-preview-tts` via Generative Language API (voice prefix `Gemini-*`)
- **Suara Standard/Chirp3** → `texttospeech.googleapis.com` via Cloud Text-to-Speech API

Google AI Studio key hanya untuk Generative Language API — tidak support Cloud TTS.

### Auth Format Gemini REST API

Gunakan **header** `x-goog-api-key`, bukan query param `?key=`. Field system prompt menggunakan camelCase `systemInstruction`:

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
2. `build_production_exe_fixed.py` — ubah default platform kembali ke `"YouTube"` jika perlu

---

# RULES OF ENGAGEMENT

> Baca dan ikuti seluruh aturan ini sebelum melakukan tindakan apapun.

## Git Workflow

- **SELALU** buat branch baru sebelum perubahan yang berarti. Format: `feat/`, `fix/`, `hotfix/`, `experiment/`
- **JANGAN** coding langsung di `main` atau `master`
- Format commit wajib: `type: deskripsi (bahasa Indonesia)` — type valid: `feat fix refactor style docs chore security`
- Setelah commit, **selalu push** ke remote branch yang sama
- **JANGAN PERNAH** jalankan `git merge`, `git rebase main`, atau `git push --force` tanpa izin eksplisit

## Konfirmasi Sebelum Eksekusi

Untuk tindakan berikut, **WAJIB tanya user dulu**:

- Menghapus file atau folder apapun
- Mengubah struktur database / schema
- Menginstall dependency baru
- Mengubah file konfigurasi environment
- Refactor besar yang mengubah arsitektur (berbeda dari perubahan styling multi-file yang normal)
- Mengubah authentication / license logic

Format tanya: `"⚠️ Saya akan [tindakan]. Ini akan mempengaruhi [dampak]. Boleh lanjut?"`

## Larangan Keras

- JANGAN merge ke main tanpa izin
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
