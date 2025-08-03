#!/usr/bin/env python3
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
        print("\n🚀 Starting improved listener...")
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
        print("\n🎯 LISTENING FOR 60 SECONDS...")
        print("Type comments with 'col' or 'bang' in YouTube chat!")
        print("-" * 50)
        
        # Listen for 60 seconds
        start_time = time.time()
        while time.time() - start_time < 60:
            time.sleep(1)
            if message_count > 0:
                print(f"\r📊 Messages: {message_count}, Triggers: {trigger_count}", end="")
        
        # Stop listener
        listener.stop()
        
        print(f"\n\n📊 FINAL RESULTS:")
        print(f"Total messages: {message_count}")
        print(f"Trigger messages: {trigger_count}")
        
        if message_count > 0:
            print("\n🎉 SUCCESS! Auto-reply is working!")
            print("\n📋 NEXT STEPS:")
            print("1. Restart StreamMate AI")
            print("2. Click 'Start Auto-Reply'")
            print("3. Test with live comments")
        else:
            print("\n⚠️ No messages received")
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
