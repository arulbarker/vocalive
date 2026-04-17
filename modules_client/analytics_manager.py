# modules_client/analytics_manager.py
"""
Analytics Manager untuk tracking live streaming performance
Support: YouTube (pytchat) dan TikTok (TikTokLive)
"""

import json
import logging
import os
import re
import sys
import threading
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("VocaLive.Analytics")


def _get_app_root() -> Path:
    """Root folder app: direktori EXE (frozen) atau root project (dev)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


class LiveAnalyticsManager:
    """
    Manager untuk tracking analytics live streaming dengan optimasi real-time

    Features:
    - Real-time tracking dengan minimal overhead
    - Support multi-platform (YouTube & TikTok)
    - Unlimited data retention dengan option hapus semua
    - Export ke CSV/Excel
    """

    def __init__(self, data_dir=None):
        """Initialize analytics manager"""
        if data_dir is None:
            data_dir = _get_app_root() / "config" / "analytics"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Thread lock untuk thread-safe operations
        self._lock = threading.Lock()

        # Current session data (in-memory untuk real-time performance)
        self.current_session = {
            "session_id": None,
            "platform": None,
            "start_time": None,
            "end_time": None,
            "is_active": False,

            # Viewer tracking
            "viewers": defaultdict(lambda: {
                "username": "",
                "total_comments": 0,
                "replied_count": 0,
                "gifts_sent": 0,
                "gifts_value": 0,
                "shares": 0,
                "likes": 0,
                "first_seen": None,
                "last_seen": None,
                "mentioned_keywords": []
            }),

            # Aggregate stats
            "stats": {
                "total_comments": 0,
                "total_comments_replied": 0,
                "unique_viewers": 0,
                "peak_viewers": 0,
                "total_gifts_value": 0,
                "total_shares": 0,
                "total_likes": 0,
                "total_follows": 0,
                "keyword_mentions": Counter()
            },

            # Timeline events
            "timeline": []
        }

        # Persistent sessions (untuk history)
        self.sessions_file = self.data_dir / "sessions.json"
        self.sessions = self._load_sessions()

    def _load_sessions(self):
        """Load saved sessions from file"""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[Analytics] Error loading sessions: {e}")
                return []
        return []

    def _save_sessions(self):
        """Save sessions to file (called periodically)"""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[Analytics] Error saving sessions: {e}")

    def start_session(self, platform="youtube"):
        """Start new analytics session"""
        with self._lock:
            session_id = f"{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            self.current_session = {
                "session_id": session_id,
                "platform": platform,
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "is_active": True,
                "viewers": defaultdict(lambda: {
                    "username": "",
                    "total_comments": 0,
                    "replied_count": 0,
                    "gifts_sent": 0,
                    "gifts_value": 0,
                    "shares": 0,
                    "likes": 0,
                    "first_seen": None,
                    "last_seen": None,
                    "mentioned_keywords": []
                }),
                "stats": {
                    "total_comments": 0,
                    "total_comments_replied": 0,
                    "unique_viewers": 0,
                    "peak_viewers": 0,
                    "total_gifts_value": 0,
                    "total_shares": 0,
                    "total_likes": 0,
                    "total_follows": 0,
                    "keyword_mentions": Counter()
                },
                "timeline": []
            }

            # Add timeline event
            self._add_timeline_event("session_start", f"Live started on {platform}")

            logger.info(f"[Analytics] Session started: {session_id}")
            return session_id

    def end_session(self):
        """End current session and save to history"""
        with self._lock:
            if not self.current_session["is_active"]:
                return False

            self.current_session["is_active"] = False
            self.current_session["end_time"] = datetime.now().isoformat()

            # Add timeline event
            self._add_timeline_event("session_end", "Live ended")

            # Convert defaultdict to regular dict for JSON serialization
            session_data = self._prepare_session_for_save()

            # Add to sessions history
            self.sessions.append(session_data)

            # Save to file
            self._save_sessions()

            logger.info(f"[Analytics] Session ended: {self.current_session['session_id']}")
            return True

    def _prepare_session_for_save(self):
        """Prepare session data for JSON serialization"""
        # Convert defaultdict and Counter to regular dict/list
        viewers_dict = {}
        for username, data in self.current_session["viewers"].items():
            viewers_dict[username] = dict(data)

        stats = dict(self.current_session["stats"])
        stats["keyword_mentions"] = dict(stats["keyword_mentions"])

        return {
            "session_id": self.current_session["session_id"],
            "platform": self.current_session["platform"],
            "start_time": self.current_session["start_time"],
            "end_time": self.current_session["end_time"],
            "viewers": viewers_dict,
            "stats": stats,
            "timeline": self.current_session["timeline"]
        }

    def _add_timeline_event(self, event_type, description):
        """Add event to timeline"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "description": description
        }
        self.current_session["timeline"].append(event)

    def track_comment(self, username, message, replied=False):
        """
        Track comment dari viewer

        Args:
            username: Nama viewer
            message: Isi pesan
            replied: Apakah comment ini dibalas oleh AI
        """
        with self._lock:
            if not self.current_session["is_active"]:
                return

            current_time = datetime.now().isoformat()

            # Update viewer data
            viewer = self.current_session["viewers"][username]
            viewer["username"] = username
            viewer["total_comments"] += 1
            viewer["last_seen"] = current_time

            if viewer["first_seen"] is None:
                viewer["first_seen"] = current_time

            if replied:
                viewer["replied_count"] += 1

            # Extract keywords from message (simple keyword extraction)
            keywords = self._extract_keywords(message)
            viewer["mentioned_keywords"].extend(keywords)

            # Update aggregate stats
            self.current_session["stats"]["total_comments"] += 1
            if replied:
                self.current_session["stats"]["total_comments_replied"] += 1

            # Update keyword counter
            for keyword in keywords:
                self.current_session["stats"]["keyword_mentions"][keyword] += 1

            # Update unique viewers
            self.current_session["stats"]["unique_viewers"] = len(self.current_session["viewers"])

    def mark_replied(self, username):
        """Tandai komentar terakhir dari viewer sebagai sudah dibalas — tanpa menambah total_comments lagi"""
        with self._lock:
            if not self.current_session["is_active"]:
                return
            viewer = self.current_session["viewers"].get(username)
            if viewer:
                viewer["replied_count"] += 1
            self.current_session["stats"]["total_comments_replied"] += 1

    def track_gift(self, username, gift_name, gift_value=0):
        """Track gift/donation dari viewer (TikTok/YouTube SuperChat)"""
        with self._lock:
            if not self.current_session["is_active"]:
                return

            viewer = self.current_session["viewers"][username]
            viewer["username"] = username
            viewer["gifts_sent"] += 1
            viewer["gifts_value"] += gift_value
            viewer["last_seen"] = datetime.now().isoformat()

            # Update aggregate stats
            self.current_session["stats"]["total_gifts_value"] += gift_value

            # Add timeline event for significant gifts
            if gift_value > 0:
                self._add_timeline_event("gift", f"{username} sent {gift_name} (Rp {gift_value:,})")

    def track_share(self, username):
        """Track share event (TikTok)"""
        with self._lock:
            if not self.current_session["is_active"]:
                return

            viewer = self.current_session["viewers"][username]
            viewer["username"] = username
            viewer["shares"] += 1
            viewer["last_seen"] = datetime.now().isoformat()

            self.current_session["stats"]["total_shares"] += 1
            self._add_timeline_event("share", f"{username} shared the live")

    def track_like(self, username, count=1):
        """Track like event (TikTok)"""
        with self._lock:
            if not self.current_session["is_active"]:
                return

            viewer = self.current_session["viewers"][username]
            viewer["username"] = username
            viewer["likes"] += count
            viewer["last_seen"] = datetime.now().isoformat()

            self.current_session["stats"]["total_likes"] += count

    def track_follow(self, username):
        """Track follow event (TikTok)"""
        with self._lock:
            if not self.current_session["is_active"]:
                return

            self.current_session["stats"]["total_follows"] += 1
            self._add_timeline_event("follow", f"{username} followed")

    def track_viewer_count(self, count):
        """Track viewer count dan update peak"""
        with self._lock:
            if not self.current_session["is_active"]:
                return

            if count > self.current_session["stats"]["peak_viewers"]:
                self.current_session["stats"]["peak_viewers"] = count
                self._add_timeline_event("peak_viewers", f"New peak: {count} viewers")

    def _extract_keywords(self, message):
        """
        Extract keywords dari message (improved implementation)

        Fokus pada:
        - Product names (kata benda)
        - Price mentions (angka + rb/ribu/k)
        - Common questions (harga, stock, warna, ukuran, dll)
        - Size mentions (size 1, 2, 3, etc.)
        - Any significant word from message
        """
        keywords = []
        message_lower = message.lower()

        # Common product-related keywords (expanded)
        product_keywords = [
            # Pakaian
            'hijab', 'gamis', 'dress', 'baju', 'celana', 'rok', 'tunik',
            'khimar', 'bergo', 'pashmina', 'jilbab', 'mukena', 'koko',
            'kaos', 'kemeja', 'jaket', 'hoodie', 'sweater', 'cardigan',
            'outer', 'blazer', 'vest', 'atasan', 'bawahan', 'setelan',
            # Aksesoris
            'tas', 'sepatu', 'sandal', 'jam', 'gelang', 'kalung', 'anting',
            # E-commerce
            'harga', 'stock', 'stok', 'warna', 'ukuran', 'size', 'diskon', 'promo',
            'beli', 'order', 'cod', 'ongkir', 'ready', 'po', 'preorder',
            'keranjang', 'checkout', 'bayar', 'transfer', 'rekening',
            # Pertanyaan umum
            'mau', 'kak', 'kakak', 'min', 'admin', 'gimana', 'caranya',
            'ada', 'masih', 'habis', 'sold', 'restock', 'kapan',
            # Ukuran
            'xl', 'xxl', 's', 'm', 'l', 'allsize', 'jumbo', 'big',
            'kecil', 'sedang', 'besar', 'fit', 'oversize',
            # Warna
            'hitam', 'putih', 'merah', 'biru', 'hijau', 'kuning', 'pink',
            'ungu', 'coklat', 'cream', 'maroon', 'navy', 'army', 'mocca',
            # Feedback
            'bagus', 'cantik', 'lucu', 'keren', 'mantap', 'recommended'
        ]

        for keyword in product_keywords:
            if keyword in message_lower:
                keywords.append(keyword)

        # Extract price mentions (e.g., "100rb", "50ribu", "25k")
        price_pattern = r'\d+\s*(?:rb|ribu|k|jt|juta)'
        if re.search(price_pattern, message_lower):
            keywords.append('_price_mention')

        # Extract size mentions (e.g., "size 3", "ukuran 40", "no 38")
        size_pattern = r'(?:size|ukuran|no|nomor)\s*(\d+)'
        size_matches = re.findall(size_pattern, message_lower)
        for size in size_matches:
            keywords.append(f'size_{size}')

        # Extract any standalone numbers that might be product codes
        number_pattern = r'\b(\d{1,3})\b'
        numbers = re.findall(number_pattern, message_lower)
        for num in numbers:
            if len(num) <= 2:  # Likely size reference
                keywords.append(f'size_{num}')

        # Extract significant words (>3 chars, not common stopwords)
        stopwords = {'yang', 'dan', 'atau', 'dengan', 'untuk', 'dari', 'ini', 'itu',
                     'ada', 'tidak', 'bisa', 'akan', 'sudah', 'juga', 'saya', 'kami',
                     'kamu', 'mereka', 'apa', 'siapa', 'mana', 'kapan', 'kenapa',
                     'bagaimana', 'kalau', 'jadi', 'dong', 'nih', 'sih', 'lho', 'ya'}

        words = re.findall(r'[a-z]{4,}', message_lower)
        for word in words:
            if word not in stopwords and word not in product_keywords:
                keywords.append(word)

        return keywords

    def get_top_viewers(self, limit=10, sort_by="total_comments"):
        """
        Get top viewers berdasarkan metric tertentu

        Args:
            limit: Jumlah top viewers
            sort_by: Metric untuk sorting (total_comments, replied_count, gifts_value)
        """
        with self._lock:
            viewers_list = []
            for username, data in self.current_session["viewers"].items():
                viewer_data = dict(data)
                viewer_data["username"] = username
                viewers_list.append(viewer_data)

            # Sort by specified metric
            viewers_list.sort(key=lambda x: x.get(sort_by, 0), reverse=True)

            return viewers_list[:limit]

    def get_top_keywords(self, limit=10):
        """Get top mentioned keywords"""
        with self._lock:
            return self.current_session["stats"]["keyword_mentions"].most_common(limit)

    def get_current_stats(self):
        """Get current session statistics (untuk real-time display)"""
        with self._lock:
            # Return copy to avoid threading issues
            stats = dict(self.current_session["stats"])
            stats["keyword_mentions"] = dict(stats["keyword_mentions"])
            stats["session_id"] = self.current_session["session_id"]
            stats["platform"] = self.current_session["platform"]
            stats["start_time"] = self.current_session["start_time"]
            stats["is_active"] = self.current_session["is_active"]

            return stats

    def get_session_duration(self):
        """Get current session duration in minutes"""
        if not self.current_session["start_time"]:
            return 0

        start = datetime.fromisoformat(self.current_session["start_time"])
        end = datetime.now() if self.current_session["is_active"] else datetime.fromisoformat(self.current_session["end_time"])

        duration = (end - start).total_seconds() / 60
        return round(duration, 1)

    def clear_all_data(self):
        """Hapus semua data analytics"""
        with self._lock:
            self.sessions = []
            self._save_sessions()
            logger.info("[Analytics] All data cleared")
            return True

    def export_to_csv(self, session_id=None, export_path=None):
        """
        Export data ke CSV

        Args:
            session_id: ID session yang akan di-export (None = current session)
            export_path: Path untuk save file (None = auto generate)
        """
        import csv

        # Get session data
        if session_id is None:
            session_data = self._prepare_session_for_save()
        else:
            session_data = next((s for s in self.sessions if s["session_id"] == session_id), None)
            if not session_data:
                return None, "Session not found"

        # Auto generate export path
        if export_path is None:
            export_dir = self.data_dir / "exports"
            export_dir.mkdir(exist_ok=True)
            export_path = export_dir / f"{session_data['session_id']}_analytics.csv"

        try:
            with open(export_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Header
                writer.writerow(["VocaLive - Live Analytics Report"])
                writer.writerow(["Session ID", session_data["session_id"]])
                writer.writerow(["Platform", session_data["platform"]])
                writer.writerow(["Start Time", session_data["start_time"]])
                writer.writerow(["End Time", session_data["end_time"] or "Active"])
                writer.writerow([])

                # Aggregate Stats
                writer.writerow(["=== AGGREGATE STATISTICS ==="])
                for key, value in session_data["stats"].items():
                    if key != "keyword_mentions":
                        writer.writerow([key.replace('_', ' ').title(), value])
                writer.writerow([])

                # Top Viewers
                writer.writerow(["=== TOP VIEWERS ==="])
                writer.writerow(["Username", "Comments", "Replied", "Gifts Sent", "Gifts Value", "Shares", "Likes"])

                viewers_list = [(username, data) for username, data in session_data["viewers"].items()]
                viewers_list.sort(key=lambda x: x[1]["total_comments"], reverse=True)

                for username, data in viewers_list[:50]:  # Top 50
                    writer.writerow([
                        username,
                        data["total_comments"],
                        data["replied_count"],
                        data["gifts_sent"],
                        data["gifts_value"],
                        data["shares"],
                        data["likes"]
                    ])

                writer.writerow([])

                # Top Keywords
                writer.writerow(["=== TOP KEYWORDS ==="])
                writer.writerow(["Keyword", "Mentions"])

                if "keyword_mentions" in session_data["stats"]:
                    keywords = sorted(session_data["stats"]["keyword_mentions"].items(), key=lambda x: x[1], reverse=True)
                    for keyword, count in keywords[:30]:  # Top 30
                        writer.writerow([keyword, count])

            return str(export_path), "Export successful"

        except Exception as e:
            return None, f"Export failed: {str(e)}"

    def get_all_sessions(self):
        """Get all saved sessions"""
        return self.sessions

    def get_session_summary(self, session_id):
        """Get summary of specific session"""
        session = next((s for s in self.sessions if s["session_id"] == session_id), None)
        if not session:
            return None

        # Calculate duration
        if session["end_time"]:
            start = datetime.fromisoformat(session["start_time"])
            end = datetime.fromisoformat(session["end_time"])
            duration_minutes = (end - start).total_seconds() / 60
        else:
            duration_minutes = 0

        return {
            "session_id": session["session_id"],
            "platform": session["platform"],
            "duration_minutes": round(duration_minutes, 1),
            "total_comments": session["stats"]["total_comments"],
            "unique_viewers": len(session["viewers"]),
            "peak_viewers": session["stats"]["peak_viewers"],
            "total_gifts": session["stats"]["total_gifts_value"]
        }


# Singleton instance
_analytics_manager = None

def get_analytics_manager():
    """Get singleton instance of analytics manager"""
    global _analytics_manager
    if _analytics_manager is None:
        _analytics_manager = LiveAnalyticsManager()
    return _analytics_manager
