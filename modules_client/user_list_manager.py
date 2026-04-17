# modules_client/user_list_manager.py
"""
User List Manager - Mengelola blacklist dan whitelist username
untuk kontrol akses di VocaLive Seller
"""

import json
import logging
from pathlib import Path
from typing import List, Set

logger = logging.getLogger("VocaLive.UserList")

# Config path
CONFIG_DIR = Path(__file__).parent.parent / "config"
USER_LISTS_FILE = CONFIG_DIR / "user_lists.json"


class UserListManager:
    """Singleton manager untuk blacklist dan whitelist users"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.blacklist: Set[str] = set()
        self.whitelist: Set[str] = set()
        self._load_lists()
        logger.info(f"UserListManager initialized: {len(self.blacklist)} blacklisted, {len(self.whitelist)} whitelisted")

    def _load_lists(self):
        """Load lists from JSON file"""
        try:
            if USER_LISTS_FILE.exists():
                with open(USER_LISTS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.blacklist = set(u.lower().strip() for u in data.get("blacklist", []))
                    self.whitelist = set(u.lower().strip() for u in data.get("whitelist", []))
                    logger.info(f"Loaded user lists: {len(self.blacklist)} blacklisted, {len(self.whitelist)} whitelisted")
            else:
                self._save_lists()  # Create default file
        except Exception as e:
            logger.error(f"Error loading user lists: {e}")
            self.blacklist = set()
            self.whitelist = set()

    def _save_lists(self):
        """Save lists to JSON file"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "blacklist": sorted(list(self.blacklist)),
                "whitelist": sorted(list(self.whitelist))
            }
            with open(USER_LISTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("User lists saved")
            return True
        except Exception as e:
            logger.error(f"Error saving user lists: {e}")
            return False

    # ===== BLACKLIST METHODS =====
    def add_to_blacklist(self, username: str) -> bool:
        """Add user to blacklist"""
        username = username.lower().strip()
        if not username:
            return False

        # Remove from whitelist if exists
        self.whitelist.discard(username)

        self.blacklist.add(username)
        self._save_lists()
        logger.info(f"Added to blacklist: {username}")
        try:
            from modules_client.telemetry import capture as _tel_capture
            _tel_capture("user_list_updated", {"action": "blacklist_add"})
        except Exception:
            pass
        return True

    def remove_from_blacklist(self, username: str) -> bool:
        """Remove user from blacklist"""
        username = username.lower().strip()
        if username in self.blacklist:
            self.blacklist.discard(username)
            self._save_lists()
            logger.info(f"Removed from blacklist: {username}")
            try:
                from modules_client.telemetry import capture as _tel_capture
                _tel_capture("user_list_updated", {"action": "blacklist_remove"})
            except Exception:
                pass
            return True
        return False

    def is_blacklisted(self, username: str) -> bool:
        """Check if user is blacklisted"""
        return username.lower().strip() in self.blacklist

    def get_blacklist(self) -> List[str]:
        """Get all blacklisted users"""
        return sorted(list(self.blacklist))

    # ===== WHITELIST METHODS =====
    def add_to_whitelist(self, username: str) -> bool:
        """Add user to whitelist (VIP)"""
        username = username.lower().strip()
        if not username:
            return False

        # Remove from blacklist if exists
        self.blacklist.discard(username)

        self.whitelist.add(username)
        self._save_lists()
        logger.info(f"Added to whitelist (VIP): {username}")
        try:
            from modules_client.telemetry import capture as _tel_capture
            _tel_capture("user_list_updated", {"action": "whitelist_add"})
        except Exception:
            pass
        return True

    def remove_from_whitelist(self, username: str) -> bool:
        """Remove user from whitelist"""
        username = username.lower().strip()
        if username in self.whitelist:
            self.whitelist.discard(username)
            self._save_lists()
            logger.info(f"Removed from whitelist: {username}")
            try:
                from modules_client.telemetry import capture as _tel_capture
                _tel_capture("user_list_updated", {"action": "whitelist_remove"})
            except Exception:
                pass
            return True
        return False

    def is_whitelisted(self, username: str) -> bool:
        """Check if user is whitelisted (VIP)"""
        return username.lower().strip() in self.whitelist

    def get_whitelist(self) -> List[str]:
        """Get all whitelisted users"""
        return sorted(list(self.whitelist))

    # ===== BULK OPERATIONS =====
    def set_blacklist(self, usernames: List[str]):
        """Replace entire blacklist"""
        self.blacklist = set(u.lower().strip() for u in usernames if u.strip())
        # Remove any overlap with whitelist
        self.blacklist -= self.whitelist
        self._save_lists()

    def set_whitelist(self, usernames: List[str]):
        """Replace entire whitelist"""
        self.whitelist = set(u.lower().strip() for u in usernames if u.strip())
        # Remove any overlap with blacklist
        self.whitelist -= self.blacklist
        self._save_lists()

    def clear_blacklist(self):
        """Clear all blacklisted users"""
        self.blacklist.clear()
        self._save_lists()
        logger.info("Blacklist cleared")

    def clear_whitelist(self):
        """Clear all whitelisted users"""
        self.whitelist.clear()
        self._save_lists()
        logger.info("Whitelist cleared")

    def get_stats(self) -> dict:
        """Get statistics"""
        return {
            "blacklist_count": len(self.blacklist),
            "whitelist_count": len(self.whitelist)
        }


# Singleton accessor
def get_user_list_manager() -> UserListManager:
    """Get the singleton UserListManager instance"""
    return UserListManager()
