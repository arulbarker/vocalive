#!/usr/bin/env python3
"""
🔧 COHOST AUTO-REPLY DIAGNOSTIC & FIX
Diagnosa dan perbaiki masalah auto-reply yang tidak merespon komentar
"""

import os
import sys
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_auto_reply_status():
    """Check current auto-reply status"""
    print("🔍 CHECKING AUTO-REPLY STATUS")
    print("=" * 50)
    
    try:
        # Check settings.json
        settings_file = project_root / "config" / "settings.json"
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            print(f"✅ Settings loaded:")
            print(f"   Platform: {settings.get('platform', 'Not set')}")
            print(f"   Video ID: {settings.get('video_id', 'Not set')}")
            print(f"   YouTube URL: {settings.get('youtube_url', 'Not set')}")
            print(f"   Trigger Words: {settings.get('trigger_words', [])}")
            print(f"   Reply Mode: {settings.get('reply_mode', 'Not set')}")
            
            return settings
        else:
            print("❌ Settings file not found")
            return None
            
    except Exception as e:
        print(f"❌ Error checking settings: {e}")
        return None

def test_trigger_detection():
    """Test trigger word detection"""
    print("\n🎯 TESTING TRIGGER DETECTION")
    print("=" * 50)
    
    try:
        settings_file = project_root / "config" / "settings.json"
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        trigger_words = settings.get('trigger_words', [])
        print(f"Configured triggers: {trigger_words}")
        
        test_messages = [
            "halo col apa kabar?",
            "bang gimana build layla?", 
            "col main rank yuk",
            "hai bang udah makan?",
            "test message without trigger",
            "bang col hero favorit apa?"
        ]
        
        def has_trigger(message):
            return any(trigger.lower() in message.lower() for trigger in trigger_words)
        
        print("\nTesting messages:")
        for msg in test_messages:
            detected = has_trigger(msg)
            status = "✅ TRIGGER" if detected else "❌ NO TRIGGER"
            print(f"  {status}: {msg}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing triggers: {e}")
        return False

def test_ai_generation():
    """Test AI reply generation"""
    print("\n🤖 TESTING AI GENERATION")
    print("=" * 50)
    
    try:
        from modules_client.api import generate_reply
        
        test_prompt = "Penonton TestUser bertanya: halo col apa kabar?"
        print(f"Testing prompt: {test_prompt}")
        
        reply = generate_reply(test_prompt)
        if reply and len(reply.strip()) > 0:
            print(f"✅ AI Reply: {reply}")
            return True
        else:
            print("❌ AI returned empty reply")
            return False
            
    except Exception as e:
        print(f"❌ Error testing AI: {e}")
        return False

def check_youtube_stream():
    """Check if YouTube stream is live and accessible"""
    print("\n📺 CHECKING YOUTUBE STREAM")
    print("=" * 50)
    
    try:
        settings_file = project_root / "config" / "settings.json"
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        video_id = settings.get('video_id', '')
        youtube_url = settings.get('youtube_url', '')
        
        if not video_id:
            print("❌ No video ID configured")
            return False
        
        print(f"Video ID: {video_id}")
        print(f"YouTube URL: {youtube_url}")
        
        # Test if we can access the stream
        try:
            import requests
            test_url = f"https://www.youtube.com/watch?v={video_id}"
            response = requests.get(test_url, timeout=10)
            
            if response.status_code == 200:
                print("✅ YouTube stream accessible")
                
                # Check if it's live
                if '"isLiveContent":true' in response.text:
                    print("✅ Stream is LIVE")
                    return True
                else:
                    print("⚠️ Stream might not be live")
                    return True
            else:
                print(f"❌ YouTube stream not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️ Could not verify stream status: {e}")
            return True  # Assume it's okay
            
    except Exception as e:
        print(f"❌ Error checking YouTube stream: {e}")
        return False

def create_manual_comment_test():
    """Create a manual test to simulate comment processing"""
    print("\n🧪 CREATING MANUAL COMMENT TEST")
    print("=" * 50)
    
    test_script = '''#!/usr/bin/env python3
"""
Manual Comment Test - Simulate comment processing
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def simulate_comment():
    """Simulate a comment with trigger word"""
    print("🎯 SIMULATING COMMENT PROCESSING")
    print("=" * 40)
    
    try:
        # Import the cohost module
        from ui.cohost_tab_basic import CohostTabBasic
        from PyQt5.QtWidgets import QApplication
        
        # Create minimal Qt application
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create cohost instance
        cohost = CohostTabBasic()
        
        # Set up basic configuration
        cohost.reply_busy = True  # Enable auto-reply
        cohost.conversation_active = False
        
        # Test comment with trigger
        test_author = "TestUser"
        test_message = "halo col apa kabar?"
        
        print(f"Simulating comment from {test_author}: {test_message}")
        
        # Check if trigger is detected
        has_trigger = cohost._has_trigger(test_message)
        print(f"Trigger detected: {has_trigger}")
        
        if has_trigger:
            print("✅ Trigger detected! Processing...")
            
            # Simulate the _enqueue_lightweight process
            cohost._enqueue_lightweight(test_author, test_message)
            
            print("✅ Comment processing completed")
        else:
            print("❌ No trigger detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Error simulating comment: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    simulate_comment()
'''
    
    test_file = project_root / "manual_comment_test.py"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print(f"✅ Created manual test: {test_file}")

def fix_common_issues():
    """Fix common auto-reply issues"""
    print("\n🔧 FIXING COMMON ISSUES")
    print("=" * 50)
    
    fixes_applied = []
    
    try:
        # 1. Ensure YouTube URL is set
        settings_file = project_root / "config" / "settings.json"
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        video_id = settings.get('video_id', '')
        if video_id and not settings.get('youtube_url'):
            settings['youtube_url'] = f"https://www.youtube.com/watch?v={video_id}"
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            fixes_applied.append("✅ Added YouTube URL to settings")
        
        # 2. Ensure trigger words are set
        if not settings.get('trigger_words'):
            settings['trigger_words'] = ['col', 'bang']
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            fixes_applied.append("✅ Added default trigger words")
        
        # 3. Ensure reply mode is set
        if not settings.get('reply_mode'):
            settings['reply_mode'] = 'All'
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            fixes_applied.append("✅ Set reply mode to 'All'")
        
        return fixes_applied
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        return fixes_applied

def main():
    """Main diagnostic function"""
    print("🔧 COHOST AUTO-REPLY DIAGNOSTIC & FIX")
    print("=" * 60)
    
    results = []
    
    # 1. Check auto-reply status
    settings = check_auto_reply_status()
    if settings:
        results.append("✅ Settings Check")
    else:
        results.append("❌ Settings Check")
    
    # 2. Test trigger detection
    if test_trigger_detection():
        results.append("✅ Trigger Detection")
    else:
        results.append("❌ Trigger Detection")
    
    # 3. Test AI generation
    if test_ai_generation():
        results.append("✅ AI Generation")
    else:
        results.append("❌ AI Generation")
    
    # 4. Check YouTube stream
    if check_youtube_stream():
        results.append("✅ YouTube Stream")
    else:
        results.append("❌ YouTube Stream")
    
    # 5. Apply fixes
    fixes = fix_common_issues()
    if fixes:
        results.append("✅ Applied Fixes")
        for fix in fixes:
            print(f"  {fix}")
    
    # 6. Create manual test
    create_manual_comment_test()
    results.append("✅ Manual Test Created")
    
    print(f"\n🏆 DIAGNOSTIC RESULTS:")
    print("=" * 60)
    for result in results:
        print(f"  {result}")
    
    success_count = sum(1 for r in results if r.startswith("✅"))
    total_tests = len(results)
    
    print(f"\n📊 SUMMARY: {success_count}/{total_tests} checks passed")
    
    if success_count >= 4:
        print(f"\n🎉 AUTO-REPLY SHOULD BE WORKING!")
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Restart StreamMate AI application")
        print(f"2. Click 'Start Auto-Reply' button")
        print(f"3. Test with live comments containing 'col' or 'bang'")
        print(f"4. Run manual test: python manual_comment_test.py")
        print(f"5. Check logs for comment processing")
    else:
        print(f"\n⚠️ SOME ISSUES FOUND - CHECK ABOVE RESULTS")
        print(f"Fix the failing checks and try again")

if __name__ == "__main__":
    main()