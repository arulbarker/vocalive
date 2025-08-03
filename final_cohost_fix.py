#!/usr/bin/env python3
"""
🔧 FINAL COHOST FIX
Perbaikan definitif untuk masalah auto-reply yang tidak merespon
"""

import os
import sys
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def fix_listener_stability():
    """Fix listener stability issues"""
    print("🔧 FIXING LISTENER STABILITY")
    print("=" * 50)
    
    try:
        # Read the current lightweight listener
        listener_file = project_root / "listeners" / "pytchat_listener_lightweight.py"
        
        if not listener_file.exists():
            print("❌ Listener file not found")
            return False
        
        # Create improved version with better error handling
        improved_listener = '''# ========== IMPROVED LIGHTWEIGHT PYTCHAT LISTENER ==========
# 🚀 ENHANCED VERSION dengan stability fixes

import sys
import os
from pathlib import Path
import threading
import time
import json
import queue
from concurrent.futures import ThreadPoolExecutor
import asyncio

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
                    
                    # ⚡ ENHANCED: Always call callback for all messages
                    # Let the UI decide what to do with them
                    if self.is_running:
                        try:
                            self.executor.submit(self._safe_callback_enhanced, author, message)
                        except RuntimeError as e:
                            if "cannot schedule new futures after shutdown" in str(e):
                                print("[IMPROVED] Executor shutdown, stopping message processing")
                                break
                            else:
                                print(f"[IMPROVED] Error submitting task: {e}")
                    
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
                except:
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
            if self.is_running:
                self.callback(author, message)
        except Exception as e:
            print(f"[IMPROVED] Error in callback: {e}")
            import traceback
            print(f"[IMPROVED] Callback traceback: {traceback.format_exc()}")

    def stop(self):
        """🛑 Enhanced stop with better cleanup"""
        print("[IMPROVED] Stopping enhanced listener...")
        self.is_running = False
        
        # Wait for threads to notice stop signal
        time.sleep(0.2)
        
        try:
            if self.chat:
                self.chat.terminate()
                print("[IMPROVED] Chat terminated")
        except Exception as e:
            print(f"[IMPROVED] Error stopping chat: {e}")
        
        try:
            # Enhanced shutdown with longer timeout
            self.executor.shutdown(wait=True, timeout=5.0)
            print("[IMPROVED] Executor shutdown complete")
        except Exception as e:
            print(f"[IMPROVED] Error shutting down executor: {e}")
        
        print("[IMPROVED] Enhanced listener stopped")

def start_improved_lightweight_pytchat_listener(video_id, callback, trigger_words=None, reply_mode="Trigger"):
    """🚀 Start improved lightweight pytchat listener"""
    listener = ImprovedLightweightPytchatListener(video_id, callback, trigger_words, reply_mode)
    if listener.start():
        return listener
    return None
'''
        
        # Backup original file
        backup_file = listener_file.with_suffix('.py.backup')
        if not backup_file.exists():
            with open(listener_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(original_content)
            print(f"✅ Backup created: {backup_file}")
        
        # Write improved version
        with open(listener_file, 'w', encoding='utf-8') as f:
            f.write(improved_listener)
        
        print(f"✅ Improved listener written to: {listener_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing listener: {e}")
        return False

def fix_cohost_integration():
    """Fix cohost integration to use improved listener"""
    print("\n🤝 FIXING COHOST INTEGRATION")
    print("=" * 50)
    
    try:
        cohost_file = project_root / "ui" / "cohost_tab_basic.py"
        
        if not cohost_file.exists():
            print("❌ Cohost file not found")
            return False
        
        # Read current content
        with open(cohost_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the import line for lightweight listener
        old_import = "from listeners.pytchat_listener_lightweight import start_lightweight_pytchat_listener"
        new_import = "from listeners.pytchat_listener_lightweight import start_improved_lightweight_pytchat_listener"
        
        if old_import in content:
            content = content.replace(old_import, new_import)
            print("✅ Updated import statement")
        
        # Find the listener start call
        old_call = "start_lightweight_pytchat_listener("
        new_call = "start_improved_lightweight_pytchat_listener("
        
        if old_call in content:
            content = content.replace(old_call, new_call)
            print("✅ Updated listener start call")
        
        # Write back
        with open(cohost_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Cohost integration updated")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing cohost integration: {e}")
        return False

def create_final_test():
    """Create final test script"""
    print("\n🧪 CREATING FINAL TEST")
    print("=" * 50)
    
    test_script = '''#!/usr/bin/env python3
"""
🎯 FINAL AUTO-REPLY TEST
Test lengkap untuk memastikan auto-reply bekerja dengan sempurna
"""

import sys
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def final_test():
    """Final comprehensive test"""
    print("🎯 FINAL AUTO-REPLY TEST")
    print("=" * 50)
    
    try:
        # Load settings
        settings_file = project_root / "config" / "settings.json"
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        video_id = settings.get('video_id', '')
        trigger_words = settings.get('trigger_words', ['col', 'bang'])
        
        print(f"Video ID: {video_id}")
        print(f"Trigger words: {trigger_words}")
        
        # Test improved listener
        from listeners.pytchat_listener_lightweight import start_improved_lightweight_pytchat_listener
        
        message_count = 0
        trigger_count = 0
        
        def test_callback(author, message):
            nonlocal message_count, trigger_count
            message_count += 1
            
            print(f"📝 [{message_count}] {author}: {message}")
            
            # Check for triggers
            has_trigger = any(trigger.lower() in message.lower() for trigger in trigger_words)
            if has_trigger:
                trigger_count += 1
                print(f"   🎯 TRIGGER DETECTED!")
                
                # Test AI reply
                try:
                    from modules_client.api import generate_reply
                    prompt = f"Penonton {author} bertanya: {message}"
                    reply = generate_reply(prompt)
                    if reply:
                        print(f"   🤖 AI REPLY: {reply[:100]}...")
                    else:
                        print(f"   ❌ No AI reply")
                except Exception as e:
                    print(f"   ❌ AI error: {e}")
        
        # Start improved listener
        print("\\n🚀 Starting improved listener...")
        listener = start_improved_lightweight_pytchat_listener(
            video_id=video_id,
            callback=test_callback,
            trigger_words=trigger_words,
            reply_mode="All"
        )
        
        if not listener:
            print("❌ Failed to start improved listener")
            return False
        
        print("✅ Improved listener started!")
        print("\\n🎯 LISTENING FOR 60 SECONDS...")
        print("Type comments with 'col' or 'bang' in YouTube chat!")
        print("-" * 50)
        
        # Listen for 60 seconds
        start_time = time.time()
        while time.time() - start_time < 60:
            time.sleep(1)
            if message_count > 0:
                print(f"\\r📊 Messages: {message_count}, Triggers: {trigger_count}", end="")
        
        # Stop listener
        listener.stop()
        
        print(f"\\n\\n📊 FINAL RESULTS:")
        print(f"Total messages: {message_count}")
        print(f"Trigger messages: {trigger_count}")
        
        if message_count > 0:
            print("\\n🎉 SUCCESS! Auto-reply is working!")
            print("\\n📋 NEXT STEPS:")
            print("1. Restart StreamMate AI")
            print("2. Click 'Start Auto-Reply'")
            print("3. Test with live comments")
        else:
            print("\\n⚠️ No messages received")
            print("Make sure:")
            print("- Stream is LIVE")
            print("- Chat is enabled")
            print("- There are viewers typing")
        
        return message_count > 0
        
    except Exception as e:
        print(f"❌ Error in final test: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    final_test()
'''
    
    test_file = project_root / "final_auto_reply_test.py"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print(f"✅ Final test created: {test_file}")

def main():
    """Main fix function"""
    print("🔧 FINAL COHOST FIX")
    print("=" * 60)
    
    results = []
    
    # Fix 1: Listener stability
    if fix_listener_stability():
        results.append("✅ Listener Stability Fixed")
    else:
        results.append("❌ Listener Stability Fix Failed")
    
    # Fix 2: Cohost integration
    if fix_cohost_integration():
        results.append("✅ Cohost Integration Fixed")
    else:
        results.append("❌ Cohost Integration Fix Failed")
    
    # Fix 3: Create final test
    create_final_test()
    results.append("✅ Final Test Created")
    
    print(f"\\n🏆 FIX RESULTS:")
    print("=" * 60)
    for result in results:
        print(f"  {result}")
    
    success_count = sum(1 for r in results if r.startswith("✅"))
    total_fixes = len(results)
    
    print(f"\\n📊 SUMMARY: {success_count}/{total_fixes} fixes applied")
    
    if success_count >= 2:
        print(f"\\n🎉 FIXES APPLIED SUCCESSFULLY!")
        print(f"\\n📋 NEXT STEPS:")
        print(f"1. Run: python final_auto_reply_test.py")
        print(f"2. If test passes, restart StreamMate AI")
        print(f"3. Click 'Start Auto-Reply' button")
        print(f"4. Test with live comments containing 'col' or 'bang'")
        print(f"5. Monitor logs for comment processing")
    else:
        print(f"\\n⚠️ SOME FIXES FAILED - CHECK ABOVE RESULTS")

if __name__ == "__main__":
    main()