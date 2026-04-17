"""
Tests untuk sales_templates.py — TEMPLATES dict dan helper functions.
"""

import pytest

from sales_templates import TEMPLATES, get_template, get_template_list

pytestmark = pytest.mark.unit

REQUIRED_KEYS = {"name", "description", "content"}


def test_templates_dict_not_empty():
    """TEMPLATES tidak boleh kosong."""
    assert len(TEMPLATES) > 0


def test_all_templates_have_required_keys():
    """Setiap template harus punya name, description, content (content > 20 chars)."""
    for key, data in TEMPLATES.items():
        missing = REQUIRED_KEYS - data.keys()
        assert not missing, f"Template '{key}' kekurangan keys: {missing}"
        assert len(data["content"]) > 20, (
            f"Template '{key}' content terlalu pendek: {len(data['content'])} chars"
        )


def test_get_template_list_returns_tuples():
    """get_template_list() harus return list (str, str, str) dengan panjang sama dengan TEMPLATES."""
    result = get_template_list()
    assert len(result) == len(TEMPLATES)
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
