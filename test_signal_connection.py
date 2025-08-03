#!/usr/bin/env python3
"""
Test script to verify signal connection fixes
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_signal_fixes():
    """Test if signal connection fixes were applied correctly"""
    print("Testing signal connection fixes...")
    
    # Read the cohost file
    with open("ui/cohost_tab_basic.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if fixes are in place
    fixes = []
    
    # 1. Check if enhanced signal debugging was added
    if "[HANDLE_REPLY_IMMEDIATE] ✅ SIGNAL RECEIVED!" in content:
        fixes.append("PASS: Enhanced signal debugging added")
    else:
        fixes.append("FAIL: Enhanced signal debugging NOT added")
    
    # 2. Check if DirectConnection was implemented
    if "Qt.ConnectionType.DirectConnection" in content:
        fixes.append("PASS: DirectConnection implemented")
    else:
        fixes.append("FAIL: DirectConnection NOT implemented")
    
    # 3. Check if thread startup debugging was added
    if "[THREAD_SETUP] Starting reply thread for" in content:
        fixes.append("PASS: Thread startup debugging added")
    else:
        fixes.append("FAIL: Thread startup debugging NOT added")
    
    # 4. Check if signal emission debugging was enhanced
    if "[REPLY_THREAD] About to emit finished signal..." in content:
        fixes.append("PASS: Signal emission debugging enhanced")
    else:
        fixes.append("FAIL: Signal emission debugging NOT enhanced")
    
    # 5. Check if signal connection logging was added
    if "[THREAD_SETUP] Connecting signal for" in content:
        fixes.append("PASS: Signal connection logging added")
    else:
        fixes.append("FAIL: Signal connection logging NOT added")
    
    print("\nSignal Connection Fix Validation Results:")
    for fix in fixes:
        print(f"  {fix}")
    
    # Overall assessment
    passed_fixes = len([f for f in fixes if f.startswith("PASS")])
    total_fixes = len(fixes)
    
    print(f"\nOverall: {passed_fixes}/{total_fixes} signal fixes applied")
    
    if passed_fixes == total_fixes:
        print("ALL SIGNAL CONNECTION FIXES SUCCESSFULLY APPLIED!")
        print("\nWhat to expect when testing:")
        print("  - [THREAD_SETUP] logs when creating reply thread")
        print("  - [REPLY_THREAD] logs when emitting signal")
        print("  - [HANDLE_REPLY_IMMEDIATE] logs when signal received")
        print("  - AI replies appearing in GUI")
        print("  - TTS processing working correctly")
        return True
    else:
        print("Some signal fixes may not have been applied correctly")
        return False

if __name__ == "__main__":
    test_signal_fixes()