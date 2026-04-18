"""
Tests untuk sales_templates.py — helper functions backward-compat dengan i18n.

Catatan: setelah refactor i18n (Task 17), `TEMPLATES` module-level sudah
dihapus. File ini sekarang menguji helper backward-compat (`get_template`,
`get_template_list`) yang internal memanggil `get_templates()` lazy.
"""

import json
from pathlib import Path

import pytest

from sales_templates import (
    TEMPLATE_KEYS,
    get_template,
    get_template_list,
    get_templates,
)

pytestmark = pytest.mark.unit

REQUIRED_KEYS = {"name", "description", "content"}
PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture(autouse=True)
def _load_id_translations(mocker):
    """Pastikan i18n _translations berisi id.json supaya helper backward-compat
    mengembalikan string Indonesia yang nyata (bukan raw key)."""
    id_path = PROJECT_ROOT / "i18n" / "id.json"
    translations = json.loads(id_path.read_text(encoding="utf-8"))
    mocker.patch("modules_client.i18n._translations", translations)
    mocker.patch("modules_client.i18n._reference_translations", translations)


def test_template_keys_not_empty():
    """TEMPLATE_KEYS tidak boleh kosong."""
    assert len(TEMPLATE_KEYS) > 0


def test_all_templates_have_required_keys():
    """Setiap template harus punya name, description, content (content > 20 chars)."""
    templates = get_templates()
    for key, data in templates.items():
        missing = REQUIRED_KEYS - data.keys()
        assert not missing, f"Template '{key}' kekurangan keys: {missing}"
        assert len(data["content"]) > 20, (
            f"Template '{key}' content terlalu pendek: {len(data['content'])} chars"
        )


def test_get_template_list_returns_tuples():
    """get_template_list() harus return list (str, str, str) dengan panjang sama dengan TEMPLATE_KEYS."""
    result = get_template_list()
    assert len(result) == len(TEMPLATE_KEYS)
    for item in result:
        assert isinstance(item, tuple), f"Item bukan tuple: {item!r}"
        assert len(item) == 3, f"Tuple tidak punya 3 elemen: {item!r}"
        key, name, description = item
        assert isinstance(key, str), f"key bukan str: {key!r}"
        assert isinstance(name, str), f"name bukan str: {name!r}"
        assert isinstance(description, str), f"description bukan str: {description!r}"


def test_get_template_valid_key():
    """get_template('general_seller') harus return string non-empty berisi 'live streaming'."""
    content = get_template("general_seller")
    assert isinstance(content, str)
    assert len(content) > 0
    assert "live streaming" in content


def test_get_template_invalid_key():
    """get_template dengan key tidak valid harus return string kosong."""
    assert get_template("nonexistent_template") == ""
    assert get_template("") == ""
