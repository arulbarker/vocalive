# modules_client/sequential_greeting_manager.py - Time-Based Sequential Greeting System

import time
import threading
import random
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from modules_client.config_manager import ConfigManager
from modules_server.tts_engine import speak
from modules_client.greeting_tts_cache import get_greeting_cache

class GreetingState(Enum):
    """Greeting system states"""
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"
    WAITING_RESUME = "waiting_resume"

class SequentialGreetingManager:
    """
    Time-based sequential greeting system
    - Plays greetings in order: Slot 1 → 2 → 3 → ... → 10 → back to 1
    - Skips empty slots automatically
    - Pauses when trigger replies are active
    - Resumes after trigger completion
    """
    
    def __init__(self):
        self.cfg = ConfigManager()
        
        # State management
        self.state = GreetingState.IDLE
        self.is_enabled = False
        
        # Slot sequencing
        self.current_slot = 1
        self.max_slot = 10
        self.play_mode = "sequential"  # "sequential" or "random"
        
        # Threading
        self.timer_thread = None
        self.should_stop = False
        self.thread_lock = threading.Lock()
        
        # Timing configuration
        self.greeting_interval = 180  # 3 minutes default
        self.resume_delay = 3  # 3 seconds after trigger
        
        # Trigger coordination
        self.trigger_active = False
        self.pending_resume_timer = None
        
        print("[SEQUENTIAL_GREETING] Manager initialized")
    
    def load_settings(self):
        """Load greeting settings from config"""
        self.greeting_interval = self.cfg.get("sequential_greeting_interval", 180)  # 3 minutes
        # Check both keys for compatibility, default to FALSE (user must explicitly enable)
        self.is_enabled = self.cfg.get("sequential_greeting_enabled", self.cfg.get("custom_greeting_enabled", False))
        self.play_mode = self.cfg.get("greeting_play_mode", "sequential")  # sequential or random

        print(f"[SEQUENTIAL_GREETING] Settings loaded - Enabled: {self.is_enabled}, Interval: {self.greeting_interval}s, Mode: {self.play_mode}")
    
    def start(self):
        """Start the sequential greeting system"""
        with self.thread_lock:
            if self.state != GreetingState.IDLE:
                print("[SEQUENTIAL_GREETING] System already running")
                return
            
            self.load_settings()
            
            if not self.is_enabled:
                print("[SEQUENTIAL_GREETING] System disabled in settings")
                return
            
            # Check if we have any greeting slots
            if not self._has_greeting_slots():
                print("[SEQUENTIAL_GREETING] No greeting slots configured")
                return
            
            print("[SEQUENTIAL_GREETING] Starting sequential greeting system...")
            
            self.should_stop = False
            self.state = GreetingState.ACTIVE
            self.trigger_active = False
            
            # Start timer thread
            self._schedule_next_greeting()
            
            print("[SEQUENTIAL_GREETING] System started successfully")
    
    def stop(self):
        """Stop the sequential greeting system"""
        with self.thread_lock:
            if self.state == GreetingState.IDLE:
                return
            
            print("[SEQUENTIAL_GREETING] Stopping system...")
            
            self.should_stop = True
            self.state = GreetingState.IDLE
            
            # Cancel any pending timers
            if self.timer_thread and self.timer_thread.is_alive():
                # Can't cancel timer thread directly, it will check should_stop
                pass
            
            if self.pending_resume_timer:
                self.pending_resume_timer.cancel()
                self.pending_resume_timer = None
            
            print("[SEQUENTIAL_GREETING] System stopped")
    
    def on_trigger_start(self):
        """Called when a trigger reply starts"""
        with self.thread_lock:
            if self.state == GreetingState.ACTIVE:
                print("[SEQUENTIAL_GREETING] Pausing for trigger reply")
                self.state = GreetingState.PAUSED
                self.trigger_active = True
                
                # Cancel any pending resume timer
                if self.pending_resume_timer:
                    self.pending_resume_timer.cancel()
                    self.pending_resume_timer = None
    
    def on_trigger_complete(self):
        """Called when a trigger reply completes"""
        with self.thread_lock:
            if self.state == GreetingState.PAUSED:
                print(f"[SEQUENTIAL_GREETING] Trigger complete, resuming in {self.resume_delay}s")
                self.state = GreetingState.WAITING_RESUME
                self.trigger_active = False
                
                # Schedule resume after delay
                self.pending_resume_timer = threading.Timer(
                    self.resume_delay, 
                    self._resume_greeting
                )
                self.pending_resume_timer.start()
    
    def _resume_greeting(self):
        """Resume greeting system after trigger delay"""
        with self.thread_lock:
            if self.state == GreetingState.WAITING_RESUME and not self.should_stop:
                print("[SEQUENTIAL_GREETING] Resuming greeting system")
                self.state = GreetingState.ACTIVE
                self._schedule_next_greeting()
    
    def _schedule_next_greeting(self):
        """Schedule the next greeting"""
        if self.should_stop:
            return
        
        def timer_callback():
            if not self.should_stop and self.state == GreetingState.ACTIVE:
                self._play_next_greeting()
        
        self.timer_thread = threading.Timer(self.greeting_interval, timer_callback)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        print(f"[SEQUENTIAL_GREETING] Next greeting scheduled in {self.greeting_interval}s")
    
    def _play_next_greeting(self):
        """Play the next greeting in sequence or random"""
        with self.thread_lock:
            if self.state != GreetingState.ACTIVE or self.should_stop:
                return

            # Find next slot based on play mode
            if self.play_mode == "random":
                next_slot = self._find_random_slot()
            else:
                next_slot = self._find_next_slot()

            if next_slot is None:
                print("[SEQUENTIAL_GREETING] No valid greeting slots found")
                self._schedule_next_greeting()
                return

            # Get slot text
            slot_text = self.cfg.get(f"custom_greeting_slot_{next_slot}", "").strip()

            if not slot_text:
                print(f"[SEQUENTIAL_GREETING] Slot {next_slot} is empty, trying again")
                if self.play_mode == "sequential":
                    self._advance_slot()
                self._schedule_next_greeting()
                return

            print(f"[SEQUENTIAL_GREETING] Playing slot {next_slot} ({self.play_mode} mode): {slot_text[:50]}...")

            # Play greeting with TTS
            self._play_greeting_tts(slot_text)

            # Advance to next slot only in sequential mode
            if self.play_mode == "sequential":
                self._advance_slot()

            # Schedule next greeting
            if self.state == GreetingState.ACTIVE:
                self._schedule_next_greeting()
    
    def _find_next_slot(self):
        """Find next non-empty slot starting from current position"""
        start_slot = self.current_slot
        
        for i in range(self.max_slot):
            slot_text = self.cfg.get(f"custom_greeting_slot_{self.current_slot}", "").strip()
            
            if slot_text:  # Found non-empty slot
                return self.current_slot
            
            # Move to next slot
            self.current_slot = (self.current_slot % self.max_slot) + 1
            
            # Prevent infinite loop if all slots are empty
            if self.current_slot == start_slot:
                break
        
        return None  # All slots are empty
    
    def _find_random_slot(self):
        """Find a random non-empty slot"""
        # Get list of all non-empty slots
        available_slots = []
        for i in range(1, self.max_slot + 1):
            slot_text = self.cfg.get(f"custom_greeting_slot_{i}", "").strip()
            if slot_text:
                available_slots.append(i)

        if not available_slots:
            return None

        # Return random slot from available slots
        return random.choice(available_slots)

    def _advance_slot(self):
        """Advance to next slot with wrap-around"""
        self.current_slot = (self.current_slot % self.max_slot) + 1
        print(f"[SEQUENTIAL_GREETING] Advanced to slot {self.current_slot}")
    
    def _play_greeting_tts(self, text):
        """Play greeting text using TTS with caching for API cost savings"""
        try:
            # Get voice settings - PENTING: Gunakan exact voice yang dipilih user
            voice_setting = self.cfg.get("tts_voice", "id-ID-Standard-A (FEMALE)")

            # Extract voice name from setting (remove gender label in parentheses)
            # Example: "Gemini-Sadachbia (MALE)" -> "Gemini-Sadachbia"
            if "(" in voice_setting:
                voice_name = voice_setting.split("(")[0].strip()
            else:
                voice_name = voice_setting

            # Determine language code based on voice
            # Gemini voices are multilingual, default to Indonesian
            if voice_name.startswith("Gemini-"):
                language_code = "id-ID"  # Gemini supports multilingual
            elif voice_name.startswith("id-"):
                language_code = "id-ID"
            elif voice_name.startswith("ms-"):
                language_code = "ms-MY"
            elif voice_name.startswith("en-"):
                # Extract exact language code (e.g., "en-US", "en-GB")
                parts = voice_name.split("-")
                if len(parts) >= 2:
                    language_code = f"{parts[0]}-{parts[1]}"
                else:
                    language_code = "en-US"
            else:
                language_code = "id-ID"  # Default fallback

            # Debug logging untuk memastikan voice konsisten
            print(f"[SEQUENTIAL_GREETING] ═══════════════════════════════")
            print(f"[SEQUENTIAL_GREETING] Playing TTS: {text[:50]}...")
            print(f"[SEQUENTIAL_GREETING] Voice Setting (raw): {voice_setting}")
            print(f"[SEQUENTIAL_GREETING] Voice Name (extracted): {voice_name}")
            print(f"[SEQUENTIAL_GREETING] Language Code: {language_code}")
            print(f"[SEQUENTIAL_GREETING] ═══════════════════════════════")

            # Get cache instance
            cache = get_greeting_cache()

            # Use cache-aware playback - will use cache if available, otherwise generate and cache
            # PENTING: voice_name harus EXACT sama setiap kali untuk cache hit
            success = cache.play_from_cache_or_generate(
                text=text,
                voice_name=voice_name,  # Must be exact and consistent!
                language_code=language_code
            )

            if success:
                print("[SEQUENTIAL_GREETING] ✅ TTS playback completed successfully")
            else:
                print("[SEQUENTIAL_GREETING] ❌ TTS playback failed")

        except Exception as e:
            print(f"[SEQUENTIAL_GREETING] ❌ Error playing TTS: {e}")
            import traceback
            traceback.print_exc()
    
    def _has_greeting_slots(self):
        """Check if any greeting slots are configured"""
        for i in range(1, self.max_slot + 1):
            slot_text = self.cfg.get(f"custom_greeting_slot_{i}", "").strip()
            if slot_text:
                return True
        return False
    
    def get_status(self):
        """Get current system status"""
        return {
            "state": self.state.value,
            "enabled": self.is_enabled,
            "current_slot": self.current_slot,
            "trigger_active": self.trigger_active,
            "interval_seconds": self.greeting_interval,
            "total_slots": self._count_configured_slots(),
            "play_mode": self.play_mode
        }
    
    def _count_configured_slots(self):
        """Count configured greeting slots"""
        count = 0
        for i in range(1, self.max_slot + 1):
            slot_text = self.cfg.get(f"custom_greeting_slot_{i}", "").strip()
            if slot_text:
                count += 1
        return count
    
    def set_greeting_interval(self, seconds):
        """Set greeting interval"""
        self.greeting_interval = max(1, seconds)  # Minimum 1 second
        self.cfg.set("sequential_greeting_interval", self.greeting_interval)
        print(f"[SEQUENTIAL_GREETING] Interval set to {self.greeting_interval}s")
    
    def force_next_greeting(self):
        """Force play next greeting immediately (for testing)"""
        with self.thread_lock:
            if self.state == GreetingState.ACTIVE:
                print("[SEQUENTIAL_GREETING] Force playing next greeting")
                self._play_next_greeting()
    
    def set_play_mode(self, mode):
        """Set play mode (sequential or random)"""
        if mode in ["sequential", "random"]:
            self.play_mode = mode
            self.cfg.set("greeting_play_mode", mode)
            print(f"[SEQUENTIAL_GREETING] Play mode set to: {mode}")
        else:
            print(f"[SEQUENTIAL_GREETING] Invalid play mode: {mode}")

    def reset_sequence(self):
        """Reset sequence to slot 1"""
        with self.thread_lock:
            self.current_slot = 1
            print("[SEQUENTIAL_GREETING] Sequence reset to slot 1")

# Global sequential greeting manager instance
_sequential_greeting_manager = None

def get_sequential_greeting_manager():
    """Get global sequential greeting manager instance"""
    global _sequential_greeting_manager
    if _sequential_greeting_manager is None:
        _sequential_greeting_manager = SequentialGreetingManager()
    return _sequential_greeting_manager