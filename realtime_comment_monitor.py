#!/usr/bin/env python3
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
                                print(f"\n📄 {log_file.name}:")
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
        print("\n\n📊 Monitor stopped by user")

if __name__ == "__main__":
    monitor_comments()
