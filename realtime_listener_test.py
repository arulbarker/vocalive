#!/usr/bin/env python3
"""
🔍 REAL-TIME LISTENER DIAGNOSTIC
Test YouTube listener untuk melihat apakah komentar benar-benar masuk
"""

import sys
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_pytchat_direct():
    """Test pytchat directly without our wrapper"""
    print("🔍 TESTING PYTCHAT DIRECTLY")
    print("=" * 50)
    
    try:
        # Load video ID from settings
        settings_file = project_root / "config" / "settings.json"
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        video_id = settings.get('video_id', '')
        if not video_id:
            print("❌ No video ID found in settings")
            return False
        
        print(f"Video ID: {video_id}")
        
        # Import pytchat
        try:
            import pytchat
            print("✅ PyTchat imported successfully")
        except ImportError as e:
            print(f"❌ PyTchat import failed: {e}")
            return False
        
        # Create chat object
        print("Creating chat object...")
        chat = pytchat.create(video_id=video_id)
        
        if not chat:
            print("❌ Failed to create chat object")
            return False
        
        print("✅ Chat object created successfully")
        print(f"Chat is alive: {chat.is_alive()}")
        
        # Test fetching messages for 30 seconds
        print("\n🎯 LISTENING FOR COMMENTS (30 seconds)...")
        print("Type comments in the YouTube chat to test!")
        print("-" * 50)
        
        start_time = time.time()
        message_count = 0
        
        while time.time() - start_time < 30:
            try:
                if not chat.is_alive():
                    print("❌ Chat connection lost")
                    break
                
                # Get messages
                items = chat.get().sync_items()
                
                for item in items:
                    message_count += 1
                    author = item.author.name if item.author else "Unknown"
                    message = item.message if item.message else ""
                    
                    print(f"📝 [{message_count}] {author}: {message}")
                
                time.sleep(0.1)  # Small delay
                
            except Exception as e:
                print(f"⚠️ Error fetching messages: {e}")
                time.sleep(1)
        
        print(f"\n📊 RESULTS:")
        print(f"Total messages received: {message_count}")
        
        if message_count > 0:
            print("✅ PyTchat is working and receiving comments!")
            return True
        else:
            print("⚠️ No comments received - stream might be inactive or no viewers")
            return True  # Not necessarily an error
        
    except Exception as e:
        print(f"❌ Error testing pytchat: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False
    
    finally:
        try:
            if 'chat' in locals() and chat:
                chat.terminate()
                print("🛑 Chat connection terminated")
        except:
            pass

def test_lightweight_listener():
    """Test our lightweight listener"""
    print("\n🚀 TESTING LIGHTWEIGHT LISTENER")
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
        
        # Import our listener
        from listeners.pytchat_listener_lightweight import start_lightweight_pytchat_listener
        
        # Message counter
        message_count = 0
        trigger_count = 0
        
        def test_callback(author, message):
            nonlocal message_count, trigger_count
            message_count += 1
            
            # Check for triggers
            has_trigger = any(trigger.lower() in message.lower() for trigger in trigger_words)
            if has_trigger:
                trigger_count += 1
                print(f"🎯 TRIGGER [{trigger_count}] {author}: {message}")
            else:
                print(f"📝 [{message_count}] {author}: {message}")
        
        # Start listener
        print("Starting lightweight listener...")
        listener = start_lightweight_pytchat_listener(
            video_id=video_id,
            callback=test_callback,
            trigger_words=trigger_words,
            reply_mode="All"
        )
        
        if not listener:
            print("❌ Failed to start lightweight listener")
            return False
        
        print("✅ Lightweight listener started successfully")
        print("\n🎯 LISTENING FOR COMMENTS (30 seconds)...")
        print("Type comments in the YouTube chat to test!")
        print("-" * 50)
        
        # Listen for 30 seconds
        time.sleep(30)
        
        # Stop listener
        listener.stop()
        
        print(f"\n📊 RESULTS:")
        print(f"Total messages: {message_count}")
        print(f"Trigger messages: {trigger_count}")
        
        if message_count > 0:
            print("✅ Lightweight listener is working!")
            return True
        else:
            print("⚠️ No messages received through lightweight listener")
            return False
        
    except Exception as e:
        print(f"❌ Error testing lightweight listener: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_cohost_integration():
    """Test if cohost can receive messages"""
    print("\n🤝 TESTING COHOST INTEGRATION")
    print("=" * 50)
    
    try:
        # Load settings
        settings_file = project_root / "config" / "settings.json"
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        video_id = settings.get('video_id', '')
        trigger_words = settings.get('trigger_words', ['col', 'bang'])
        
        # Simulate cohost callback
        def cohost_callback(author, message):
            print(f"🤝 COHOST RECEIVED: {author}: {message}")
            
            # Simulate trigger check
            has_trigger = any(trigger.lower() in message.lower() for trigger in trigger_words)
            if has_trigger:
                print(f"   🎯 TRIGGER DETECTED!")
                
                # Simulate AI reply generation
                try:
                    from modules_client.api import generate_reply
                    prompt = f"Penonton {author} bertanya: {message}"
                    reply = generate_reply(prompt)
                    if reply:
                        print(f"   🤖 AI REPLY: {reply[:100]}...")
                    else:
                        print(f"   ❌ No AI reply generated")
                except Exception as e:
                    print(f"   ❌ AI reply error: {e}")
        
        # Test with sample messages
        test_messages = [
            ("TestUser1", "halo col apa kabar?"),
            ("TestUser2", "bang gimana build layla?"),
            ("TestUser3", "hello everyone"),
            ("TestUser4", "col main rank yuk")
        ]
        
        print("Simulating cohost message processing:")
        for author, message in test_messages:
            cohost_callback(author, message)
            time.sleep(0.5)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing cohost integration: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🔍 REAL-TIME LISTENER DIAGNOSTIC")
    print("=" * 60)
    
    results = []
    
    # Test 1: Direct pytchat
    if test_pytchat_direct():
        results.append("✅ Direct PyTchat")
    else:
        results.append("❌ Direct PyTchat")
    
    # Test 2: Lightweight listener
    if test_lightweight_listener():
        results.append("✅ Lightweight Listener")
    else:
        results.append("❌ Lightweight Listener")
    
    # Test 3: Cohost integration
    if test_cohost_integration():
        results.append("✅ Cohost Integration")
    else:
        results.append("❌ Cohost Integration")
    
    print(f"\n🏆 DIAGNOSTIC RESULTS:")
    print("=" * 60)
    for result in results:
        print(f"  {result}")
    
    success_count = sum(1 for r in results if r.startswith("✅"))
    total_tests = len(results)
    
    print(f"\n📊 SUMMARY: {success_count}/{total_tests} tests passed")
    
    if success_count >= 2:
        print(f"\n💡 DIAGNOSIS:")
        if "❌ Direct PyTchat" in results:
            print("- PyTchat connection issue - check video ID or stream status")
        if "❌ Lightweight Listener" in results:
            print("- Lightweight listener issue - check implementation")
        if "❌ Cohost Integration" in results:
            print("- Cohost integration issue - check callback setup")
        
        print(f"\n🔧 RECOMMENDATIONS:")
        print("1. Make sure YouTube stream is LIVE and has active chat")
        print("2. Verify video ID is correct and stream is public")
        print("3. Check if there are actual viewers typing comments")
        print("4. Restart the application and try again")
        print("5. Test with a different live stream if possible")
    else:
        print(f"\n⚠️ MULTIPLE ISSUES FOUND")
        print("Check the individual test results above for specific problems")

if __name__ == "__main__":
    main()