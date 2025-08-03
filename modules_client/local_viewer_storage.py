# modules_client/local_viewer_storage.py
"""
Local Viewer Storage - Sistem penyimpanan lokal yang ringan untuk data komentar viewer
Menggantikan operasi Supabase yang berat untuk meningkatkan performa autoreply
"""

import json
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import queue
import time

class LocalViewerStorage:
    """
    Sistem penyimpanan lokal yang sangat ringan untuk data viewer comments.
    Menggunakan SQLite untuk performa tinggi dan async operations untuk non-blocking UI.
    """
    
    def __init__(self, db_path: str = "data/viewer_comments.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Thread-safe queue untuk async operations
        self._write_queue = queue.Queue()
        self._running = True
        
        # Initialize database
        self._init_database()
        
        # Start background writer thread
        self._writer_thread = threading.Thread(target=self._background_writer, daemon=True)
        self._writer_thread.start()
        
        # In-memory cache untuk fast access
        self._cache = {}
        self._cache_lock = threading.RLock()
        
        print(f"[LocalViewerStorage] Initialized with database: {self.db_path}")
    
    def _init_database(self):
        """Initialize SQLite database dengan schema yang optimal"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS viewer_comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        viewer_name TEXT NOT NULL,
                        message TEXT NOT NULL,
                        reply TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        sentiment TEXT DEFAULT 'neutral',
                        platform TEXT DEFAULT 'youtube',
                        session_id TEXT,
                        INDEX(viewer_name),
                        INDEX(timestamp),
                        INDEX(session_id)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS viewer_stats (
                        viewer_name TEXT PRIMARY KEY,
                        total_comments INTEGER DEFAULT 0,
                        last_seen DATETIME,
                        status TEXT DEFAULT 'new',
                        preferred_topics TEXT,
                        avg_sentiment REAL DEFAULT 0.5,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_comments_viewer_time ON viewer_comments(viewer_name, timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_stats_last_seen ON viewer_stats(last_seen)")
                
                conn.commit()
                print("[LocalViewerStorage] Database initialized successfully")
                
        except Exception as e:
            print(f"[LocalViewerStorage] Database init error: {e}")
    
    def _background_writer(self):
        """Background thread untuk async database writes"""
        while self._running:
            try:
                # Get write operation from queue (blocking with timeout)
                operation = self._write_queue.get(timeout=1.0)
                
                if operation is None:  # Shutdown signal
                    break
                
                # Execute the operation
                operation_type = operation.get('type')
                
                if operation_type == 'save_comment':
                    self._save_comment_sync(operation['data'])
                elif operation_type == 'update_stats':
                    self._update_viewer_stats_sync(operation['data'])
                
                self._write_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[LocalViewerStorage] Background writer error: {e}")
    
    def save_comment_async(self, viewer_name: str, message: str, reply: str = None, 
                          sentiment: str = 'neutral', platform: str = 'youtube'):
        """
        Simpan komentar secara asinkron (non-blocking)
        Ini adalah method utama yang dipanggil dari autoreply
        """
        try:
            # Generate session ID untuk tracking
            session_id = f"{int(time.time())}-{hash(viewer_name) % 10000}"
            
            comment_data = {
                'viewer_name': viewer_name,
                'message': message,
                'reply': reply,
                'sentiment': sentiment,
                'platform': platform,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to async queue (non-blocking)
            self._write_queue.put({
                'type': 'save_comment',
                'data': comment_data
            })
            
            # Update in-memory cache immediately for fast access
            with self._cache_lock:
                if viewer_name not in self._cache:
                    self._cache[viewer_name] = []
                
                self._cache[viewer_name].append(comment_data)
                
                # Keep only last 10 comments in cache per viewer
                if len(self._cache[viewer_name]) > 10:
                    self._cache[viewer_name] = self._cache[viewer_name][-10:]
            
            # Update viewer stats async
            self._write_queue.put({
                'type': 'update_stats',
                'data': {
                    'viewer_name': viewer_name,
                    'sentiment': sentiment
                }
            })
            
            return True
            
        except Exception as e:
            print(f"[LocalViewerStorage] Error saving comment async: {e}")
            return False
    
    def _save_comment_sync(self, comment_data: Dict):
        """Simpan komentar ke database (dipanggil dari background thread)"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT INTO viewer_comments 
                    (viewer_name, message, reply, sentiment, platform, session_id, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    comment_data['viewer_name'],
                    comment_data['message'],
                    comment_data.get('reply'),
                    comment_data.get('sentiment', 'neutral'),
                    comment_data.get('platform', 'youtube'),
                    comment_data.get('session_id'),
                    comment_data['timestamp']
                ))
                conn.commit()
                
        except Exception as e:
            print(f"[LocalViewerStorage] Error saving comment to DB: {e}")
    
    def _update_viewer_stats_sync(self, stats_data: Dict):
        """Update viewer statistics (dipanggil dari background thread)"""
        try:
            viewer_name = stats_data['viewer_name']
            sentiment = stats_data.get('sentiment', 'neutral')
            
            with sqlite3.connect(str(self.db_path)) as conn:
                # Get current stats
                cursor = conn.execute("""
                    SELECT total_comments, avg_sentiment FROM viewer_stats 
                    WHERE viewer_name = ?
                """, (viewer_name,))
                
                result = cursor.fetchone()
                
                if result:
                    # Update existing stats
                    total_comments, avg_sentiment = result
                    new_total = total_comments + 1
                    
                    # Simple sentiment scoring
                    sentiment_score = {
                        'positive': 1.0, 'excited': 1.0,
                        'neutral': 0.5, 'curious': 0.5,
                        'negative': 0.0
                    }.get(sentiment, 0.5)
                    
                    # Update average sentiment
                    new_avg_sentiment = ((avg_sentiment * total_comments) + sentiment_score) / new_total
                    
                    conn.execute("""
                        UPDATE viewer_stats 
                        SET total_comments = ?, avg_sentiment = ?, last_seen = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE viewer_name = ?
                    """, (new_total, new_avg_sentiment, viewer_name))
                    
                else:
                    # Insert new stats
                    sentiment_score = {
                        'positive': 1.0, 'excited': 1.0,
                        'neutral': 0.5, 'curious': 0.5,
                        'negative': 0.0
                    }.get(sentiment, 0.5)
                    
                    conn.execute("""
                        INSERT INTO viewer_stats 
                        (viewer_name, total_comments, avg_sentiment, last_seen, status)
                        VALUES (?, 1, ?, CURRENT_TIMESTAMP, 'new')
                    """, (viewer_name, sentiment_score))
                
                conn.commit()
                
        except Exception as e:
            print(f"[LocalViewerStorage] Error updating viewer stats: {e}")
    
    def get_viewer_recent_comments(self, viewer_name: str, limit: int = 5) -> List[Dict]:
        """Get recent comments dari viewer (fast cache access)"""
        try:
            # Try cache first (fastest)
            with self._cache_lock:
                if viewer_name in self._cache:
                    cached_comments = self._cache[viewer_name][-limit:]
                    if cached_comments:
                        return cached_comments
            
            # Fallback to database
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT viewer_name, message, reply, sentiment, timestamp
                    FROM viewer_comments 
                    WHERE viewer_name = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (viewer_name, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"[LocalViewerStorage] Error getting recent comments: {e}")
            return []
    
    def get_viewer_stats(self, viewer_name: str) -> Optional[Dict]:
        """Get viewer statistics"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM viewer_stats WHERE viewer_name = ?
                """, (viewer_name,))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            print(f"[LocalViewerStorage] Error getting viewer stats: {e}")
            return None
    
    def cleanup_old_data(self, days_old: int = 30):
        """Cleanup data lama untuk menjaga performa"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            with sqlite3.connect(str(self.db_path)) as conn:
                # Delete old comments
                cursor = conn.execute("""
                    DELETE FROM viewer_comments 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_comments = cursor.rowcount
                
                # Delete inactive viewer stats
                cursor = conn.execute("""
                    DELETE FROM viewer_stats 
                    WHERE last_seen < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_stats = cursor.rowcount
                
                conn.commit()
                
                print(f"[LocalViewerStorage] Cleanup: {deleted_comments} comments, {deleted_stats} viewer stats")
                
        except Exception as e:
            print(f"[LocalViewerStorage] Cleanup error: {e}")
    
    def get_total_stats(self) -> Dict:
        """Get total statistics untuk monitoring"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM viewer_comments")
                total_comments = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM viewer_stats")
                total_viewers = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM viewer_comments 
                    WHERE timestamp > datetime('now', '-1 day')
                """)
                today_comments = cursor.fetchone()[0]
                
                return {
                    'total_comments': total_comments,
                    'total_viewers': total_viewers,
                    'today_comments': today_comments,
                    'cache_size': len(self._cache),
                    'queue_size': self._write_queue.qsize()
                }
                
        except Exception as e:
            print(f"[LocalViewerStorage] Error getting total stats: {e}")
            return {}
    
    def shutdown(self):
        """Shutdown storage system dengan graceful cleanup"""
        try:
            print("[LocalViewerStorage] Shutting down...")
            
            # Stop background writer
            self._running = False
            self._write_queue.put(None)  # Shutdown signal
            
            # Wait for writer thread to finish
            if self._writer_thread.is_alive():
                self._writer_thread.join(timeout=5.0)
            
            # Clear cache
            with self._cache_lock:
                self._cache.clear()
            
            print("[LocalViewerStorage] Shutdown complete")
            
        except Exception as e:
            print(f"[LocalViewerStorage] Shutdown error: {e}")

# Global instance
_local_storage = None

def get_local_storage() -> LocalViewerStorage:
    """Get global local storage instance"""
    global _local_storage
    if _local_storage is None:
        _local_storage = LocalViewerStorage()
    return _local_storage

def shutdown_local_storage():
    """Shutdown global local storage"""
    global _local_storage
    if _local_storage:
        _local_storage.shutdown()
        _local_storage = None