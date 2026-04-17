"""
ProductSceneManager - Load/save daftar produk untuk popup video overlay
"""

from __future__ import annotations

import copy
import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger('VocaLive')

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'product_scenes.json')

DEFAULT_CONFIG = {
    "popup_width": 608,
    "popup_height": 1080,
    "enabled": True,
    "scenes": []
}


class ProductSceneManager:
    """Kelola daftar produk dan konfigurasi popup video."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.abspath(CONFIG_PATH)
        self._config = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.config_path):
            return copy.deepcopy(DEFAULT_CONFIG)
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Pastikan semua key ada
            for k, v in DEFAULT_CONFIG.items():
                data.setdefault(k, copy.deepcopy(v))
            return data
        except Exception as e:
            logger.error(f"ProductSceneManager: gagal load config: {e}")
            return copy.deepcopy(DEFAULT_CONFIG)

    def save(self):
        """Simpan config ke disk."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"ProductSceneManager: gagal save config: {e}")

    def reload(self):
        """Reload config dari disk (untuk refresh setelah user edit)."""
        self._config = self._load()

    # --- Scenes ---

    def get_scenes(self) -> List[Dict]:
        """Return list of scenes: [{"id": 1, "name": "...", "video_path": "..."}, ...]"""
        return self._config.get("scenes", [])

    def get_scene_by_id(self, scene_id: int) -> Optional[Dict]:
        """Return scene dict untuk id tertentu, atau None jika tidak ada."""
        for scene in self.get_scenes():
            if scene.get("id") == scene_id:
                return scene
        return None

    MAX_SCENES = 100

    def add_scene(self, name: str, video_path: str) -> Dict:
        """Tambah produk baru. Return scene dict yang dibuat, atau None jika sudah penuh."""
        scenes = self.get_scenes()
        if len(scenes) >= self.MAX_SCENES:
            logger.warning(f"ProductSceneManager: batas maksimal {self.MAX_SCENES} produk tercapai")
            return None
        new_id = max((s["id"] for s in scenes), default=0) + 1
        scene = {"id": new_id, "name": name.strip(), "video_path": video_path}
        scenes.append(scene)
        self._config["scenes"] = scenes
        self.save()
        return scene

    def update_scene(self, scene_id: int, name: str = None, video_path: str = None) -> bool:
        """Update nama atau path video scene. Return True jika berhasil, False jika scene_id tidak ditemukan."""
        for scene in self._config["scenes"]:
            if scene["id"] == scene_id:
                if name is not None:
                    scene["name"] = name.strip()
                if video_path is not None:
                    scene["video_path"] = video_path
                self.save()
                return True
        logger.warning(f"ProductSceneManager: scene_id {scene_id} tidak ditemukan untuk update")
        return False

    def remove_scene(self, scene_id: int):
        """Hapus scene berdasarkan id."""
        self._config["scenes"] = [
            s for s in self._config["scenes"] if s["id"] != scene_id
        ]
        self.save()

    # --- Enabled toggle ---

    def get_enabled(self) -> bool:
        return self._config.get("enabled", True)

    def set_enabled(self, value: bool):
        self._config["enabled"] = bool(value)
        self.save()

    # --- Popup size ---

    def get_popup_size(self) -> tuple[int, int]:
        """Return (width, height)."""
        return self._config.get("popup_width", 608), self._config.get("popup_height", 1080)

    def set_popup_size(self, width: int, height: int):
        self._config["popup_width"] = max(1, min(width, 1920))
        self._config["popup_height"] = min(height, 1080)
        self.save()

    # --- AI prompt helper ---

    def build_product_context(self) -> str:
        """
        Return string yang di-inject ke system prompt AI.
        Kosong jika tidak ada produk.
        """
        scenes = self.get_scenes()
        if not scenes:
            return ""
        product_list = "\n".join(f"scene_id={s['id']} : {s['name']}" for s in scenes)
        return (
            f"DAFTAR VIDEO SCENE (hanya untuk menentukan video yang ditampilkan, "
            f"BUKAN nomor keranjang belanja):\n"
            f"{product_list}\n\n"
            "PENTING: scene_id adalah ID video internal, BUKAN nomor keranjang TikTok. "
            "Informasi keranjang, harga, dan stok ada di knowledge produk. "
            "Jangan pernah menyebut 'keranjang [scene_id]' dalam balasan.\n\n"
            "Balas SELALU dalam format JSON berikut (wajib, tanpa teks lain di luar JSON):\n"
            '{"reply": "<teks balasan>", "scene_id": <scene_id video atau 0>}\n\n'
            "Aturan memilih scene_id:\n"
            "- Pilih scene_id yang nama scene-nya paling cocok dengan topik pertanyaan.\n"
            "- Gunakan scene_id > 0 HANYA jika penonton SECARA SPESIFIK bertanya tentang "
            "produk tersebut (harga, spesifikasi, warna, cara beli, stok, dll).\n"
            "- Gunakan scene_id = 0 untuk sapaan umum, pertanyaan non-produk, "
            "atau komentar yang tidak butuh penjelasan produk.\n"
            "- Jangan tampilkan video hanya karena komentar menyebut kata mirip nama produk."
        )
