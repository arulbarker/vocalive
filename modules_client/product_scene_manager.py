"""
ProductSceneManager - Load/save daftar produk untuk popup video overlay
"""

import json
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger('VocaLive')

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'product_scenes.json')

DEFAULT_CONFIG = {
    "popup_width": 608,
    "popup_height": 1080,
    "scenes": []
}


class ProductSceneManager:
    """Kelola daftar produk dan konfigurasi popup video."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.abspath(CONFIG_PATH)
        self._config = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.config_path):
            return dict(DEFAULT_CONFIG)
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Pastikan semua key ada
            for k, v in DEFAULT_CONFIG.items():
                data.setdefault(k, v)
            return data
        except Exception as e:
            logger.error(f"ProductSceneManager: gagal load config: {e}")
            return dict(DEFAULT_CONFIG)

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

    def add_scene(self, name: str, video_path: str) -> Dict:
        """Tambah produk baru. Return scene dict yang dibuat."""
        scenes = self.get_scenes()
        new_id = max((s["id"] for s in scenes), default=0) + 1
        scene = {"id": new_id, "name": name.strip(), "video_path": video_path}
        scenes.append(scene)
        self._config["scenes"] = scenes
        self.save()
        return scene

    def update_scene(self, scene_id: int, name: str = None, video_path: str = None):
        """Update nama atau path video scene."""
        for scene in self._config["scenes"]:
            if scene["id"] == scene_id:
                if name is not None:
                    scene["name"] = name.strip()
                if video_path is not None:
                    scene["video_path"] = video_path
                self.save()
                return

    def remove_scene(self, scene_id: int):
        """Hapus scene berdasarkan id."""
        self._config["scenes"] = [
            s for s in self._config["scenes"] if s["id"] != scene_id
        ]
        self.save()

    # --- Popup size ---

    def get_popup_size(self) -> tuple[int, int]:
        """Return (width, height)."""
        return self._config.get("popup_width", 608), self._config.get("popup_height", 1080)

    def set_popup_size(self, width: int, height: int):
        self._config["popup_width"] = width
        self._config["popup_height"] = min(height, 1080)  # max 1080
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
        product_list = "\n".join(f"{s['id']}. {s['name']}" for s in scenes)
        return (
            f"Produk yang tersedia (pilih scene_id yang paling relevan):\n"
            f"{product_list}\n\n"
            "Balas SELALU dalam format JSON berikut (wajib, tanpa teks lain di luar JSON):\n"
            '{"reply": "<teks balasan>", "scene_id": <nomor produk atau 0>}\n'
            "scene_id = 0 jika tidak ada produk yang relevan dengan percakapan."
        )
