"""Tests untuk ProductSceneManager — modules_client/product_scene_manager.py"""

import json
import pytest
from pathlib import Path

from modules_client.product_scene_manager import ProductSceneManager

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manager(config_path: str) -> ProductSceneManager:
    return ProductSceneManager(config_path=config_path)


def _make_empty_manager(tmp_path) -> ProductSceneManager:
    """Manager dengan config kosong (tidak ada scene)."""
    config_dir = tmp_path / "config_empty"
    config_dir.mkdir()
    empty_file = config_dir / "product_scenes_empty.json"
    empty_file.write_text(
        json.dumps({"popup_width": 608, "popup_height": 1080, "enabled": True, "scenes": []}),
        encoding="utf-8",
    )
    return ProductSceneManager(config_path=str(empty_file))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_get_scenes(tmp_product_scenes):
    """Harus return 2 scenes; scene pertama bernama 'Hijab Voal Premium'."""
    mgr = _make_manager(tmp_product_scenes)
    scenes = mgr.get_scenes()

    assert len(scenes) == 2
    assert scenes[0]["name"] == "Hijab Voal Premium"


def test_get_scene_by_id_found(tmp_product_scenes):
    """get_scene_by_id(1) harus return scene dengan id=1 dan nama yang benar."""
    mgr = _make_manager(tmp_product_scenes)
    scene = mgr.get_scene_by_id(1)

    assert scene is not None
    assert scene["id"] == 1
    assert scene["name"] == "Hijab Voal Premium"


def test_get_scene_by_id_not_found(tmp_product_scenes):
    """get_scene_by_id(999) harus return None."""
    mgr = _make_manager(tmp_product_scenes)
    result = mgr.get_scene_by_id(999)

    assert result is None


def test_add_scene(tmp_product_scenes):
    """Tambah scene baru — id harus 3 dan total scene menjadi 3."""
    mgr = _make_manager(tmp_product_scenes)
    new_scene = mgr.add_scene("Baju Koko", "videos/koko.mp4")

    assert new_scene is not None
    assert new_scene["id"] == 3
    assert len(mgr.get_scenes()) == 3


def test_add_scene_strips_name(tmp_product_scenes):
    """Nama dengan spasi di awal/akhir harus di-strip."""
    mgr = _make_manager(tmp_product_scenes)
    new_scene = mgr.add_scene("  Baju Koko  ", "videos/koko.mp4")

    assert new_scene["name"] == "Baju Koko"


def test_update_scene(tmp_product_scenes):
    """Update nama scene id=1 harus berhasil dan nilai baru terverifikasi."""
    mgr = _make_manager(tmp_product_scenes)
    success = mgr.update_scene(1, name="Hijab Voal Deluxe")

    assert success is True
    assert mgr.get_scene_by_id(1)["name"] == "Hijab Voal Deluxe"


def test_update_scene_not_found(tmp_product_scenes):
    """Update scene id=999 yang tidak ada harus return False."""
    mgr = _make_manager(tmp_product_scenes)
    result = mgr.update_scene(999, name="Ghost Scene")

    assert result is False


def test_remove_scene(tmp_product_scenes):
    """Hapus scene id=1 — scene tersebut tidak boleh ada lagi."""
    mgr = _make_manager(tmp_product_scenes)
    mgr.remove_scene(1)

    assert mgr.get_scene_by_id(1) is None
    assert len(mgr.get_scenes()) == 1


def test_get_enabled(tmp_product_scenes):
    """enabled harus True secara default (sesuai fixture)."""
    mgr = _make_manager(tmp_product_scenes)

    assert mgr.get_enabled() is True


def test_set_enabled(tmp_product_scenes):
    """set_enabled(False) harus mengubah nilai enabled menjadi False."""
    mgr = _make_manager(tmp_product_scenes)
    mgr.set_enabled(False)

    assert mgr.get_enabled() is False


def test_popup_size_clamps_width(tmp_product_scenes):
    """set_popup_size(2000, 500) — width harus diclamped ke 1920."""
    mgr = _make_manager(tmp_product_scenes)
    mgr.set_popup_size(2000, 500)
    width, height = mgr.get_popup_size()

    assert width == 1920
    assert height == 500


def test_build_product_context(tmp_product_scenes):
    """Context harus mengandung 'scene_id=1' dan 'BUKAN nomor keranjang'."""
    mgr = _make_manager(tmp_product_scenes)
    context = mgr.build_product_context()

    assert "scene_id=1" in context
    assert "BUKAN nomor keranjang" in context


def test_build_product_context_empty(tmp_path):
    """Manager tanpa scene harus return string kosong."""
    mgr = _make_empty_manager(tmp_path)
    context = mgr.build_product_context()

    assert context == ""


def test_add_scene_max_limit(tmp_path):
    """Setelah tepat 100 scene, add_scene berikutnya harus return None."""
    # Buat config dengan MAX_SCENES scene
    config_dir = tmp_path / "config_max"
    config_dir.mkdir()
    scenes = [
        {"id": i, "name": f"Produk {i}", "video_path": f"videos/produk_{i}.mp4"}
        for i in range(1, ProductSceneManager.MAX_SCENES + 1)
    ]
    config_data = {
        "popup_width": 608,
        "popup_height": 1080,
        "enabled": True,
        "scenes": scenes,
    }
    config_file = config_dir / "product_scenes_max.json"
    config_file.write_text(json.dumps(config_data, indent=2), encoding="utf-8")

    mgr = ProductSceneManager(config_path=str(config_file))

    assert len(mgr.get_scenes()) == ProductSceneManager.MAX_SCENES
    result = mgr.add_scene("Produk Overflow", "videos/overflow.mp4")

    assert result is None
