#!/usr/bin/env python3
"""
🔧 Fix Auto-Reply Issues - Comprehensive Solution
Memperbaiki masalah auto-reply yang tidak berfungsi secara sistematis
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def fix_api_bridge_issue():
    """Perbaiki masalah APIBridge yang tidak memiliki active_server"""
    print("🔧 Fixing APIBridge Issue...")
    print("=" * 50)
    
    api_file = project_root / "modules_client" / "api.py"
    
    try:
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if APIBridge has active_server initialization
        if "self.active_server = self._get_active_server()" not in content:
            print("❌ APIBridge missing active_server initialization")
            
            # Find APIBridge __init__ method and add missing initialization
            lines = content.split('\n')
            new_lines = []
            in_apibridge_init = False
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                
                # Find APIBridge __init__ method
                if "class APIBridge:" in line:
                    in_apibridge_init = True
                elif in_apibridge_init and "def __init__(self):" in line:
                    # Add missing initialization after __init__
                    j = i + 1
                    while j < len(lines) and (lines[j].strip() == "" or lines[j].startswith("        ")):
                        new_lines.append(lines[j])
                        j += 1
                    
                    # Add missing attributes
                    if "self.vps_server" not in content:
                        new_lines.append("        self.vps_server = \"http://69.62.79.238:8000\"")
                    if "self.local_server" not in content:
                        new_lines.append("        self.local_server = \"http://localhost:8888\"")
                    if "self.active_server" not in content:
                        new_lines.append("        self.active_server = self._get_active_server()")
                    
                    # Skip the lines we already processed
                    i = j - 1
                    in_apibridge_init = False
            
            # Write back the fixed content
            with open(api_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
            print("✅ Fixed APIBridge initialization")
            return True
        else:
            print("✅ APIBridge already has proper initialization")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing APIBridge: {e}")
        return False

def fix_supabase_client_issue():
    """Perbaiki masalah Supabase client yang tidak memiliki generate_ai_reply method"""
    print("\n🔧 Fixing Supabase Client Issue...")
    print("=" * 50)
    
    supabase_file = project_root / "modules_client" / "supabase_client.py"
    
    if not supabase_file.exists():
        print("❌ Supabase client file not found")
        return False
    
    try:
        with open(supabase_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if generate_ai_reply method exists
        if "def generate_ai_reply" not in content:
            print("❌ Supabase client missing generate_ai_reply method")
            
            # Add the missing method
            method_code = '''
    def generate_ai_reply(self, prompt: str, timeout: int = 30) -> str:
        """Generate AI reply using Supabase Edge Function"""
        try:
            response = self.supabase.functions.invoke(
                "ai-generate",
                invoke_options={
                    "body": {"prompt": prompt},
                    "headers": {"Content-Type": "application/json"}
                }
            )
            
            if response and hasattr(response, 'data'):
                data = response.data
                if isinstance(data, dict) and "reply" in data:
                    return data["reply"]
                elif isinstance(data, str):
                    return data
            
            return None
            
        except Exception as e:
            print(f"[Supabase] AI generation error: {e}")
            return None
'''
            
            # Find the class and add the method
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                new_lines.append(line)
                # Add method after class definition
                if line.strip().startswith("class ") and "SupabaseClient" in line:
                    # Find the end of __init__ method
                    pass
            
            # Add method at the end of the class
            if content.strip().endswith('"""'):
                # Remove the last docstring and add method
                content = content.rstrip('"""').rstrip() + method_code + '\n"""'
            else:
                content += method_code
            
            with open(supabase_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Added generate_ai_reply method to Supabase client")
            return True
        else:
            print("✅ Supabase client already has generate_ai_reply method")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing Supabase client: {e}")
        return False

def fix_youtube_url_config():
    """Perbaiki konfigurasi YouTube URL"""
    print("\n🔧 Fixing YouTube URL Configuration...")
    print("=" * 50)
    
    config_file = project_root / "config" / "settings.json"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check if video_id exists but youtube_url doesn't
        if "video_id" in config and "youtube_url" not in config:
            video_id = config["video_id"]
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            config["youtube_url"] = youtube_url
            
            print(f"✅ Added youtube_url: {youtube_url}")
            
            # Save the updated config
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
        elif "youtube_url" in config:
            print(f"✅ YouTube URL already configured: {config['youtube_url']}")
            return True
        else:
            print("❌ No video_id or youtube_url found in config")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing YouTube URL config: {e}")
        return False

def test_fixed_ai_generation():
    """Test AI generation setelah perbaikan"""
    print("\n🤖 Testing Fixed AI Generation...")
    print("=" * 50)
    
    try:
        # Reload modules to get the fixes
        import importlib
        if 'modules_client.api' in sys.modules:
            importlib.reload(sys.modules['modules_client.api'])
        
        from modules_client.api import generate_reply
        
        test_prompt = "Penonton TestUser bertanya: halo bang apa kabar?"
        print(f"📝 Test Prompt: {test_prompt}")
        print(f"⏳ Generating reply...")
        
        reply = generate_reply(test_prompt)
        
        if reply and len(reply.strip()) > 0:
            print(f"✅ AI Generation: SUCCESS")
            print(f"📤 Reply: {reply}")
            
            # Check if it's not just fallback response
            if "gangguan koneksi AI" not in reply and "bermasalah" not in reply:
                print(f"🎉 Real AI response detected!")
                return True
            else:
                print(f"⚠️ Fallback response detected - API still has issues")
                return False
        else:
            print(f"❌ AI Generation: Empty reply")
            return False
            
    except Exception as e:
        print(f"❌ AI Generation test failed: {e}")
        return False

def create_manual_test_script():
    """Buat skrip untuk test manual auto-reply"""
    print("\n📝 Creating Manual Test Script...")
    print("=" * 50)
    
    test_script = '''#!/usr/bin/env python3
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
    print("\\n🤖 Testing AI Reply Generation...")
    
    try:
        from modules_client.api import generate_reply
        
        test_prompts = [
            "Penonton TestUser bertanya: halo col apa kabar?",
            "Penonton Gamer123 bertanya: bang build layla gimana?",
            "Penonton ProPlayer bertanya: col main rank yuk"
        ]
        
        for prompt in test_prompts:
            print(f"\\n📝 Testing: {prompt}")
            reply = generate_reply(prompt)
            print(f"📤 Reply: {reply}")
            time.sleep(1)  # Rate limiting
            
    except Exception as e:
        print(f"❌ Error testing AI generation: {e}")

def simulate_comment_processing():
    """Simulasi pemrosesan komentar dengan trigger"""
    print("\\n🎯 Simulating Comment Processing...")
    
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
            print(f"\\n👤 Processing: {author}: {message}")
            
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
    
    print("\\n✅ Manual testing completed!")
'''
    
    test_file = project_root / "manual_test_auto_reply.py"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print(f"✅ Created manual test script: {test_file}")

def main():
    """Main fix function"""
    print("🚀 StreamMate AI - Auto-Reply Fix Tool")
    print("=" * 60)
    
    fixes_applied = []
    
    # 1. Fix APIBridge issue
    if fix_api_bridge_issue():
        fixes_applied.append("✅ APIBridge initialization")
    
    # 2. Fix Supabase client issue
    if fix_supabase_client_issue():
        fixes_applied.append("✅ Supabase client method")
    
    # 3. Fix YouTube URL config
    if fix_youtube_url_config():
        fixes_applied.append("✅ YouTube URL configuration")
    
    # 4. Test fixed AI generation
    if test_fixed_ai_generation():
        fixes_applied.append("✅ AI generation working")
    
    # 5. Create manual test script
    create_manual_test_script()
    fixes_applied.append("✅ Manual test script created")
    
    print(f"\n🎉 FIXES APPLIED ({len(fixes_applied)}):")
    for fix in fixes_applied:
        print(f"  {fix}")
    
    print(f"\n📋 NEXT STEPS:")
    print(f"1. Restart StreamMate AI application")
    print(f"2. Click 'Start Auto-Reply' button")
    print(f"3. Test with trigger words: 'col' or 'bang'")
    print(f"4. Run manual test: python manual_test_auto_reply.py")
    print(f"5. Check YouTube stream has live comments")

if __name__ == "__main__":
    main()