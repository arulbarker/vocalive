#!/usr/bin/env python3
"""
🧪 Manual Auto-Reply Test Script
Test auto-reply functionality secara manual
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_trigger_detection():
    """Test deteksi trigger words"""
    print("🔍 Testing Trigger Detection...")
    
    try:
        from modules_client.config_manager import ConfigManager
        cfg = ConfigManager("config/settings.json")
        
        trigger_words = cfg.get("trigger_words", [])
        print(f"Configured trigger words: {trigger_words}")
        
        test_messages = [
            "halo col apa kabar?",
            "bang gimana build layla?", 
            "col main rank yuk",
            "test message without trigger"
        ]
        
        for msg in test_messages:
            has_trigger = any(trigger.lower() in msg.lower() for trigger in trigger_words)
            status = "✅ TRIGGER" if has_trigger else "❌ NO TRIGGER"
            print(f"{status}: {msg}")
            
    except Exception as e:
        print(f"❌ Error testing trigger detection: {e}")

def test_ai_reply_generation():
    """Test AI reply generation"""
    print("\n🤖 Testing AI Reply Generation...")
    
    try:
        from modules_client.api import generate_reply
        
        test_prompts = [
            "Penonton TestUser bertanya: halo col apa kabar?",
            "Penonton Gamer123 bertanya: bang build layla gimana?",
            "Penonton ProPlayer bertanya: col main rank yuk"
        ]
        
        for prompt in test_prompts:
            print(f"\n📝 Testing: {prompt}")
            reply = generate_reply(prompt)
            print(f"📤 Reply: {reply}")
            time.sleep(1)  # Rate limiting
            
    except Exception as e:
        print(f"❌ Error testing AI generation: {e}")

def simulate_comment_processing():
    """Simulasi pemrosesan komentar dengan trigger"""
    print("\n🎯 Simulating Comment Processing...")
    
    try:
        from ui.cohost_tab_basic import CohostTabBasic
        from PyQt5.QtWidgets import QApplication
        
        # Create minimal Qt application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create cohost tab instance
        cohost_tab = CohostTabBasic()
        
        # Test comment processing
        test_comments = [
            ("TestUser", "halo col apa kabar?"),
            ("Gamer123", "bang build layla gimana?"),
            ("ProPlayer", "col main rank yuk")
        ]
        
        for author, message in test_comments:
            print(f"\n👤 Processing: {author}: {message}")
            
            # Check if has trigger
            has_trigger = cohost_tab._has_trigger(message)
            print(f"🔍 Has trigger: {has_trigger}")
            
            if has_trigger:
                # Simulate reply generation
                print(f"⚡ Generating reply...")
                # This would normally be handled by the thread
                
    except Exception as e:
        print(f"❌ Error simulating comment processing: {e}")

if __name__ == "__main__":
    print("🧪 StreamMate AI - Manual Test Script")
    print("=" * 50)
    
    test_trigger_detection()
    test_ai_reply_generation()
    simulate_comment_processing()
    
    print("\n✅ Manual testing completed!")
