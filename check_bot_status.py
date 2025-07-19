#!/usr/bin/env python3
"""
Check Discord Bot Status
This script checks if the Discord bot is running properly and provides a status summary.
"""

import os
import sys
import time
import sqlite3
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_process_running():
    """Check if the bot process is running using platform-specific commands"""
    try:
        if sys.platform == "win32":
            # Windows
            output = subprocess.check_output(
                'tasklist /FI "IMAGENAME eq python.exe" /FO CSV', 
                shell=True
            ).decode()
            
            # Check if any python process has main.py in its command line
            if "python.exe" in output:
                # Check if it's our bot
                processes = subprocess.check_output(
                    'wmic process where name="python.exe" get commandline', 
                    shell=True
                ).decode()
                
                if "main.py" in processes:
                    return True, "Bot is running"
        else:
            # Unix-like
            try:
                output = subprocess.check_output(
                    "ps aux | grep '[p]ython main.py'", 
                    shell=True
                ).decode()
                if output.strip():
                    return True, "Bot is running"
            except subprocess.CalledProcessError:
                pass
        
        return False, "Bot is not running"
    except Exception as e:
        return False, f"Error checking process: {e}"

def check_log_file(log_path="logs/bot.log", minutes=5):
    """Check if the log file has been updated recently"""
    if not os.path.exists(log_path):
        return False, "Log file not found"
    
    file_time = os.path.getmtime(log_path)
    current_time = time.time()
    
    # Check if file was modified in the last X minutes
    if current_time - file_time < minutes * 60:
        # Get the last few lines of the log
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin1', 'cp1252']
            last_lines = []
            
            for encoding in encodings:
                try:
                    with open(log_path, 'r', encoding=encoding) as f:
                        # Read only the last 1000 bytes to avoid memory issues
                        f.seek(0, os.SEEK_END)
                        size = f.tell()
                        f.seek(max(0, size - 1000), os.SEEK_SET)
                        lines = f.readlines()
                        last_lines = lines[-10:] if len(lines) >= 10 else lines
                        break
                except UnicodeDecodeError:
                    continue
            
            if last_lines:
                return True, ''.join(last_lines)
            else:
                return False, "Could not decode log file with any encoding"
        except Exception as e:
            return False, f"Error reading log file: {e}"
    else:
        return False, f"Log file not updated in the last {minutes} minutes"

def check_database(db_path="data/member_joins.db"):
    """Check database status and get statistics"""
    if not os.path.exists(db_path):
        return False, "Database file not found"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total member joins
        cursor.execute("SELECT COUNT(*) FROM member_joins")
        total_joins = cursor.fetchone()[0]
        
        # Get recent joins (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d %H:%M:%S')
        
        # Check column name - could be timestamp or join_timestamp
        try:
            cursor.execute("SELECT COUNT(*) FROM member_joins WHERE join_timestamp > ?", (yesterday_str,))
            recent_joins = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            try:
                cursor.execute("SELECT COUNT(*) FROM member_joins WHERE timestamp > ?", (yesterday_str,))
                recent_joins = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                recent_joins = "Unknown (column name issue)"
        
        # Get notification stats if the table exists
        notification_stats = "N/A"
        try:
            cursor.execute("SELECT COUNT(*) FROM notifications_sent")
            notification_stats = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            # Try alternative table name
            try:
                cursor.execute("SELECT COUNT(*) FROM notifications")
                notification_stats = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                pass
        
        conn.close()
        return True, {
            "total_joins": total_joins,
            "recent_joins": recent_joins,
            "notifications": notification_stats
        }
    except Exception as e:
        return False, f"Error checking database: {e}"

def check_config(config_path="config.yaml"):
    """Check if the configuration file is valid"""
    if not os.path.exists(config_path):
        return False, "Configuration file not found"
    
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            
        # Check essential configuration
        if not config.get('discord', {}).get('token'):
            return False, "Discord bot token not configured"
        
        if not config.get('discord', {}).get('user_id'):
            return False, "Discord user ID not configured"
        
        return True, "Configuration is valid"
    except Exception as e:
        return False, f"Error checking configuration: {e}"

def check_backup_status(backup_dir="backups"):
    """Check backup status"""
    if not os.path.exists(backup_dir):
        return False, "Backup directory not found"
    
    try:
        backup_files = list(Path(backup_dir).glob("member_joins_backup_*.db"))
        
        if not backup_files:
            return False, "No backup files found"
        
        # Get most recent backup
        most_recent = max(backup_files, key=os.path.getmtime)
        most_recent_time = datetime.fromtimestamp(os.path.getmtime(most_recent))
        
        # Check if backup is recent (last 24 hours)
        if datetime.now() - most_recent_time < timedelta(days=1):
            return True, {
                "most_recent": str(most_recent.name),
                "timestamp": most_recent_time.strftime('%Y-%m-%d %H:%M:%S'),
                "total_backups": len(backup_files)
            }
        else:
            return False, f"Most recent backup is too old: {most_recent_time.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return False, f"Error checking backups: {e}"

def main():
    """Main function to check bot status"""
    logger.info("Checking Discord Bot Status...")
    
    # Check if bot process is running
    process_running, process_details = check_process_running()
    if process_running:
        logger.info(f"✅ Bot process is running")
    else:
        logger.error(f"❌ Bot process is not running: {process_details}")
    
    # Check log file
    log_status, log_details = check_log_file()
    if log_status:
        logger.info("✅ Log file is being updated")
        logger.info("Recent log entries:")
        for line in log_details.splitlines()[-5:]:
            logger.info(f"  {line.strip()}")
    else:
        logger.error(f"❌ Log file issue: {log_details}")
    
    # Check database
    db_status, db_details = check_database()
    if db_status:
        logger.info("✅ Database is accessible")
        logger.info(f"  - Total member joins: {db_details['total_joins']}")
        logger.info(f"  - Recent joins (24h): {db_details['recent_joins']}")
        logger.info(f"  - Notifications: {db_details['notifications']}")
    else:
        logger.error(f"❌ Database issue: {db_details}")
    
    # Check configuration
    config_status, config_details = check_config()
    if config_status:
        logger.info("✅ Configuration is valid")
    else:
        logger.error(f"❌ Configuration issue: {config_details}")
    
    # Check backup status
    backup_status, backup_details = check_backup_status()
    if backup_status:
        logger.info("✅ Backups are up to date")
        logger.info(f"  - Most recent: {backup_details['most_recent']}")
        logger.info(f"  - Timestamp: {backup_details['timestamp']}")
        logger.info(f"  - Total backups: {backup_details['total_backups']}")
    else:
        logger.error(f"❌ Backup issue: {backup_details}")
    
    # Overall status
    if process_running and log_status and db_status and config_status and backup_status:
        logger.info("\n✅ OVERALL STATUS: Bot is running properly")
    else:
        logger.error("\n❌ OVERALL STATUS: Bot has issues that need attention")

if __name__ == "__main__":
    main() 