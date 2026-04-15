# Virtual Camera Tab — Design Spec

**Tanggal**: 2026-04-15
**Branch**: `feat/virtual-camera-tab`

## Tujuan

Menambahkan tab Virtual Camera di VocaLive agar user bisa memutar video file sebagai virtual webcam device. TikTok Live Studio yang mewajibkan webcam aktif akan membaca video ini sebagai kamera, sehingga user bisa menampilkan video produk saat live.

## User Flow

1. Buka tab Virtual Camera
2. Tambahkan video (1-10 file, format mp4/avi/mkv/mov)
3. Pilih mode: **Berurutan** atau **Acak**
4. Klik **Play** — video langsung terbaca sebagai virtual camera
5. Di TikTok Live Studio, pilih "OBS Virtual Camera" atau "Unity Video Capture" sebagai webcam

## Arsitektur

```
VirtualCameraTab (QWidget)
  → VirtualCameraManager
      → OpenCV cv2.VideoCapture (baca frame video)
      → pyvirtualcam.Camera (kirim frame ke virtual camera device)
      → Backend: OBS (primary) / UnityCapture (fallback)
```

### File Baru

| File | Tanggung Jawab |
|------|----------------|
| `ui/virtual_camera_tab.py` | Tab UI: playlist, kontrol play/stop/next, status |
| `modules_client/virtual_camera_manager.py` | Logic: video decode, frame send, playlist management |
| `config/virtual_camera.json` | Persist playlist & settings |

### Perubahan File Existing

| File | Perubahan |
|------|-----------|
| `ui/main_window.py` | Import & addTab VirtualCameraTab |
| `requirements.txt` | Tambah `pyvirtualcam`, `opencv-python-headless` |

## Driver Detection & Fallback

```
Tab dibuka / Play diklik
  → detect OBS Virtual Camera (registry DirectShow)
      → ada → backend = "obs"
  → tidak ada → detect UnityCapture
      → ada → backend = "unitycapture"
  → tidak ada dua-duanya →
      → tampilkan panel info: "Driver belum terinstall"
      → tombol "Download UnityCapture Driver" → buka URL GitHub release
      → notif: "Setelah install driver, restart VocaLive"
```

## VirtualCameraManager

### Class Design

```python
class VirtualCameraManager(QThread):
    statusChanged = pyqtSignal(str)        # "Playing video 3/10 — nama.mp4"
    errorOccurred = pyqtSignal(str)        # error message
    videoChanged = pyqtSignal(int, str)    # index, filename
    playbackFinished = pyqtSignal()        # semua video selesai (non-loop)

    def __init__(self):
        self.playlist: list[str] = []       # list path video
        self.play_mode: str = "sequential"  # "sequential" | "random"
        self.is_playing: bool = False
        self.current_index: int = 0
        self._cam = None                    # pyvirtualcam.Camera instance

    def start_playback(self)
    def stop_playback(self)
    def next_video(self)
    def set_playlist(self, paths: list[str])
    def set_play_mode(self, mode: str)
    def detect_backend(self) -> str | None  # "obs" / "unitycapture" / None
```

### Playback Loop (di QThread.run)

```python
def run(self):
    backend = self.detect_backend()
    if not backend:
        self.errorOccurred.emit("no_driver")
        return

    # Baca resolusi dari video pertama
    cap = cv2.VideoCapture(self.playlist[0])
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.release()

    # Buka virtual camera dengan resolusi asli video
    with pyvirtualcam.Camera(width, height, fps, backend=backend) as cam:
        self._cam = cam
        while self.is_playing:
            video_path = self._get_next_video()
            self._play_single_video(cam, video_path, fps)

def _play_single_video(self, cam, path, fps):
    cap = cv2.VideoCapture(path)
    while self.is_playing and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # OpenCV = BGR, pyvirtualcam = RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cam.send(frame_rgb)
        cam.sleep_until_next_frame()
    cap.release()
```

## UI Layout

```
+---------------------------------------------+
|  Virtual Camera                              |
+---------------------------------------------+
|  Status: [indicator] Streaming video 3/10    |
|  Backend: OBS Virtual Camera (detected)      |
+---------------------------------------------+
|  Playlist:                                   |
|  +--+----------------------------+--------+  |
|  |1 | produk_sepatu.mp4          | [Hapus] | |
|  |2 | demo_tas.mp4               | [Hapus] | |
|  |3 | promo_baju.mp4             | [Hapus] | |
|  +--+----------------------------+--------+  |
|  [+ Tambah Video]                            |
|                                              |
|  Mode: (o) Berurutan  ( ) Acak               |
|                                              |
|  [ Play ]  [ Stop ]  [ Next ]                |
+---------------------------------------------+
```

### Komponen UI

- **Status bar** — indicator warna + teks status (playing/stopped/error)
- **Backend info** — detected driver name
- **Playlist table** — QTableWidget, kolom: No, Filename, Hapus
- **Tambah Video** — QFileDialog multi-select, filter video files
- **Mode radio** — QRadioButton sequential/random
- **Kontrol** — 3 tombol: Play (btn_success), Stop (btn_danger), Next (btn_primary)
- **Driver install panel** — hanya muncul jika tidak ada driver terdeteksi

## Config Persistence

File: `config/virtual_camera.json`

```json
{
    "playlist": [
        "D:/Videos/produk1.mp4",
        "D:/Videos/produk2.mp4"
    ],
    "play_mode": "sequential",
    "last_backend": "obs"
}
```

## Spesifikasi Teknis

- **Resolusi**: asli video (semua video diasumsikan resolusi sama, user edit di CapCut)
- **FPS**: dari metadata video pertama, fallback 30
- **Format frame**: RGB (OpenCV BGR → convert ke RGB untuk pyvirtualcam)
- **Video format**: mp4, avi, mkv, mov (semua yang OpenCV support)
- **Max playlist**: 10 video
- **Loop**: playlist loop terus sampai Stop ditekan
- **Thread**: QThread terpisah agar UI tidak freeze

## Dependencies Baru

```
pyvirtualcam>=0.15.0
opencv-python-headless>=4.8.0
```

`opencv-python-headless` dipilih karena tidak perlu GUI window dari OpenCV (sudah pakai PyQt6).

## Error Handling

| Skenario | Handling |
|----------|----------|
| Tidak ada driver | Tampilkan panel install dengan link download |
| Video file corrupt/missing | Skip ke video berikutnya, log warning |
| Playlist kosong saat Play | Disable tombol Play, tampilkan pesan |
| Driver crash saat streaming | Emit error, auto-stop, tampilkan pesan restart |
| Semua video gagal dibaca | Stop playback, tampilkan error |

## Build Considerations

- `pyvirtualcam` dan `opencv-python-headless` harus masuk `hiddenimports` PyInstaller
- `cv2` memerlukan tambahan data files di spec (biasanya otomatis)
