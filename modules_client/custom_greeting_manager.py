# modules_client/custom_greeting_manager.py - Custom Greeting System Manager

import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from queue import Empty, PriorityQueue

from modules_client.config_manager import ConfigManager
from modules_client.greeting_tts_cache import get_greeting_cache


class CustomGreetingManager:
    """Manage custom greeting system with 10 slots, priority queue, and idle detection"""

    # Priority levels
    PRIORITY_TRIGGER = 1      # Trigger replies (highest priority)
    PRIORITY_MANUAL = 5       # Manual commands
    PRIORITY_GREETING = 9     # Auto greetings (lowest priority)

    def __init__(self):
        self.cfg = ConfigManager()
        self.cache = get_greeting_cache()

        # Queue system
        self.priority_queue = PriorityQueue()
        self.is_active = False
        self.is_paused = False

        # Threading
        self.worker_thread = None
        self.greeting_thread = None
        self.should_stop = False

        # Idle detection
        self.last_trigger_time = None
        self.idle_timeout = 300  # 5 minutes

        # Greeting state
        self.current_slot = 1
        self.greeting_timers = {}

        # Load settings
        self.load_greeting_settings()

    def load_greeting_settings(self):
        """Load greeting slots and timers from config"""
        self.greeting_slots = {}

        for i in range(1, 11):  # Slots 1-10
            text = self.cfg.get(f"custom_greeting_slot_{i}", "").strip()
            timer = self.cfg.get(f"custom_greeting_timer_{i}", 120)  # Default 2 minutes

            if text:  # Only load non-empty slots
                self.greeting_slots[i] = {
                    "text": text,
                    "timer": timer,
                    "last_played": None
                }

        print(f"[GREETING] Loaded {len(self.greeting_slots)} greeting slots")

    def start(self):
        """Start the greeting system"""
        if self.is_active:
            print("[GREETING] System already active")
            return

        # Check if enabled
        if not self.cfg.get("custom_greeting_enabled", False):
            print("[GREETING] Custom greeting system is disabled")
            return

        if not self.greeting_slots:
            print("[GREETING] No greeting slots configured")
            return

        print("[GREETING] Starting custom greeting system...")

        self.is_active = True
        self.is_paused = False
        self.should_stop = False

        # Start worker thread for priority queue
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

        # Start greeting scheduler thread
        self.greeting_thread = threading.Thread(target=self._greeting_loop, daemon=True)
        self.greeting_thread.start()

        print("[GREETING] Custom greeting system started")

    def stop(self):
        """Stop the greeting system"""
        if not self.is_active:
            return

        print("[GREETING] Stopping custom greeting system...")

        self.should_stop = True
        self.is_active = False

        # Signal threads to stop
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2)

        if self.greeting_thread and self.greeting_thread.is_alive():
            self.greeting_thread.join(timeout=2)

        print("[GREETING] Custom greeting system stopped")

    def add_trigger(self, author, message, reply_text):
        """Add trigger reply to priority queue (highest priority)"""
        self.last_trigger_time = datetime.now()

        task = {
            "type": "trigger",
            "author": author,
            "message": message,
            "reply_text": reply_text,
            "timestamp": datetime.now()
        }

        self.priority_queue.put((self.PRIORITY_TRIGGER, time.time(), task))
        print(f"[GREETING] Added trigger to queue: {author}")

        # Resume if paused due to idle
        if self.is_paused:
            self.is_paused = False
            print("[GREETING] Resumed from idle due to trigger activity")

    def add_greeting(self, slot_number):
        """Add greeting to priority queue (lowest priority)"""
        if slot_number not in self.greeting_slots:
            return

        slot_data = self.greeting_slots[slot_number]

        task = {
            "type": "greeting",
            "slot_number": slot_number,
            "text": slot_data["text"],
            "timer": slot_data["timer"],
            "timestamp": datetime.now()
        }

        self.priority_queue.put((self.PRIORITY_GREETING, time.time(), task))
        print(f"[GREETING] Queued greeting slot {slot_number}")

    def _worker_loop(self):
        """Main worker loop to process priority queue"""
        print("[GREETING] Worker loop started")

        while self.is_active and not self.should_stop:
            try:
                # Get task from queue (with timeout to allow checking stop condition)
                priority, timestamp, task = self.priority_queue.get(timeout=1.0)

                if task["type"] == "trigger":
                    self._process_trigger_task(task)
                elif task["type"] == "greeting":
                    self._process_greeting_task(task)

                self.priority_queue.task_done()

            except Empty:
                # No tasks in queue, continue
                continue
            except Exception as e:
                print(f"[GREETING] Error in worker loop: {e}")
                time.sleep(0.5)

        print("[GREETING] Worker loop stopped")

    def _process_trigger_task(self, task):
        """Process trigger reply task"""
        try:
            # For trigger tasks, we don't need to play TTS here
            # The cohost tab will handle the TTS playback
            # We just need to update our idle detection
            self.last_trigger_time = datetime.now()

            print(f"[GREETING] Processed trigger from {task['author']}")

        except Exception as e:
            print(f"[GREETING] Error processing trigger task: {e}")

    def _process_greeting_task(self, task):
        """Process greeting task"""
        try:
            slot_number = task["slot_number"]
            text = task["text"]

            # Check if system is paused or should be paused
            if self._should_pause_for_idle():
                print(f"[GREETING] Skipping greeting slot {slot_number} - system paused")
                return

            print(f"[GREETING] Playing greeting slot {slot_number}: {text[:50]}...")

            # Get voice settings
            voice_setting = self.cfg.get("tts_voice", "id-ID-Standard-B (MALE)")
            language_code = "id-ID"  # Default Indonesian

            # Play from cache
            success = self.cache.play_cached_tts(text, voice_setting, language_code)

            if success:
                # Update last played time
                self.greeting_slots[slot_number]["last_played"] = datetime.now()
                print(f"[GREETING] Successfully played greeting slot {slot_number}")
            else:
                print(f"[GREETING] Failed to play greeting slot {slot_number}")

        except Exception as e:
            print(f"[GREETING] Error processing greeting task: {e}")

    def _greeting_loop(self):
        """Main greeting scheduler loop"""
        print("[GREETING] Greeting scheduler started")

        while self.is_active and not self.should_stop:
            try:
                # Check if system should be paused
                if self._should_pause_for_idle():
                    if not self.is_paused:
                        self.is_paused = True
                        print("[GREETING] Paused greeting system due to recent trigger activity")

                    time.sleep(10)  # Check every 10 seconds when paused
                    continue

                # Resume if was paused
                if self.is_paused:
                    self.is_paused = False
                    print("[GREETING] Resumed greeting system after idle period")

                # Find next slot to play
                next_slot = self._get_next_greeting_slot()
                if next_slot:
                    self.add_greeting(next_slot)

                # Sleep for a short interval before checking again
                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                print(f"[GREETING] Error in greeting loop: {e}")
                time.sleep(5)

        print("[GREETING] Greeting scheduler stopped")

    def _should_pause_for_idle(self):
        """Check if system should be paused due to recent trigger activity"""
        if self.last_trigger_time is None:
            return False

        idle_duration = (datetime.now() - self.last_trigger_time).total_seconds()
        return idle_duration < self.idle_timeout

    def _get_next_greeting_slot(self):
        """Get the next greeting slot that should be played"""
        current_time = datetime.now()

        for slot_number, slot_data in self.greeting_slots.items():
            last_played = slot_data.get("last_played")
            timer_seconds = slot_data["timer"]

            # If never played, or timer has elapsed
            if last_played is None:
                return slot_number

            elapsed = (current_time - last_played).total_seconds()
            if elapsed >= timer_seconds:
                return slot_number

        return None

    def reload_settings(self):
        """Reload greeting settings from config"""
        print("[GREETING] Reloading settings...")
        self.load_greeting_settings()

        # Clean up old cache if needed
        self.cache.cleanup_old_cache()

    def get_status(self):
        """Get current system status"""
        cache_stats = self.cache.get_cache_stats()

        return {
            "active": self.is_active,
            "paused": self.is_paused,
            "total_slots": len(self.greeting_slots),
            "queue_size": self.priority_queue.qsize(),
            "last_trigger": self.last_trigger_time.isoformat() if self.last_trigger_time else None,
            "idle_timeout": self.idle_timeout,
            "cache_stats": cache_stats
        }

# Global greeting manager instance
_greeting_manager = None

def get_greeting_manager():
    """Get global greeting manager instance"""
    global _greeting_manager
    if _greeting_manager is None:
        _greeting_manager = CustomGreetingManager()
    return _greeting_manager
