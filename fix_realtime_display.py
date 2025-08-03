#!/usr/bin/env python3
"""
🔧 Fix Real-time Comment Display Issue
Memperbaiki masalah komentar tidak muncul di activity log secara real-time
"""

import os
import sys
import shutil
from pathlib import Path

def fix_comment_display():
    """Fix the real-time comment display in activity log"""
    print("🔧 Fixing real-time comment display...")
    
    project_root = Path(__file__).parent
    cohost_file = project_root / "ui" / "cohost_tab_basic.py"
    
    if not cohost_file.exists():
        print("❌ cohost_tab_basic.py not found!")
        return False
    
    # Backup original file
    backup_file = cohost_file.with_suffix('.py.backup_display')
    if not backup_file.exists():
        shutil.copy2(cohost_file, backup_file)
        print(f"✅ Backup created: {backup_file}")
    
    # Read current content
    with open(cohost_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Ensure all comments are displayed in log_view
    old_enqueue_lightweight = '''    def _enqueue_lightweight(self, author, message):
        """Process comment untuk lightweight mode dengan validasi minimal."""
        try:
            # ✅ PERBAIKAN UTAMA: Log komentar yang masuk untuk user visibility
            self.log_user(f"📨 Incoming comment from {author}: {message}", "👁️")'''
    
    new_enqueue_lightweight = '''    def _enqueue_lightweight(self, author, message):
        """Process comment untuk lightweight mode dengan validasi minimal."""
        try:
            # ✅ PERBAIKAN UTAMA: ALWAYS display incoming comments in real-time
            self.log_user(f"💬 {author}: {message}", "👁️")
            
            # ✅ ENHANCED: Also log to activity log for system monitoring
            try:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                activity_log = Path("logs/activity.log")
                activity_log.parent.mkdir(exist_ok=True)
                with open(activity_log, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] [INFO] [CoHost] Real-time comment: {author}: {message}\\n")
            except Exception as e:
                self.log_debug(f"Failed to log to activity.log: {e}")'''
    
    # Fix 2: Ensure log_user method works properly
    old_log_user = '''    def log_user(self, message, icon="ℹ️"):
        """Log pesan untuk user dengan format yang konsisten - PERBAIKAN UI DISPLAY"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {icon} {message}"
        
        # ✅ PERBAIKAN UTAMA: Tampilkan di UI log_view 
        if safe_attr_check(self, 'log_view'):
            self.log_view.append(formatted_message)
            # Auto-scroll ke bawah jika ada log baru
            self.log_view.ensureCursorVisible()
        
        # Juga print ke terminal untuk debugging
        print(f"[{timestamp}] [CoHost] {message}")'''
    
    new_log_user = '''    def log_user(self, message, icon="ℹ️"):
        """Log pesan untuk user dengan format yang konsisten - ENHANCED UI DISPLAY"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {icon} {message}"
        
        # ✅ ENHANCED: Force UI update in main thread
        try:
            if hasattr(self, 'log_view') and self.log_view is not None:
                # Use QTimer to ensure UI update happens in main thread
                from PyQt6.QtCore import QTimer
                def update_ui():
                    try:
                        self.log_view.append(formatted_message)
                        self.log_view.ensureCursorVisible()
                        # Force immediate repaint
                        self.log_view.repaint()
                    except Exception as e:
                        print(f"Error updating UI: {e}")
                
                # Schedule UI update
                QTimer.singleShot(0, update_ui)
            else:
                print(f"[WARNING] log_view not available: {formatted_message}")
        except Exception as e:
            print(f"[ERROR] Failed to update UI: {e}")
        
        # Always print to terminal for debugging
        print(f"[{timestamp}] [CoHost] {message}")'''
    
    # Fix 3: Add real-time comment counter
    old_start_listener = '''        self.log_user("🤖 Real-time comment viewer active! All comments will be displayed.", "✅")
        self.log_user("🎯 Auto-Reply will respond only to trigger words.", "🎯")
        self.status.setText("✅ Real-time Comments Active")
        self.log_system("Real-time comment viewer ready with AI auto-reply for triggers.")'''
    
    new_start_listener = '''        # ✅ ENHANCED: Initialize comment counter
        if not hasattr(self, 'comment_counter'):
            self.comment_counter = 0
        
        self.log_user("🤖 Real-time comment viewer active! All comments will be displayed.", "✅")
        self.log_user("🎯 Auto-Reply will respond only to trigger words.", "🎯")
        self.log_user("📊 Comment counter initialized. Waiting for comments...", "📈")
        self.status.setText("✅ Real-time Comments Active")
        self.log_system("Real-time comment viewer ready with AI auto-reply for triggers.")'''
    
    # Apply fixes
    fixes_applied = 0
    
    if old_enqueue_lightweight in content:
        content = content.replace(old_enqueue_lightweight, new_enqueue_lightweight)
        fixes_applied += 1
        print("✅ Fix 1: Enhanced comment display in _enqueue_lightweight")
    
    if old_log_user in content:
        content = content.replace(old_log_user, new_log_user)
        fixes_applied += 1
        print("✅ Fix 2: Enhanced log_user method for better UI updates")
    
    if old_start_listener in content:
        content = content.replace(old_start_listener, new_start_listener)
        fixes_applied += 1
        print("✅ Fix 3: Added comment counter initialization")
    
    # Add comment counter to _enqueue_lightweight
    if 'self.comment_counter += 1' not in content:
        # Find the right place to add counter
        counter_insertion = '''            # ✅ PERBAIKAN UTAMA: ALWAYS display incoming comments in real-time
            self.log_user(f"💬 {author}: {message}", "👁️")'''
        
        counter_replacement = '''            # ✅ PERBAIKAN UTAMA: ALWAYS display incoming comments in real-time
            if not hasattr(self, 'comment_counter'):
                self.comment_counter = 0
            self.comment_counter += 1
            self.log_user(f"💬 [{self.comment_counter}] {author}: {message}", "👁️")'''
        
        if counter_insertion in content:
            content = content.replace(counter_insertion, counter_replacement)
            fixes_applied += 1
            print("✅ Fix 4: Added comment counter to display")
    
    # Write the fixed content
    with open(cohost_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Applied {fixes_applied} fixes to cohost_tab_basic.py")
    return fixes_applied > 0

def create_test_script():
    """Create a test script to verify real-time display"""
    test_script = '''#!/usr/bin/env python3
"""
🧪 Test Real-time Comment Display
Verifikasi bahwa komentar muncul di activity log secara real-time
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_comment_display():
    """Test if comments are displayed properly"""
    print("🧪 Testing real-time comment display...")
    
    try:
        # Import the fixed cohost module
        from ui.cohost_tab_basic import CohostTabBasic
        from PyQt6.QtWidgets import QApplication
        
        # Create minimal Qt application
        app = QApplication([])
        
        # Create cohost instance
        cohost = CohostTabBasic()
        
        # Test log_user method
        print("📝 Testing log_user method...")
        cohost.log_user("Test message 1", "🧪")
        cohost.log_user("Test message 2", "✅")
        
        # Test _enqueue_lightweight method
        print("📝 Testing _enqueue_lightweight method...")
        cohost._enqueue_lightweight("TestUser1", "Hello world!")
        cohost._enqueue_lightweight("TestUser2", "This is a test comment")
        
        print("✅ Comment display test completed!")
        print("📊 Check the UI log view for displayed comments")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_comment_display()
'''
    
    test_file = Path(__file__).parent / "test_realtime_display.py"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print(f"✅ Test script created: {test_file}")
    return test_file

def main():
    """Main function to fix real-time display issues"""
    print("🚀 Starting Real-time Comment Display Fix...")
    print("=" * 50)
    
    # Apply fixes
    if fix_comment_display():
        print("\n✅ Real-time display fixes applied successfully!")
    else:
        print("\n❌ Failed to apply fixes")
        return False
    
    # Create test script
    test_file = create_test_script()
    
    print("\n📋 NEXT STEPS:")
    print("1. Restart StreamMate AI application")
    print("2. Go to Cohost Basic tab")
    print("3. Start auto-reply")
    print("4. Check if comments appear in Activity Log")
    print(f"5. Run test script: python {test_file.name}")
    
    print("\n🔍 WHAT TO LOOK FOR:")
    print("- Comments should appear as: [timestamp] 👁️ 💬 [counter] username: message")
    print("- Activity log should update in real-time")
    print("- Comment counter should increment")
    print("- UI should auto-scroll to show new comments")
    
    print("\n✅ Real-time display fix completed!")
    return True

if __name__ == "__main__":
    main()