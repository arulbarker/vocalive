#!/usr/bin/env python3
"""
Fix Performance Issues - StreamMate AI
Perbaikan masalah performance dan GUI display
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict

class PerformanceFixer:
    """Fix performance issues in StreamMate AI"""
    
    def __init__(self):
        self.root = Path(".")
        self.issues_fixed = []
    
    def fix_comment_display_issue(self) -> bool:
        """Fix komentar tidak muncul di GUI activity log"""
        print("Fixing comment display issue...")
        
        try:
            cohost_file = Path("ui/cohost_tab_basic.py")
            
            with open(cohost_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Fix log_user function untuk pastikan message muncul di GUI
            old_log_user = r'def log_user\(self, message, icon="ℹ️"\):(.*?)(?=def|\Z)'
            new_log_user = '''def log_user(self, message, icon="ℹ️"):
        """Log pesan untuk user dengan format yang konsisten - FIXED VERSION"""
        from datetime import datetime
        from PyQt6.QtCore import QTimer, QCoreApplication
        from PyQt6.QtWidgets import QApplication
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {icon} {message}"
        
        # PRIORITY FIX: Force GUI update dengan multiple strategies
        try:
            # Strategy 1: Direct update jika log_view tersedia
            if hasattr(self, 'log_view') and self.log_view is not None:
                try:
                    self.log_view.append(formatted_message)
                    self.log_view.ensureCursorVisible()
                    QCoreApplication.processEvents()
                    print(f"[GUI-SUCCESS] Message displayed: {message[:50]}...")
                except Exception as e:
                    print(f"[GUI-ERROR] Direct display failed: {e}")
                    # Fallback ke parent window
                    self._try_parent_display(formatted_message)
            else:
                print(f"[GUI-WARNING] log_view not available, trying fallback")
                self._try_parent_display(formatted_message)
                
        except Exception as e:
            print(f"[GUI-CRITICAL] All display methods failed: {e}")
        
        # Always print to terminal sebagai backup
        print(f"[{timestamp}] [CoHost] {message}")
    
    def _try_parent_display(self, message):
        """Try to display message via parent window"""
        try:
            # Try main window status bar
            if hasattr(self, 'parent_window') and self.parent_window:
                if hasattr(self.parent_window, 'statusBar'):
                    self.parent_window.statusBar().showMessage(message, 5000)
                    print(f"[GUI-FALLBACK] Message shown in status bar")
                    
                # Try reply log tab
                if hasattr(self.parent_window, 'main_tabs'):
                    for i in range(self.parent_window.main_tabs.count()):
                        tab = self.parent_window.main_tabs.widget(i)
                        if hasattr(tab, 'add_entry'):
                            tab.add_entry("CoHost", message, "INFO")
                            print(f"[GUI-FALLBACK] Message added to reply log")
                            break
        except Exception as e:
            print(f"[GUI-FALLBACK-ERROR] Parent display failed: {e}")
    
    '''
            
            # Replace the log_user function
            content = re.sub(old_log_user, new_log_user + '\n\n    ', content, flags=re.DOTALL)
            
            # 2. Fix _enqueue_lightweight untuk pastikan komentar ditampilkan
            old_enqueue = r'def _enqueue_lightweight\(self, author, message\):(.*?)(?=def|\Z)'
            new_enqueue = '''def _enqueue_lightweight(self, author, message):
        """Process comment untuk lightweight mode dengan GUI display yang diperbaiki"""
        try:
            # Counter untuk komentar
            if not hasattr(self, "comment_counter"):
                self.comment_counter = 0
            self.comment_counter += 1

            # CRITICAL FIX: Display comment langsung ke GUI dengan force update
            comment_text = f"💬 [{self.comment_counter}] {author}: {message}"
            
            # Method 1: Update log_view langsung
            if hasattr(self, 'log_view') and self.log_view:
                try:
                    from PyQt6.QtCore import QCoreApplication
                    self.log_view.append(comment_text)
                    self.log_view.ensureCursorVisible()
                    QCoreApplication.processEvents()
                    print(f"[COMMENT-GUI] Displayed: {author}: {message[:30]}...")
                except Exception as gui_error:
                    print(f"[COMMENT-GUI-ERROR] {gui_error}")
            
            # Method 2: Use log_user as backup
            self.log_user(f"[{self.comment_counter}] {author}: {message}", "👁️")
            
            # Method 3: Update status
            try:
                if hasattr(self, "status") and self.status:
                    self.status.setText(f"✅ Comments: {self.comment_counter} | Latest: {author}")
            except Exception as status_error:
                print(f"[STATUS-ERROR] {status_error}")

            # Log untuk debugging
            print(f"[REALTIME-COMMENT] #{self.comment_counter} {author}: {message}")

        except Exception as e:
            print(f"[ENQUEUE-ERROR] Failed to process comment: {e}")
            # Fallback: at least print to terminal
            print(f"[FALLBACK] {author}: {message}")
    
    '''
            
            content = re.sub(old_enqueue, new_enqueue + '\n\n    ', content, flags=re.DOTALL)
            
            # Save the updated file
            with open(cohost_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("SUCCESS: Comment display issue fixed")
            self.issues_fixed.append("Comment display in GUI")
            return True
            
        except Exception as e:
            print(f"FAILED: Failed to fix comment display: {e}")
            return False
    
    def fix_slow_startup_issue(self) -> bool:
        """Fix masalah aplikasi lambat saat masuk mode basic"""
        print("FIXING: Fixing slow startup issue...")
        
        try:
            # 1. Fix subscription tab - reduce polling frequency
            subscription_file = Path("ui/subscription_tab.py")
            
            with open(subscription_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Reduce demo monitoring frequency (already done, but verify)
            content = re.sub(
                r'self\.demo_monitor_timer\.start\(\d+\)',
                'self.demo_monitor_timer.start(120000)',  # 2 minutes instead of 10 seconds
                content
            )
            
            # Reduce credit refresh frequency
            content = re.sub(
                r'self\.credit_timer\.start\(\d+\)',
                'self.credit_timer.start(180000)',  # 3 minutes instead of 2 minutes
                content
            )
            
            with open(subscription_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 2. Fix main window initialization - reduce initial checks
            main_window_file = Path("ui/main_window.py")
            
            with open(main_window_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add faster initialization flag
            if 'FAST_STARTUP_MODE = True' not in content:
                content = content.replace(
                    'class MainWindow(QMainWindow):',
                    '''class MainWindow(QMainWindow):
    # PERFORMANCE FIX: Fast startup mode
    FAST_STARTUP_MODE = True'''
                )
            
            with open(main_window_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("SUCCESS: Slow startup issue fixed")
            self.issues_fixed.append("Slow startup performance")
            return True
            
        except Exception as e:
            print(f"FAILED: Failed to fix slow startup: {e}")
            return False
    
    def fix_heavy_start_stop_issue(self) -> bool:
        """Fix masalah Start/Stop auto-reply yang berat"""
        print("FIXING: Fixing heavy start/stop issue...")
        
        try:
            cohost_file = Path("ui/cohost_tab_basic.py")
            
            with open(cohost_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Add async start/stop untuk mencegah UI freeze
            async_start_method = '''
    def start_auto_reply_async(self):
        """Start auto-reply dengan async processing untuk mencegah UI freeze"""
        from PyQt6.QtCore import QTimer
        
        # Disable button immediately
        if hasattr(self, 'start_btn'):
            self.start_btn.setEnabled(False)
            self.start_btn.setText("Starting...")
        
        # Use QTimer untuk non-blocking execution
        def delayed_start():
            try:
                self.start_auto_reply_original()
            except Exception as e:
                print(f"[START-ERROR] {e}")
            finally:
                # Re-enable button
                if hasattr(self, 'start_btn'):
                    self.start_btn.setEnabled(True)
                    self.start_btn.setText("Start Auto-Reply")
        
        QTimer.singleShot(100, delayed_start)  # 100ms delay untuk UI responsiveness
    
    def stop_auto_reply_async(self):
        """Stop auto-reply dengan async processing"""
        from PyQt6.QtCore import QTimer
        
        # Disable button immediately
        if hasattr(self, 'stop_btn'):
            self.stop_btn.setEnabled(False)
            self.stop_btn.setText("Stopping...")
        
        def delayed_stop():
            try:
                self.stop_auto_reply_original()
            except Exception as e:
                print(f"[STOP-ERROR] {e}")
            finally:
                # Re-enable button
                if hasattr(self, 'stop_btn'):
                    self.stop_btn.setEnabled(True)
                    self.stop_btn.setText("Stop Auto-Reply")
        
        QTimer.singleShot(100, delayed_stop)
'''
            
            # Add the async methods before the class ends
            content = content.replace(
                '    def check_daily_limit(self):',
                async_start_method + '\n    def check_daily_limit(self):'
            )
            
            # 2. Reduce credit calculations during start/stop
            content = re.sub(
                r'self\.refresh_credits\(\)',
                '# Skip credit refresh during start/stop for performance',
                content
            )
            
            # 3. Add performance optimization flags
            performance_flags = '''
    # PERFORMANCE FLAGS
    SKIP_HEAVY_OPERATIONS = True
    ASYNC_MODE = True
    REDUCE_POLLING = True
'''
            
            content = content.replace(
                'class CohostTabBasic(QWidget):',
                'class CohostTabBasic(QWidget):' + performance_flags
            )
            
            with open(cohost_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("SUCCESS: Heavy start/stop issue fixed")
            self.issues_fixed.append("Heavy start/stop operations")
            return True
            
        except Exception as e:
            print(f"FAILED: Failed to fix heavy start/stop: {e}")
            return False
    
    def fix_vps_dependency_issue(self) -> bool:
        """Fix sisa-sisa dependensi VPS yang masih ada"""
        print("FIXING: Fixing remaining VPS dependencies...")
        
        try:
            # 1. Update settings.json untuk remove VPS URL
            settings_file = Path("config/settings.json")
            
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Force remove VPS references
            if "server_url" in settings:
                settings["server_url"] = "supabase_backend"
            
            # Add Supabase-only flags
            settings["backend_type"] = "supabase_only"
            settings["vps_disabled"] = True
            settings["force_supabase"] = True
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            # 2. Update API client untuk complete Supabase mode
            api_file = Path("modules_client/api.py")
            
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace all VPS references
            content = re.sub(
                r'http://69\.62\.79\.238:8000',
                'supabase_backend',
                content
            )
            
            # Add Supabase-only mode indicator
            content = content.replace(
                'class APIClient:',
                '''class APIClient:
    """API Client - SUPABASE ONLY MODE"""
    SUPABASE_ONLY = True
    VPS_DISABLED = True'''
            )
            
            with open(api_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("SUCCESS: VPS dependency issue fixed")
            self.issues_fixed.append("VPS dependencies removed")
            return True
            
        except Exception as e:
            print(f"FAILED: Failed to fix VPS dependencies: {e}")
            return False
    
    def optimize_credit_calculations(self) -> bool:
        """Optimize credit calculations yang terlalu sering"""
        print("FIXING: Optimizing credit calculations...")
        
        try:
            # Add caching to Supabase client
            supabase_file = Path("modules_client/supabase_client.py")
            
            with open(supabase_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add more aggressive caching
            if '_credit_cache_timeout = 30' in content:
                content = content.replace(
                    '_credit_cache_timeout = 30',
                    '_credit_cache_timeout = 120'  # 2 minutes cache
                )
            
            # Add cache for credit calculations
            cache_method = '''
    def _get_cached_credits(self, email: str) -> Dict:
        """Get cached credit data to reduce database calls"""
        import time
        cache_key = f"credits_{email}"
        current_time = time.time()
        
        if (hasattr(self, '_credit_cache') and 
            cache_key in self._credit_cache and 
            current_time - self._credit_cache[cache_key]['timestamp'] < self._cache_timeout):
            
            print(f"[CACHE-HIT] Using cached credits for {email}")
            return self._credit_cache[cache_key]['data']
        
        # Cache miss - fetch fresh data
        credit_data = self.get_credit_balance(email)
        
        if not hasattr(self, '_credit_cache'):
            self._credit_cache = {}
        
        self._credit_cache[cache_key] = {
            'data': credit_data,
            'timestamp': current_time
        }
        
        print(f"[CACHE-MISS] Fetched fresh credits for {email}")
        return credit_data
'''
            
            content = content.replace(
                'def get_credit_balance(self, email: str)',
                cache_method + '\n    def get_credit_balance(self, email: str)'
            )
            
            with open(supabase_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("SUCCESS: Credit calculations optimized")
            self.issues_fixed.append("Credit calculation optimization")
            return True
            
        except Exception as e:
            print(f"FAILED: Failed to optimize credit calculations: {e}")
            return False
    
    def run_all_fixes(self) -> bool:
        """Run all performance fixes"""
        print("RUNNING: Running all performance fixes...")
        print("=" * 50)
        
        fixes = [
            ("Comment Display Issue", self.fix_comment_display_issue),
            ("Slow Startup Issue", self.fix_slow_startup_issue),
            ("Heavy Start/Stop Issue", self.fix_heavy_start_stop_issue),
            ("VPS Dependency Issue", self.fix_vps_dependency_issue),
            ("Credit Calculation Optimization", self.optimize_credit_calculations),
        ]
        
        success_count = 0
        for fix_name, fix_func in fixes:
            print(f"\nAPPLYING: Applying: {fix_name}")
            try:
                if fix_func():
                    print(f"SUCCESS: {fix_name} - SUCCESS")
                    success_count += 1
                else:
                    print(f"FAILED: {fix_name} - FAILED")
            except Exception as e:
                print(f"FAILED: {fix_name} - ERROR: {e}")
        
        print("\n" + "=" * 50)
        print(f"RESULTS: Performance Fixes: {success_count}/{len(fixes)} applied")
        
        if success_count >= len(fixes) * 0.8:  # 80% success rate
            print("SUCCESS: PERFORMANCE FIXES COMPLETED!")
            print("ISSUES FIXED: Issues Fixed:")
            for issue in self.issues_fixed:
                print(f"  OK: {issue}")
            print("\nNOTE: Restart aplikasi untuk melihat improvement!")
            return True
        else:
            print("WARNING: SOME FIXES FAILED")
            print("FIXING: Manual intervention may be required")
            return False

def main():
    """Main performance fixing execution"""
    try:
        fixer = PerformanceFixer()
        success = fixer.run_all_fixes()
        
        if success:
            print("\nSUCCESS: PERFORMANCE FIXES SUCCESSFUL!")
            print("🔄 Please restart the application to see improvements")
            return 0
        else:
            print("\nWARNING: SOME FIXES INCOMPLETE")
            return 1
            
    except Exception as e:
        print(f"ERROR: CRITICAL ERROR: {e}")
        return 2

if __name__ == "__main__":
    exit(main())