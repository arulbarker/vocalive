#!/usr/bin/env python3
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
