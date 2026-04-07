# Product Video Popup — Design Spec

**Tanggal:** 2026-04-06  
**Branch target:** `feat/product-video-popup`  
**Status:** Approved, siap implementasi

---

## Ringkasan

Fitur overlay video produk untuk TikTok Live Studio. Saat AI menjelaskan produk, sebuah popup window vertikal muncul dan memutar video produk yang relevan. Setelah TTS selesai berbicara, popup otomatis hilang sehingga karakter/avatar streamer terlihat kembali.

User tidak perlu OBS. TikTok Live Studio cukup menangkap popup window ini sebagai "Window Capture" source di layer atas kamera.

---

## Komponen Baru

### File yang dibuat

| File | Tanggung Jawab |
|------|----------------|
| `ui/product_scene_tab.py` | Tab UI untuk kelola daftar produk (nama + file video) |
| `ui/product_popup_window.py` | Jendela overlay frameless, always-on-top, putar video |
| `modules_client/product_scene_manager.py` | Load/save `config/product_scenes.json` |

### File yang dimodifikasi

| File | Perubahan |
|------|-----------|
| `modules_client/api.py` | Tambah `scene_id` di JSON response dari AI |
| `modules_client/chatgpt_ai.py` | Inject daftar produk ke system prompt, parse JSON response |
| `modules_client/deepseek_ai.py` | Sama seperti chatgpt_ai.py |
| `ui/main_window.py` | Tambah ProductSceneTab, inisialisasi ProductPopupWindow |
| `ui/cohost_tab_basic.py` | Setelah dapat AI reply, trigger popup berdasarkan scene_id |

### File baru (config)

| File | Isi |
|------|-----|
| `config/product_scenes.json` | Daftar produk: id, nama, path video. Popup size. |

---

## Arsitektur & Flow

```
Chat masuk
  → AI call (api.py / chatgpt_ai.py / deepseek_ai.py)
      → system prompt menyertakan daftar produk bernomor
      → response JSON: { "reply": "...", "scene_id": 4 }
  → cohost_tab_basic.py parse scene_id
      → scene_id == 0 → skip popup, TTS jalan normal
      → scene_id > 0  → lookup video path dari product_scene_manager
  → TTS speak(reply) dimulai (pygame)
  → ProductPopupWindow.show_product(video_path)
      → window.show()
      → QMediaPlayer.play(video), loop aktif
  → TTS watcher thread
      → cek pygame.mixer.music.get_busy() tiap 200ms
      → TTS selesai → QMetaObject.invokeMethod(window, "hide")
  → Popup hilang, karakter streamer terlihat lagi
```

---

## ProductPopupWindow

- PyQt6 `QWidget` dengan flags: `FramelessWindowHint | WindowStaysOnTopHint | Tool`
- Background: hitam penuh (bukan transparan — transparan tidak di-support semua driver)
- Video player: `QMediaPlayer` + `QVideoWidget`
- Default size: **608 × 1080** (9:16, max height 1080px)
- Width bisa diatur user, height dikunci max 1080
- `show_product(video_path)`: load video, play, loop sampai di-hide
- `hide()`: stop player, sembunyikan window

**Catatan TikTok Live Studio:** User setup sekali — tambah "Window Capture", pilih window "VocaLive Product Display", taruh di layer atas kamera. Saat window hide, source otomatis blank/hitam.

---

## UI Tab: Product Scene Manager

```
┌─────────────────────────────────────────────────────┐
│  Product Scene Manager                               │
├─────────────────────────────────────────────────────┤
│  [+ Tambah Produk]  [Hapus]  [Test Tampilkan]       │
├────┬──────────────────────────┬─────────────────────┤
│ No │ Nama Produk              │ File Video           │
├────┼──────────────────────────┼─────────────────────┤
│  1 │ Celana Jeans Slim        │ celana_jeans.mp4  📁 │
│  2 │ Baju Batik Premium       │ batik_premium.mp4 📁 │
│  3 │ Topi Baseball            │ topi_baseball.mp4 📁 │
└────┴──────────────────────────┴─────────────────────┘
  Popup Size: [608] x [1080]  [Preview Window]
```

- Klik 📁 → QFileDialog pilih MP4
- **Test Tampilkan** → show_product() tanpa harus live
- **Preview Window** → buka popup kosong agar user bisa posisikan di TikTok Live Studio
- Nama produk yang jelas = kunci AI bisa memilih scene yang tepat

---

## Format Config: product_scenes.json

```json
{
  "popup_width": 608,
  "popup_height": 1080,
  "scenes": [
    { "id": 1, "name": "Celana Jeans Slim", "video_path": "C:/Videos/celana_jeans.mp4" },
    { "id": 2, "name": "Baju Batik Premium", "video_path": "C:/Videos/batik_premium.mp4" },
    { "id": 3, "name": "Topi Baseball", "video_path": "C:/Videos/topi_baseball.mp4" }
  ]
}
```

---

## AI Prompt Injection

Daftar produk di-inject ke system prompt setiap kali AI dipanggil:

```
Produk yang tersedia (gunakan scene_id sesuai nomor):
1. Celana Jeans Slim
2. Baju Batik Premium
3. Topi Baseball

Balas SELALU dalam format JSON:
{"reply": "<teks balasan>", "scene_id": <nomor atau 0>}

scene_id = 0 jika tidak ada produk yang relevan dengan percakapan.
```

Response AI di-parse: ambil `reply` untuk TTS, ambil `scene_id` untuk popup.

---

## Edge Cases

| Situasi | Handling |
|---------|----------|
| Video lebih pendek dari TTS | Loop video sampai TTS selesai |
| Video lebih panjang dari TTS | Stop video + hide window saat TTS selesai |
| scene_id = 0 | Tidak tampilkan popup, TTS jalan normal |
| Produk ke-2 datang saat popup masih aktif | Ganti video langsung, reset watcher thread |
| File video tidak ditemukan | Log error, skip popup, TTS tetap jalan |
| AI reply bukan JSON valid | Fallback: treat seluruh response sebagai reply, scene_id = 0 |

---

## Thread Safety

TTS watcher berjalan di background thread. Hide window **harus** dipanggil dari Qt main thread:

```python
QMetaObject.invokeMethod(popup_window, "hide", Qt.ConnectionType.QueuedConnection)
```

Pola ini konsisten dengan `sequential_greeting_manager.py` yang sudah ada.

---

## Tidak Termasuk Scope

- Animasi transisi masuk/keluar popup (fade, slide)
- Overlay teks harga/nama produk di atas video
- Auto-trigger dari keyword chat (bukan dari AI reply)
- Upload/hosting video online
