# ========== IMPROVED LIGHTWEIGHT PYTCHAT LISTENER ==========
# 🚀 ENHANCED VERSION dengan stability fixes

import queue
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Handle pytchat import
try:
    import pytchat
    print("[DEBUG] PyTchat imported directly")
except ImportError:
    print("[DEBUG] Direct pytchat import failed, trying thirdparty...")

    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        thirdparty_path = bundle_dir / "thirdparty"
    else:
        # Running in development
        current_dir = Path(__file__).parent
        thirdparty_path = current_dir.parent / "thirdparty"

    if thirdparty_path.exists():
        sys.path.insert(0, str(thirdparty_path))
        try:
            import pytchat
            print(f"[DEBUG] PyTchat imported from thirdparty: {thirdparty_path}")
        except ImportError as e:
            print(f"[ERROR] Failed to import pytchat from thirdparty: {e}")
            pytchat = None
    else:
        print(f"[ERROR] Thirdparty path not found: {thirdparty_path}")
        pytchat = None

class ImprovedLightweightPytchatListener:
    """🚀 Improved lightweight pytchat listener dengan enhanced stability"""

    def __init__(self, video_id, callback, trigger_words=None, reply_mode="Trigger"):
        self.video_id = video_id
        self.callback = callback
        self.is_running = False
        self.chat = None

        # Debug: Log listener creation
        print(f"[LISTENER-INIT] Creating new listener with ID: {id(self)}")

        # ⚡ IMPROVED: Better queue management
        self.message_queue = queue.Queue(maxsize=500)
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pytchat")

        # ⚡ ENHANCED CONFIG
        self.reply_mode = reply_mode
        self.trigger_words = [word.lower().strip() for word in (trigger_words or ["halo", "bang", "min"])]
        self.delay_seconds = 5

        # ⚡ IMPROVED: Better message tracking
        self.seen_messages = set()
        self.last_message_time = 0
        self.connection_retries = 0
        self.max_retries = 3

        print(f"[IMPROVED] Initialized for video: {video_id}")
        print(f"[IMPROVED] Trigger words: {self.trigger_words}")
        print(f"[IMPROVED] Reply mode: {self.reply_mode}")

    def start(self):
        """🚀 Start improved listener with retry logic"""
        for attempt in range(self.max_retries):
            try:
                print(f"[IMPROVED] Starting listener attempt {attempt + 1}/{self.max_retries}")

                if not pytchat:
                    print("[IMPROVED] PyTchat not available")
                    return False

                # ⚡ ENHANCED: Create chat object with retry
                self.chat = pytchat.create(video_id=self.video_id)
                if not self.chat:
                    print(f"[IMPROVED] Failed to create chat object (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        time.sleep(2)
                        continue
                    return False

                # ⚡ ENHANCED: Verify chat is alive
                if not self.chat.is_alive():
                    print(f"[IMPROVED] Chat not alive (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        time.sleep(2)
                        continue
                    return False

                self.is_running = True

                # ⚡ IMPROVED: Start threads with better error handling
                self.executor.submit(self._enhanced_message_fetcher)
                self.executor.submit(self._enhanced_message_processor)

                print("[IMPROVED] Listener started successfully")
                return True

            except Exception as e:
                print(f"[IMPROVED] Error starting listener (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    return False

        return False

    def _enhanced_message_fetcher(self):
        """⚡ ENHANCED: More robust message fetcher"""
        print("[IMPROVED] Enhanced message fetcher started")

        consecutive_errors = 0
        max_consecutive_errors = 5

        try:
            while self.is_running and consecutive_errors < max_consecutive_errors:
                try:
                    # ⚡ ENHANCED: Check if chat is still alive
                    if not self.chat or not self.chat.is_alive():
                        print("[IMPROVED] Chat connection lost, attempting reconnect...")
                        if not self._reconnect_chat():
                            break

                    # ⚡ ENHANCED: Get messages with better error handling
                    items = self.chat.get().sync_items()

                    if items:
                        consecutive_errors = 0  # Reset error counter on success

                        for item in items:
                            if not self.is_running:
                                break

                            # ⚡ ENHANCED: Better message validation
                            if self._is_valid_message_enhanced(item):
                                try:
                                    self.message_queue.put_nowait({
                                        'author': item.author.name,
                                        'message': item.message,
                                        'timestamp': time.time()
                                    })
                                    print(f"[IMPROVED] Queued: {item.author.name}: {item.message}")
                                except queue.Full:
                                    # ⚡ ENHANCED: Better queue management
                                    try:
                                        # Remove oldest message
                                        self.message_queue.get_nowait()
                                        self.message_queue.put_nowait({
                                            'author': item.author.name,
                                            'message': item.message,
                                            'timestamp': time.time()
                                        })
                                    except queue.Empty:
                                        pass

                    # ⚡ ENHANCED: Adaptive sleep based on activity
                    time.sleep(0.05 if items else 0.2)

                except Exception as e:
                    consecutive_errors += 1
                    print(f"[IMPROVED] Error in message fetcher ({consecutive_errors}/{max_consecutive_errors}): {e}")
                    time.sleep(min(consecutive_errors, 5))  # Exponential backoff

        except Exception as e:
            print(f"[IMPROVED] Fatal error in enhanced message fetcher: {e}")

        print("[IMPROVED] Enhanced message fetcher stopped")

    def _enhanced_message_processor(self):
        """⚡ ENHANCED: More robust message processor"""
        print("[IMPROVED] Enhanced message processor started")

        try:
            while self.is_running:
                try:
                    # ⚡ ENHANCED: Get message with timeout
                    msg_data = self.message_queue.get(timeout=1.0)

                    author = msg_data['author']
                    message = msg_data['message']

                    print(f"[IMPROVED] Processing: {author}: {message}")

                    # ⚡ ENHANCED: Always call callback for all messages - DIRECT CALL
                    # Let the UI decide what to do with them
                    if self.is_running:
                        try:
                            # CRITICAL FIX: Call callback directly instead of using executor
                            # This ensures callback is executed immediately and reliably
                            self._safe_callback_enhanced(author, message)
                        except Exception as e:
                            print(f"[IMPROVED] Error in direct callback: {e}")

                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[IMPROVED] Error processing message: {e}")

        except Exception as e:
            print(f"[IMPROVED] Fatal error in enhanced message processor: {e}")

        print("[IMPROVED] Enhanced message processor stopped")

    def _is_valid_message_enhanced(self, item):
        """⚡ ENHANCED: Better message validation"""
        try:
            # ⚡ ENHANCED: More thorough checks
            if not item or not hasattr(item, 'author') or not hasattr(item, 'message'):
                return False

            if not item.author or not item.message:
                return False

            if not hasattr(item.author, 'name') or not item.author.name:
                return False

            if not item.message.strip():
                return False

            # ⚡ ENHANCED: Better deduplication
            msg_id = f"{item.author.name}:{item.message[:100]}:{int(time.time())}"
            if msg_id in self.seen_messages:
                return False

            # ⚡ ENHANCED: Smarter memory management
            if len(self.seen_messages) > 2000:
                # Keep only recent half
                recent_messages = list(self.seen_messages)[-1000:]
                self.seen_messages = set(recent_messages)

            self.seen_messages.add(msg_id)
            return True

        except Exception as e:
            print(f"[IMPROVED] Error validating message: {e}")
            return False

    def _reconnect_chat(self):
        """⚡ ENHANCED: Reconnect chat if connection lost"""
        try:
            print("[IMPROVED] Attempting to reconnect chat...")

            if self.chat:
                try:
                    self.chat.terminate()
                except Exception:
                    pass

            self.chat = pytchat.create(video_id=self.video_id)
            if self.chat and self.chat.is_alive():
                print("[IMPROVED] Chat reconnected successfully")
                return True
            else:
                print("[IMPROVED] Failed to reconnect chat")
                return False

        except Exception as e:
            print(f"[IMPROVED] Error reconnecting chat: {e}")
            return False

    def _safe_callback_enhanced(self, author, message):
        """⚡ ENHANCED: Execute callback with better error handling"""
        try:
            print(f"[LISTENER-CALLBACK] Checking callback for: {author}: {message[:50]}...")
            print(f"[LISTENER-CALLBACK] self.is_running = {self.is_running}")
            print(f"[LISTENER-CALLBACK] Listener object ID: {id(self)}")

            if self.is_running:
                print(f"[LISTENER-CALLBACK] About to call callback for: {author}: {message[:50]}...")
                print(f"[LISTENER-CALLBACK] Callback function: {self.callback}")
                self.callback(author, message)
                print(f"[LISTENER-CALLBACK] OK Callback executed successfully for: {author}")
            else:
                print(f"[LISTENER-CALLBACK] SKIP Listener not running (is_running={self.is_running}), skipping callback for: {author}")
        except Exception as e:
            print(f"[IMPROVED] ERROR Error in callback: {e}")
            import traceback
            print(f"[IMPROVED] Callback traceback: {traceback.format_exc()}")

    def stop(self):
        """🛑 Enhanced stop with better cleanup"""
        print("[IMPROVED] Stopping enhanced listener...")

        # First, signal all threads to stop
        self.is_running = False
        print("[IMPROVED] is_running set to False")

        # Wait for threads to notice stop signal
        time.sleep(0.3)

        try:
            if self.chat:
                self.chat.terminate()
                print("[IMPROVED] Chat terminated")
        except Exception as e:
            print(f"[IMPROVED] Error stopping chat: {e}")

        try:
            # Enhanced shutdown (timeout param only available in Python 3.9+)
            self.executor.shutdown(wait=True)
            print("[IMPROVED] Executor shutdown complete")
        except Exception as e:
            print(f"[IMPROVED] Error shutting down executor: {e}")

        # Clear the chat object
        self.chat = None

        print("[IMPROVED] Enhanced listener stopped completely")

def start_improved_lightweight_pytchat_listener(video_id, callback, trigger_words=None, reply_mode="Trigger"):
    """🚀 Start improved lightweight pytchat listener"""
    listener = ImprovedLightweightPytchatListener(video_id, callback, trigger_words, reply_mode)
    if listener.start():
        return listener
    return None
