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

**Versi saat ini: v1.0.0**

Versioning: `MAJOR` = breaking change, `MINOR` = fitur baru backward-compatible, `PATCH` = bug fix.

---

## What This App Does

**VocaLive** adalah Windows desktop app untuk live streaming automation. Mendengarkan chat YouTube/TikTok Live, menghasilkan balasan AI (ChatGPT/DeepSeek), mengubahnya ke suara (Google Cloud TTS / gTTS), lalu memutarnya selama siaran. Didistribusikan sebagai EXE berlisensi.

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
      → Tab: CohostTabBasic, ConfigTab, AnalyticsTab, UserManagementTab, DeveloperTab
```

`main.py` harus **pertama kali** set UTF-8 encoding untuk stdout/stderr (ada di baris awal) sebelum import apapun — ini kritis di mode EXE.

### Module Split

| Direktori | Tanggung Jawab |
|-----------|----------------|
| `modules_client/` | Berjalan di GUI process: config, AI calls, TTS wrapper, listeners, analytics, license |
| `modules_server/` | Service berat: TTS engine (Google Cloud + pygame), provider logic |
| `listeners/` | Subprocess terpisah: `pytchat_listener.py` (YouTube), `tiktok_runner.py` (TikTok) |
| `ui/` | Semua tab PyQt6, design system di `theme.py` |
| `thirdparty/pytchat_ng/` | Fork pytchat yang dimodifikasi — **jangan ganti dengan pytchat dari pip** |

`modules_client/tts_engine.py` adalah thin wrapper yang mendelegasikan ke `modules_server/tts_engine.py`.

### Comment Processing Pipeline

```
Chat message
  → UnifiedCommentProcessor (main_window.py)
      → blacklist/whitelist check (user_list_manager)
      → toxic keyword filter
      → spam detection (hash-based, 60s window)
      → cooldown check
  → CohostTabBasic.generate_cohost_reply()
  → AI reply (modules_client/api.py → localhost:8888 atau langsung ke ChatGPT/DeepSeek)
  → TTS speak() → pygame playback
```

### AI Call Flow

`modules_client/api.py` selalu mengarah ke `http://localhost:8888` (local FastAPI server). `fast_mode=True` menggunakan timeout agresif (80 tokens max) untuk respons cepat. `modules_client/chatgpt_ai.py` dan `modules_client/deepseek_ai.py` adalah direct AI clients alternatif.

### Greeting System

Sistem sapaan otomatis terdiri dari 3 layer:
1. **`config_tab.py`** — UI untuk mengisi 10 slot teks sapaan
2. **`greeting_tts_cache.py`** — Pre-render TTS tiap slot ke file audio (hash-based caching di `greeting_cache/`)
3. **`sequential_greeting_manager.py`** — Timer-based playback, mode random, satu thread

Interval timer diatur di Cohost Tab (bukan Config Tab). File audio cache disimpan agar tidak panggil TTS API berulang.

### Config System

- `config/settings.json` — user config (jangan di-commit)
- `config/settings_default.json` — template fallback
- `modules_client/config_manager.py` — interface `cfg.get(key, default)` / `cfg.set(key, value)`

### License System

- Hardware-locked: fingerprint di `config/device.hash`, license terenkripsi di `config/license.enc`
- Validasi via Google Sheets (`config/sheet.json` credentials)
- `modules_client/license_monitor.py` — monitoring kontinu saat runtime

### TTS Flow

```
speak(text)
  → modules_server/tts_engine.py
      → Google Cloud TTS (jika config/gcloud_tts_credentials.json ada)
      → fallback: gTTS
  → pygame playback
```

---

## UI Design System

**Semua styling harus menggunakan helper dari `ui/theme.py`.** Jangan hardcode warna di file tab.

### Helper yang Tersedia

| Helper | Kegunaan |
|--------|---------|
| `btn_primary()` | Tombol utama — background biru |
| `btn_success()` | Tombol aksi positif — hijau |
| `btn_danger()` | Tombol destruktif — merah |
| `btn_ghost()` | Tombol sekunder — transparan subtle |
| `btn_accent()` | Tombol emphasis — accent biru muda |
| `btn_secondary()` | Tombol outline biru |
| `status_badge(color, size)` | Label status dengan border berwarna |
| `label_title(size)` | Judul section — biru, bold |
| `label_subtitle(size)` | Sub-judul — muted |
| `label_value(size)` | Angka besar metric — bold |
| `label_muted(size)` | Teks redup |
| `CARD_STYLE` | QFrame card standar |
| `CARD_ELEVATED_STYLE` | QFrame card elevated |
| `HEADER_FRAME_STYLE` | Frame header dengan border bawah |
| `LOG_TEXTEDIT_STYLE` | QTextEdit log/console style |
| `GLOBAL_QSS` | Global stylesheet — diapply di MainWindow |

### Cara Pakai

```python
from ui.theme import btn_success, btn_danger, status_badge, ERROR, SUCCESS

self.start_button.setStyleSheet(btn_success("font-size: 13px;"))
self.stop_button.setStyleSheet(btn_danger())
self.status_indicator.setStyleSheet(status_badge(ERROR, size=13))
```

Selalu sertakan fallback di blok `except ImportError` dengan nilai Ocean Blue (bukan gold lama).

---

## Key Config Fields

```json
{
  "platform": "YouTube",
  "paket": "basic",
  "output_language": "Indonesia",
  "trigger_words": ["bro", "bang", "min"],
  "viewer_cooldown_minutes": 3,
  "cohost_cooldown": 2,
  "sequential_greeting_interval": 180,
  "OPENAI_API_KEY": "...",
  "DEEPSEEK_API_KEY": "..."
}
```

## Frozen EXE Considerations

- `getattr(sys, 'frozen', False)` dipakai untuk mendeteksi mode EXE dan adjust paths
- UTF-8 encoding fix di `main.py` harus berjalan **sebelum** import apapun
- Resource paths: `ROOT = os.path.dirname(sys.executable)` di mode EXE
- Splash screen di-disable (`splash = None`) untuk mencegah QPaintDevice segfault

## Protected Files (Jangan Diubah Tanpa Hati-Hati)

- `modules_server/tts_engine.py` — TTS engine stabil
- `modules_client/pytchat_listener.py` — YouTube listener berjalan
- `modules_client/license_manager.py` — validasi lisensi
- `modules_client/config_manager.py` — sistem config pusat
- `thirdparty/pytchat_ng/` — fork custom, jangan replace dengan versi pip

## Sensitive Files (Never Commit)

`config/gcloud_tts_credentials.json`, `config/google_token.json`, `config/sheet.json`, `config/license.enc`, `config/device.hash`, `config/settings.json`, `config/user_lists.json`, `.env`

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
