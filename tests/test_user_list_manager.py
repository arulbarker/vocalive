"""Tests for modules_client/user_list_manager.py — UserListManager singleton."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

pytestmark = pytest.mark.integration


@pytest.fixture
def manager(tmp_path):
    """
    Isolated UserListManager fixture:
    1. Reset _instance to None
    2. Patch USER_LISTS_FILE and CONFIG_DIR to use tmp_path
    3. Pre-populate user_lists.json with known data
    4. Yield the manager, then reset _instance after
    """
    import modules_client.user_list_manager as ulm_module

    # Reset singleton before creating a fresh one
    ulm_module.UserListManager._instance = None

    # Build tmp paths
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    user_lists_file = config_dir / "user_lists.json"
    user_lists_file.write_text(
        json.dumps({"blacklist": ["spammer1"], "whitelist": ["vip_buyer"]}),
        encoding="utf-8",
    )

    with patch.object(ulm_module, "CONFIG_DIR", config_dir), \
         patch.object(ulm_module, "USER_LISTS_FILE", user_lists_file):
        mgr = ulm_module.UserListManager()
        yield mgr

    # Teardown: reset singleton so other tests start clean
    ulm_module.UserListManager._instance = None


# ---------------------------------------------------------------------------
# 1. is_blacklisted
# ---------------------------------------------------------------------------
def test_is_blacklisted(manager):
    assert manager.is_blacklisted("spammer1") is True
    assert manager.is_blacklisted("SPAMMER1") is True
    assert manager.is_blacklisted("normal_user") is False


# ---------------------------------------------------------------------------
# 2. is_whitelisted
# ---------------------------------------------------------------------------
def test_is_whitelisted(manager):
    assert manager.is_whitelisted("vip_buyer") is True
    assert manager.is_whitelisted("VIP_BUYER") is True


# ---------------------------------------------------------------------------
# 3. add_to_blacklist moves user from whitelist
# ---------------------------------------------------------------------------
def test_add_to_blacklist(manager):
    result = manager.add_to_blacklist("vip_buyer")
    assert result is True
    assert manager.is_blacklisted("vip_buyer") is True
    assert manager.is_whitelisted("vip_buyer") is False


# ---------------------------------------------------------------------------
# 4. add_to_whitelist moves user from blacklist
# ---------------------------------------------------------------------------
def test_add_to_whitelist(manager):
    result = manager.add_to_whitelist("spammer1")
    assert result is True
    assert manager.is_whitelisted("spammer1") is True
    assert manager.is_blacklisted("spammer1") is False


# ---------------------------------------------------------------------------
# 5. add empty / whitespace username returns False
# ---------------------------------------------------------------------------
def test_add_empty_username(manager):
    assert manager.add_to_blacklist("") is False
    assert manager.add_to_blacklist("  ") is False
    assert manager.add_to_whitelist("") is False
    assert manager.add_to_whitelist("  ") is False


# ---------------------------------------------------------------------------
# 6. remove_from_blacklist removes and returns True
# ---------------------------------------------------------------------------
def test_remove_from_blacklist(manager):
    result = manager.remove_from_blacklist("spammer1")
    assert result is True
    assert manager.is_blacklisted("spammer1") is False


# ---------------------------------------------------------------------------
# 7. remove_from_blacklist on non-existent user returns False
# ---------------------------------------------------------------------------
def test_remove_nonexistent(manager):
    result = manager.remove_from_blacklist("ghost_user")
    assert result is False


# ---------------------------------------------------------------------------
# 8. get_blacklist returns sorted list
# ---------------------------------------------------------------------------
def test_get_blacklist_sorted(manager):
    manager.add_to_blacklist("alpha_user")
    manager.add_to_blacklist("zebra_user")
    bl = manager.get_blacklist()
    assert bl == sorted(bl)
    assert "spammer1" in bl
    assert "alpha_user" in bl
    assert "zebra_user" in bl


# ---------------------------------------------------------------------------
# 9. clear_blacklist empties the blacklist
# ---------------------------------------------------------------------------
def test_clear_blacklist(manager):
    manager.clear_blacklist()
    assert manager.get_blacklist() == []
    assert manager.is_blacklisted("spammer1") is False


# ---------------------------------------------------------------------------
# 10. set_blacklist excludes usernames already in whitelist
# ---------------------------------------------------------------------------
def test_set_blacklist_removes_overlap(manager):
    # "vip_buyer" is in whitelist — it must be excluded from the new blacklist
    manager.set_blacklist(["new_spammer", "vip_buyer"])
    assert manager.is_blacklisted("new_spammer") is True
    assert manager.is_blacklisted("vip_buyer") is False
    assert manager.is_whitelisted("vip_buyer") is True


# ---------------------------------------------------------------------------
# 11. get_stats returns dict with correct counts
# ---------------------------------------------------------------------------
def test_get_stats(manager):
    stats = manager.get_stats()
    assert isinstance(stats, dict)
    assert "blacklist_count" in stats
    assert "whitelist_count" in stats
    assert stats["blacklist_count"] == len(manager.get_blacklist())
    assert stats["whitelist_count"] == len(manager.get_whitelist())
    # Baseline fixture: 1 blacklisted, 1 whitelisted
    assert stats["blacklist_count"] == 1
    assert stats["whitelist_count"] == 1
