# modules_client/subscription_checker.py
"""
Subscription checker module untuk tracking penggunaan harian
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger('StreamMate')

def get_config_path():
    """Get path to config directory"""
    return Path("config")

def get_usage_file_path():
    """Get path to daily usage file"""
    config_dir = get_config_path()
    config_dir.mkdir(exist_ok=True)
    return config_dir / "daily_usage.json"

def get_subscription_file_path():
    """Get path to subscription status file"""
    config_dir = get_config_path()
    return config_dir / "subscription_status.json"

def get_today_usage():
    """
    Get today's usage information
    Returns: (tier, used_hours, limit_hours)
    """
    try:
        # Get subscription info
        subscription_file = get_subscription_file_path()
        tier = "basic"
        limit_hours = 24.0  # Default limit
        
        if subscription_file.exists():
            try:
                with open(subscription_file, 'r', encoding='utf-8') as f:
                    sub_data = json.load(f)
                    tier = sub_data.get("tier", "basic")
                    if tier == "pro":
                        limit_hours = 120.0  # Pro limit: 120 hours per day
                    elif tier == "basic":
                        limit_hours = 24.0   # Basic limit: 24 hours per day
                    else:
                        limit_hours = 24.0   # Default
            except Exception as e:
                logger.error(f"Error reading subscription file: {e}")
        
        # Get usage info
        usage_file = get_usage_file_path()
        used_hours = 0.0
        
        if usage_file.exists():
            try:
                with open(usage_file, 'r', encoding='utf-8') as f:
                    usage_data = json.load(f)
                    
                today = datetime.now().strftime("%Y-%m-%d")
                daily_usage = usage_data.get(today, {})
                used_hours = float(daily_usage.get("total_hours", 0.0))
                
            except Exception as e:
                logger.error(f"Error reading usage file: {e}")
        
        return tier, used_hours, limit_hours
        
    except Exception as e:
        logger.error(f"Error in get_today_usage: {e}")
        return "basic", 0.0, 24.0

def add_usage(hours_used):
    """
    Add usage hours to today's total
    Args:
        hours_used (float): Hours to add to usage
    """
    try:
        usage_file = get_usage_file_path()
        usage_data = {}
        
        # Load existing data
        if usage_file.exists():
            try:
                with open(usage_file, 'r', encoding='utf-8') as f:
                    usage_data = json.load(f)
            except Exception as e:
                logger.error(f"Error reading existing usage data: {e}")
                usage_data = {}
        
        # Update today's usage
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in usage_data:
            usage_data[today] = {
                "total_hours": 0.0,
                "sessions": []
            }
        
        # Add to total
        usage_data[today]["total_hours"] = float(usage_data[today]["total_hours"]) + float(hours_used)
        
        # Add session record
        session_record = {
            "timestamp": datetime.now().isoformat(),
            "hours": float(hours_used),
            "type": "cohost_pro"
        }
        usage_data[today]["sessions"].append(session_record)
        
        # Clean old data (keep only last 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        keys_to_remove = [key for key in usage_data.keys() if key < cutoff_str]
        for key in keys_to_remove:
            del usage_data[key]
        
        # Save updated data
        with open(usage_file, 'w', encoding='utf-8') as f:
            json.dump(usage_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Added {hours_used} hours to daily usage. Total today: {usage_data[today]['total_hours']}")
        
    except Exception as e:
        logger.error(f"Error in add_usage: {e}")

def time_until_next_day():
    """
    Get seconds until next day (midnight)
    Returns: int (seconds)
    """
    try:
        now = datetime.now()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        delta = tomorrow - now
        return int(delta.total_seconds())
    except Exception as e:
        logger.error(f"Error in time_until_next_day: {e}")
        return 86400  # 24 hours as fallback

def reset_daily_usage():
    """Reset daily usage (called at midnight)"""
    try:
        usage_file = get_usage_file_path()
        if usage_file.exists():
            with open(usage_file, 'r', encoding='utf-8') as f:
                usage_data = json.load(f)
        else:
            usage_data = {}
        
        today = datetime.now().strftime("%Y-%m-%d")
        usage_data[today] = {
            "total_hours": 0.0,
            "sessions": []
        }
        
        with open(usage_file, 'w', encoding='utf-8') as f:
            json.dump(usage_data, f, indent=2, ensure_ascii=False)
            
        logger.info("Daily usage reset successfully")
        
    except Exception as e:
        logger.error(f"Error resetting daily usage: {e}")

def get_usage_stats(days=7):
    """
    Get usage statistics for the last N days
    Args:
        days (int): Number of days to get stats for
    Returns:
        dict: Usage statistics
    """
    try:
        usage_file = get_usage_file_path()
        if not usage_file.exists():
            return {}
        
        with open(usage_file, 'r', encoding='utf-8') as f:
            usage_data = json.load(f)
        
        stats = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if date in usage_data:
                stats[date] = usage_data[date]
            else:
                stats[date] = {"total_hours": 0.0, "sessions": []}
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        return {}