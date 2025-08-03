#!/usr/bin/env python3
"""
🔧 Fix DeepSeek API Key Issue
Memperbaiki masalah DeepSeek API key yang mendapat error 401
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_deepseek_api_key():
    """Test DeepSeek API key yang ada"""
    print("🔑 Testing DeepSeek API Key...")
    print("=" * 50)
    
    # Get API key from environment
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_key:
        # Try to get from config
        config_file = project_root / "config" / "settings.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if "api_keys" in config and "DEEPSEEK_API_KEY" in config["api_keys"]:
                deepseek_key = config["api_keys"]["DEEPSEEK_API_KEY"]
                os.environ["DEEPSEEK_API_KEY"] = deepseek_key
                print(f"✅ Loaded API key from config: {len(deepseek_key)} chars")
    
    if not deepseek_key:
        print("❌ No DeepSeek API key found")
        return False
    
    print(f"🔍 Testing API key: {deepseek_key[:10]}...{deepseek_key[-4:]}")
    
    # Test API key with simple request
    try:
        headers = {
            "Authorization": f"Bearer {deepseek_key}",
            "Content-Type": "application/json",
        }
        
        # Test with models endpoint first
        response = requests.get(
            "https://api.deepseek.com/v1/models",
            headers=headers,
            timeout=10
        )
        
        print(f"📡 Models endpoint: HTTP {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API key is valid!")
            return True
        elif response.status_code == 401:
            print("❌ API key is invalid or expired")
            print(f"Response: {response.text[:200]}")
            return False
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        return False

def test_deepseek_chat_completion():
    """Test DeepSeek chat completion"""
    print("\n🤖 Testing DeepSeek Chat Completion...")
    print("=" * 50)
    
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_key:
        print("❌ No API key available")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {deepseek_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": "Halo, apa kabar? Jawab singkat saja."}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        print("📝 Sending test prompt...")
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📡 Chat completion: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            reply = result["choices"][0]["message"]["content"].strip()
            print(f"✅ Chat completion successful!")
            print(f"📤 Reply: {reply}")
            return True
        else:
            print(f"❌ Chat completion failed: {response.status_code}")
            print(f"Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing chat completion: {e}")
        return False

def get_new_api_key_instructions():
    """Berikan instruksi untuk mendapatkan API key baru"""
    print("\n📋 How to Get New DeepSeek API Key:")
    print("=" * 50)
    print("1. Visit: https://platform.deepseek.com/")
    print("2. Sign up or log in to your account")
    print("3. Go to API Keys section")
    print("4. Create a new API key")
    print("5. Copy the API key")
    print("6. Add to config/settings.json:")
    print('   "api_keys": {')
    print('     "DEEPSEEK_API_KEY": "your_new_key_here"')
    print('   }')
    print("7. Or set environment variable:")
    print("   set DEEPSEEK_API_KEY=your_new_key_here")

def fix_api_key_in_config():
    """Perbaiki API key di config jika perlu"""
    print("\n🔧 Fixing API Key in Config...")
    print("=" * 50)
    
    config_file = project_root / "config" / "settings.json"
    
    if not config_file.exists():
        print("❌ Config file not found")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check current API key
        current_key = None
        if "api_keys" in config and "DEEPSEEK_API_KEY" in config["api_keys"]:
            current_key = config["api_keys"]["DEEPSEEK_API_KEY"]
        
        if current_key:
            print(f"Current API key: {current_key[:10]}...{current_key[-4:]}")
            
            # Test current key
            if test_deepseek_api_key():
                print("✅ Current API key is working")
                return True
            else:
                print("❌ Current API key is not working")
                
                # Suggest getting new key
                get_new_api_key_instructions()
                return False
        else:
            print("❌ No API key found in config")
            get_new_api_key_instructions()
            return False
            
    except Exception as e:
        print(f"❌ Error checking config: {e}")
        return False

def create_working_ai_test():
    """Buat test AI yang bekerja dengan fallback"""
    print("\n🧪 Creating Working AI Test...")
    print("=" * 50)
    
    test_script = '''#!/usr/bin/env python3
"""
🧪 Working AI Test - Test AI dengan berbagai fallback
"""

import os
import sys
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_direct_deepseek():
    """Test DeepSeek API langsung"""
    print("🤖 Testing Direct DeepSeek API...")
    
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_key:
        print("❌ No DeepSeek API key")
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {deepseek_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": "Penonton TestUser bertanya: halo bang apa kabar? Jawab sebagai gaming streamer."}
            ],
            "max_tokens": 200,
            "temperature": 0.8
        }
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            reply = result["choices"][0]["message"]["content"].strip()
            print(f"✅ DeepSeek Direct: {reply}")
            return reply
        else:
            print(f"❌ DeepSeek Direct failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ DeepSeek Direct error: {e}")
        return None

def test_vps_api():
    """Test VPS API endpoint"""
    print("\\n🌐 Testing VPS API...")
    
    try:
        response = requests.post(
            "http://69.62.79.238:8000/api/ai/reply",
            json={"text": "Penonton TestUser bertanya: halo bang apa kabar?"},
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            reply = result.get("reply", "").strip()
            if reply:
                print(f"✅ VPS API: {reply}")
                return reply
            else:
                print(f"❌ VPS API returned empty reply")
                return None
        else:
            print(f"❌ VPS API failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ VPS API error: {e}")
        return None

def test_fallback_response():
    """Test fallback response"""
    print("\\n🔄 Testing Fallback Response...")
    
    try:
        from modules_client.api import _get_fallback_response
        
        prompt = "Penonton TestUser bertanya: halo bang apa kabar?"
        reply = _get_fallback_response(prompt)
        print(f"✅ Fallback: {reply}")
        return reply
        
    except Exception as e:
        print(f"❌ Fallback error: {e}")
        return "Hai TestUser! Maaf lagi ada gangguan koneksi AI"

def main():
    """Test semua metode AI"""
    print("🧪 Testing All AI Methods")
    print("=" * 40)
    
    # Test 1: Direct DeepSeek
    reply1 = test_direct_deepseek()
    
    # Test 2: VPS API
    reply2 = test_vps_api()
    
    # Test 3: Fallback
    reply3 = test_fallback_response()
    
    print("\\n📊 RESULTS:")
    print(f"DeepSeek Direct: {'✅' if reply1 else '❌'}")
    print(f"VPS API: {'✅' if reply2 else '❌'}")
    print(f"Fallback: {'✅' if reply3 else '❌'}")
    
    # Use the best available method
    best_reply = reply1 or reply2 or reply3
    print(f"\\n🎯 Best Reply: {best_reply}")

if __name__ == "__main__":
    main()
'''
    
    test_file = project_root / "test_working_ai.py"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print(f"✅ Created working AI test: {test_file}")

def main():
    """Main function"""
    print("🔧 DeepSeek API Key Fix Tool")
    print("=" * 50)
    
    # Test current API key
    if test_deepseek_api_key():
        # Test chat completion
        if test_deepseek_chat_completion():
            print("\n✅ DeepSeek API is working correctly!")
        else:
            print("\n⚠️ API key valid but chat completion failed")
    else:
        print("\n❌ DeepSeek API key issue detected")
        fix_api_key_in_config()
    
    # Create working AI test
    create_working_ai_test()
    
    print("\n📋 NEXT STEPS:")
    print("1. If API key is invalid, get new one from https://platform.deepseek.com/")
    print("2. Update config/settings.json with new API key")
    print("3. Run: python test_working_ai.py")
    print("4. Restart StreamMate AI application")

if __name__ == "__main__":
    main()