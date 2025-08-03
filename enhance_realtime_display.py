#!/usr/bin/env python3
"""
🔧 Enhanced Real-time Comment Display Fix
Perbaikan tambahan untuk memastikan komentar muncul di activity log
"""

import os
import sys
import shutil
from pathlib import Path

def enhance_comment_display():
    """Enhance the comment display system"""
    print("🔧 Enhancing comment display system...")
    
    project_root = Path(__file__).parent
    cohost_file = project_root / "ui" / "cohost_tab_basic.py"
    
    if not cohost_file.exists():
        print("❌ cohost_tab_basic.py not found!")
        return False
    
    # Read current content
    with open(cohost_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Enhancement 1: Force immediate UI update in _enqueue_lightweight
    old_enqueue = '''        try:
            # ✅ PERBAIKAN UTAMA: Log komentar yang masuk untuk user visibility
            self.log_user(f"📨 Incoming comment from {author}: {message}", "👁️")'''
    
    new_enqueue = '''        try:
            # ✅ ENHANCED: Force immediate comment display
            if not hasattr(self, 'comment_counter'):
                self.comment_counter = 0
            self.comment_counter += 1
            
            # Display comment immediately in UI
            self.log_user(f"💬 [{self.comment_counter}] {author}: {message}", "👁️")
            
            # Force UI refresh
            try:
                if hasattr(self, 'log_view') and self.log_view:
                    from PyQt6.QtCore import QCoreApplication
                    QCoreApplication.processEvents()
            except Exception as e:
                self.log_debug(f"UI refresh error: {e}")'''
    
    # Enhancement 2: Add real-time status updates
    status_update = '''            # ✅ ENHANCED: Update status with comment count
            try:
                if hasattr(self, 'status') and self.status:
                    self.status.setText(f"✅ Real-time Active | Comments: {self.comment_counter}")
            except Exception as e:
                self.log_debug(f"Status update error: {e}")'''
    
    # Apply enhancements
    fixes_applied = 0
    
    if old_enqueue in content:
        content = content.replace(old_enqueue, new_enqueue + status_update)
        fixes_applied += 1
        print("✅ Enhancement 1: Added immediate UI update and comment counter")
    
    # Enhancement 3: Improve log_user method with thread safety
    old_log_user_method = '''    def log_user(self, message, icon="ℹ️"):
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
    
    new_log_user_method = '''    def log_user(self, message, icon="ℹ️"):
        """Log pesan untuk user dengan format yang konsisten - SUPER ENHANCED UI DISPLAY"""
        from datetime import datetime
        from PyQt6.QtCore import QTimer, QCoreApplication
        from PyQt6.QtWidgets import QApplication
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {icon} {message}"
        
        # ✅ SUPER ENHANCED: Multiple UI update strategies
        try:
            if hasattr(self, 'log_view') and self.log_view is not None:
                # Strategy 1: Direct update if in main thread
                if QApplication.instance() and QApplication.instance().thread() == self.thread():
                    try:
                        self.log_view.append(formatted_message)
                        self.log_view.ensureCursorVisible()
                        self.log_view.repaint()
                        QCoreApplication.processEvents()
                    except Exception as e:
                        print(f"Direct UI update error: {e}")
                else:
                    # Strategy 2: Use QTimer for thread safety
                    def safe_update_ui():
                        try:
                            if hasattr(self, 'log_view') and self.log_view:
                                self.log_view.append(formatted_message)
                                self.log_view.ensureCursorVisible()
                                self.log_view.repaint()
                                QCoreApplication.processEvents()
                        except Exception as e:
                            print(f"Timer UI update error: {e}")
                    
                    QTimer.singleShot(0, safe_update_ui)
                
                # Strategy 3: Force immediate processing
                QCoreApplication.processEvents()
                
            else:
                print(f"[WARNING] log_view not available: {formatted_message}")
        except Exception as e:
            print(f"[ERROR] Failed to update UI: {e}")
        
        # Always print to terminal for debugging
        print(f"[{timestamp}] [CoHost] {message}")'''
    
    if old_log_user_method in content:
        content = content.replace(old_log_user_method, new_log_user_method)
        fixes_applied += 1
        print("✅ Enhancement 2: Super enhanced log_user method with multiple UI update strategies")
    
    # Enhancement 4: Add periodic UI refresh
    refresh_method = '''
    def _start_ui_refresh_timer(self):
        """Start periodic UI refresh timer"""
        try:
            from PyQt6.QtCore import QTimer
            if not hasattr(self, 'ui_refresh_timer'):
                self.ui_refresh_timer = QTimer()
                self.ui_refresh_timer.timeout.connect(self._refresh_ui)
                self.ui_refresh_timer.start(1000)  # Refresh every second
                self.log_debug("UI refresh timer started")
        except Exception as e:
            self.log_debug(f"Failed to start UI refresh timer: {e}")
    
    def _refresh_ui(self):
        """Periodic UI refresh"""
        try:
            from PyQt6.QtCore import QCoreApplication
            if hasattr(self, 'log_view') and self.log_view:
                QCoreApplication.processEvents()
        except Exception as e:
            pass  # Silent fail for periodic refresh
'''
    
    # Add refresh method if not exists
    if '_start_ui_refresh_timer' not in content:
        # Find a good place to insert the method (after log_error method)
        insertion_point = 'def init_ui(self):'
        if insertion_point in content:
            content = content.replace(insertion_point, refresh_method + '\n    ' + insertion_point)
            fixes_applied += 1
            print("✅ Enhancement 3: Added periodic UI refresh timer")
    
    # Enhancement 5: Start UI refresh timer when listener starts
    old_listener_start = '''        self.log_user("🤖 Real-time comment viewer active! All comments will be displayed.", "✅")
        self.log_user("🎯 Auto-Reply will respond only to trigger words.", "🎯")
        self.log_user("📊 Comment counter initialized. Waiting for comments...", "📈")
        self.status.setText("✅ Real-time Comments Active")
        self.log_system("Real-time comment viewer ready with AI auto-reply for triggers.")'''
    
    new_listener_start = '''        self.log_user("🤖 Real-time comment viewer active! All comments will be displayed.", "✅")
        self.log_user("🎯 Auto-Reply will respond only to trigger words.", "🎯")
        self.log_user("📊 Comment counter initialized. Waiting for comments...", "📈")
        
        # ✅ ENHANCED: Start UI refresh timer
        self._start_ui_refresh_timer()
        
        self.status.setText("✅ Real-time Comments Active")
        self.log_system("Real-time comment viewer ready with AI auto-reply for triggers.")'''
    
    if old_listener_start in content:
        content = content.replace(old_listener_start, new_listener_start)
        fixes_applied += 1
        print("✅ Enhancement 4: Added UI refresh timer startup")
    
    # Write the enhanced content
    with open(cohost_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Applied {fixes_applied} enhancements to cohost_tab_basic.py")
    return fixes_applied > 0

def create_realtime_monitor():
    """Create a real-time monitor script"""
    monitor_script = '''#!/usr/bin/env python3
"""
📊 Real-time Comment Monitor
Monitor komentar yang masuk secara real-time
"""

import time
import sys
from pathlib import Path
from datetime import datetime

def monitor_comments():
    """Monitor comments in real-time"""
    print("📊 Starting Real-time Comment Monitor...")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    # Monitor log files
    log_files = [
        Path("logs/activity.log"),
        Path("logs/cohost_log.txt"),
        Path("temp/error_log.txt")
    ]
    
    # Track file positions
    file_positions = {}
    for log_file in log_files:
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                f.seek(0, 2)  # Go to end
                file_positions[log_file] = f.tell()
        else:
            file_positions[log_file] = 0
    
    try:
        while True:
            for log_file in log_files:
                if log_file.exists():
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(file_positions[log_file])
                            new_lines = f.readlines()
                            if new_lines:
                                print(f"\\n📄 {log_file.name}:")
                                for line in new_lines:
                                    line = line.strip()
                                    if line:
                                        timestamp = datetime.now().strftime("%H:%M:%S")
                                        print(f"[{timestamp}] {line}")
                                file_positions[log_file] = f.tell()
                    except Exception as e:
                        print(f"Error reading {log_file}: {e}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\\n\\n📊 Monitor stopped by user")

if __name__ == "__main__":
    monitor_comments()
'''
    
    monitor_file = Path(__file__).parent / "realtime_comment_monitor.py"
    with open(monitor_file, 'w', encoding='utf-8') as f:
        f.write(monitor_script)
    
    print(f"✅ Real-time monitor created: {monitor_file}")
    return monitor_file

def main():
    """Main function to enhance real-time display"""
    print("🚀 Starting Enhanced Real-time Comment Display Fix...")
    print("=" * 60)
    
    # Apply enhancements
    if enhance_comment_display():
        print("\\n✅ Real-time display enhancements applied successfully!")
    else:
        print("\\n❌ Failed to apply enhancements")
        return False
    
    # Create monitor script
    monitor_file = create_realtime_monitor()
    
    print("\\n📋 ENHANCED FEATURES:")
    print("- Immediate UI updates with multiple strategies")
    print("- Comment counter with real-time status")
    print("- Periodic UI refresh timer")
    print("- Thread-safe UI operations")
    print("- Force UI processing events")
    
    print("\\n📋 NEXT STEPS:")
    print("1. Restart StreamMate AI application")
    print("2. Go to Cohost Basic tab")
    print("3. Start auto-reply")
    print("4. Comments should now appear immediately")
    print(f"5. Run monitor: python {monitor_file.name}")
    
    print("\\n🔍 WHAT TO EXPECT:")
    print("- Comments appear as: [time] 👁️ 💬 [#] username: message")
    print("- Status shows: ✅ Real-time Active | Comments: X")
    print("- UI refreshes automatically every second")
    print("- Immediate visual feedback for all comments")
    
    print("\\n✅ Enhanced real-time display fix completed!")
    return True

if __name__ == "__main__":
    main()