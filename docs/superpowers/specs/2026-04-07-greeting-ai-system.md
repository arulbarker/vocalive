# Greeting AI System — Design Spec
**Date:** 2026-04-07  
**Status:** Approved  
**Branch target:** `feat/greeting-ai-system`

---

## Latar Belakang & Masalah

Fitur sapaan (greeting) VocaLive saat ini menyimpan teks manual di 10 slot dan merender sekali menjadi file audio cache. File yang **identik secara bit-for-bit** diputar berulang setiap interval tetap (default 3 menit).

Hal ini menimbulkan dua risiko deteksi spam oleh TikTok:

1. **Audio fingerprint identik** — file `.wav`/`.mp3` yang sama diputar berulang → sistem fingerprinting TikTok (mirip Shazam) dapat mendeteksinya sebagai konten otomatis/bot
2. **Pola interval mekanikal** — interval tepat 180 detik tanpa variasi → sinyal kuat bahwa ini bukan manusia

Ada laporan satu pengguna ter-banned, diduga kuat karena pola ini.

---

## Tujuan

- Hapus risiko audio fingerprint identik secara permanen
- Hapus pola interval mekanikal
- Tidak menambah dependency baru ke build
- Permudah UI: user tidak perlu isi 10 slot manual, cukup ON/OFF

---

## Solusi: Greeting AI System

### Konsep Inti

AI (Gemini) generate 10 teks sapaan unik setiap 2 jam menggunakan konteks dari tab Knowledge. Semua 10 teks di-render TTS ke audio baru. Sistem putar acak dengan interval yang di-jitter ±25%.

Hasil: setiap 2 jam fingerprint audio berubah total. Dalam satu sesi streaming, pola tidak pernah mekanikal.

---

## Alur Sistem (Background)

```
Greeting AI aktif (ON)
  │
  ├─ Startup
  │   ├── Baca user_context dari settings.json
  │   ├── Gemini generate 10 teks sapaan (plain text, tanpa tanda baca)
  │   ├── clean_greeting_text() — strip simbol sisa
  │   ├── TTS pre-render semua 10 → greeting_cache/ai_slot_{n}_{timestamp}.*
  │   └── Mulai timer playback + schedule regenerasi 2 jam
  │
  ├─ Loop Playback (berjalan terus)
  │   ├── Pilih slot acak dari 10
  │   ├── Putar audio dari cache
  │   ├── Tunggu: interval_base × random(0.75, 1.25)
  │   └── Ulangi
  │
  └─ Setiap 2 jam (regenerasi)
      ├── Generate 10 teks baru via Gemini
      ├── Render TTS ke nama file SEMENTARA (ai_slot_{n}_new.*)
      ├── Setelah SEMUA 10 selesai → swap atomik (ganti referensi)
      ├── Hapus file set lama
      └── Update timestamp "last_updated"
```

**Kenapa atomic swap:** render ke file sementara dulu, baru ganti referensi setelah semua siap. Mencegah crash/miss jika playback sedang berjalan saat regenerasi.

---

## AI Prompt untuk Generate Sapaan

```
Buatkan 10 variasi sapaan untuk live streaming TikTok
Syarat ketat:
- Setiap sapaan 1 sampai 2 kalimat natural dan percakapan
- Semua 10 sapaan berbeda satu sama lain dalam variasi kata gaya dan panjang
- Sesuai konteks berikut: {user_context}
- JANGAN gunakan tanda baca apapun termasuk titik koma tanda seru tanda tanya tanda kutip
- JANGAN gunakan simbol markdown seperti bintang garis bawah pagar atau tanda kurung
- Hanya huruf biasa dan spasi
Format respons: JSON array dengan tepat 10 string
["sapaan1", "sapaan2", "sapaan3", ...]
```

---

## Post-Processing (Defensive Layer)

Setelah dapat response dari Gemini, sebelum dikirim ke TTS:

```python
import re

def clean_greeting_text(text: str) -> str:
    """Strip semua simbol — hanya huruf, angka, dan spasi."""
    cleaned = re.sub(r'[^\w\s]', '', text)
    return ' '.join(cleaned.split())  # normalize spasi berlebih
```

Berlaku walaupun prompt sudah ketat — safety net jika Gemini tetap menambahkan simbol.

---

## Interval Jitter

```python
import random

def get_jittered_interval(base_seconds: int) -> float:
    """Tambah ±25% variasi acak pada interval."""
    factor = random.uniform(0.75, 1.25)
    return base_seconds * factor
```

Contoh: interval 180 detik → aktual antara 135–225 detik. Tidak pernah persis sama.

---

## Perubahan File

### `modules_client/sequential_greeting_manager.py`
- Tambah method `generate_greetings_with_ai()` — panggil Gemini, parse JSON response
- Tambah method `_prerender_all_slots(slot_texts, suffix)` — TTS batch render
- Tambah method `_atomic_swap_slots(new_suffix)` — swap referensi file
- Modifikasi `_schedule_next_greeting()` — pakai `get_jittered_interval()`
- Tambah `_schedule_regeneration()` — timer 2 jam untuk auto-regen
- Slot data tidak lagi dibaca dari `settings.json` (no more `custom_greeting_slot_N`), tapi dari memory (list of 10 texts)

### `modules_client/greeting_tts_cache.py`
- Tambah method `prerender_batch(texts, voice_name, language_code, suffix)` — render semua teks ke file dengan suffix tertentu
- Tambah method `swap_batch(old_suffix, new_suffix)` — atomic swap
- Tambah method `cleanup_batch(suffix)` — hapus file set lama

### `ui/config_tab.py`
- **Hapus:** 10 QLineEdit slot manual + label-labelnya
- **Tambah:** Toggle ON/OFF `QCheckBox` atau `QPushButton` berlabel "🤖 Greeting AI"
- **Tambah:** Status label — "✅ Aktif — 10 sapaan tersedia" / "⏳ Sedang generate..."
- **Tambah:** Label timestamp — "Diperbarui: 14:32 (47 menit lalu)"
- **Tambah:** Tombol `🔄 Generate Ulang Sekarang` — manual trigger regenerasi
- Keterangan kecil: "Sapaan dibuat otomatis dari konteks Knowledge setiap 2 jam"

### `config/settings.json` (field baru)
```json
{
  "greeting_ai_enabled": false,
  "greeting_ai_last_updated": null
}
```
- `greeting_ai_interval_seconds` **tidak ada** — pakai `sequential_greeting_interval` yang sudah ada (tetap bisa diatur user via UI seperti sekarang)
- Siklus regenerasi AI **hardcode 2 jam** (7200 detik), tidak exposed ke UI
- Field lama `custom_greeting_slot_1` s/d `custom_greeting_slot_10` tetap ada di file (backward compat) tapi tidak dipakai sistem baru

---

## Error Handling

| Skenario | Penanganan |
|----------|-----------|
| Gemini gagal generate (API error) | Retry 1x setelah 30 detik. Jika tetap gagal, lanjut pakai slot lama sampai regen berikutnya |
| Response Gemini bukan valid JSON | Fallback parse per-baris, ambil baris yang valid saja |
| TTS gagal render satu slot | Skip slot tersebut, lanjut render slot lain. Slot yang gagal tidak masuk rotasi |
| Semua TTS gagal | Log error, Greeting AI tetap ON tapi diam (tidak crash) |
| user_context kosong | Pakai fallback prompt generik: "sapaan untuk live streaming jualan online" |

---

## Batasan & Trade-off

- **API cost:** 10 TTS call setiap 2 jam. Untuk stream 4 jam = 20 TTS calls. Wajar untuk Gemini TTS.
- **Startup delay:** Ada jeda ~5–15 detik saat pertama aktif (generate + render 10 audio). Tampilkan spinner "Sedang menyiapkan sapaan...".
- **Field lama di settings.json:** Tidak dihapus untuk backward compat. User yang downgrade ke versi lama tidak kehilangan data.
- **Tidak ada audio jitter (pydub):** Tidak diperlukan karena teks baru = audio baru = fingerprint baru secara alami.

---

## Yang TIDAK Berubah

- `modules_server/tts_engine.py` — tidak disentuh
- `modules_client/license_manager.py` — tidak disentuh
- Logika pause/resume saat trigger aktif tetap berjalan seperti sekarang
- `custom_greeting_manager.py` — dibiarkan (dead code, tidak dipakai)

---

## Kriteria Selesai

- [ ] Toggle ON/OFF berfungsi, state tersimpan di settings.json
- [ ] Saat ON, Gemini generate 10 teks dalam 15 detik pertama
- [ ] Semua 10 teks ter-render ke audio tanpa simbol/tanda baca
- [ ] Playback berjalan acak dengan interval bervariasi (tidak tepat sama)
- [ ] Setelah 2 jam, 10 audio baru di-swap tanpa crash/interupsi playback
- [ ] Tombol "Generate Ulang" memicu regenerasi manual
- [ ] Jika Gemini gagal, sistem tidak crash dan pakai audio lama
- [ ] Status UI update realtime (last updated, jumlah slot aktif)
