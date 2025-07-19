#!/usr/bin/env python3
"""
Discord Bot Validation Script
Simple script to validate bot configuration and basic functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def validate_bot():
    """Validate bot configuration and dependencies"""
    print("🤖 Discord Bot Validation")
    print("=" * 40)

    errors = []
    warnings = []

    # Check if config file exists
    config_path = Path("config.yaml")
    if not config_path.exists():
        errors.append("❌ config.yaml not found")
    else:
        print("✅ config.yaml found")

    # Check if database directory exists
    data_dir = Path("data")
    if not data_dir.exists():
        warnings.append("⚠️ data directory doesn't exist (will be created)")
    else:
        print("✅ data directory exists")

    # Check if logs directory exists
    logs_dir = Path("logs")
    if not logs_dir.exists():
        warnings.append("⚠️ logs directory doesn't exist (will be created)")
    else:
        print("✅ logs directory exists")

    # Test configuration loading
    try:
        from src.config_manager import ConfigManager
        config = ConfigManager()
        print("✅ Configuration loaded successfully")

        # Check if tokens are configured
        try:
            bot_token = config.get_discord_token()
            if bot_token and len(bot_token) > 20:
                print("✅ Bot token configured")
            else:
                errors.append("❌ Bot token not properly configured")
        except:
            errors.append("❌ Failed to get bot token")

        try:
            user_token = config.get_user_token()
            if user_token and len(user_token) > 20:
                print("✅ User token configured")
            else:
                warnings.append("⚠️ User token not configured (user monitoring disabled)")
        except:
            warnings.append("⚠️ Failed to get user token")

    except Exception as e:
        errors.append(f"❌ Configuration error: {e}")

    # Test database manager
    try:
        from src.database_manager import DatabaseManager
        db = DatabaseManager()
        await db.initialize()
        print("✅ Database manager initialized")

        # Test database stats
        stats = await db.get_database_stats()
        print(f"📊 Database stats: {stats}")

    except Exception as e:
        errors.append(f"❌ Database error: {e}")

    # Test other components
    try:
        from src.notification_manager import NotificationManager
        print("✅ Notification manager imports successfully")
    except Exception as e:
        errors.append(f"❌ Notification manager error: {e}")

    try:
        from src.server_manager import ServerManager
        print("✅ Server manager imports successfully")
    except Exception as e:
        errors.append(f"❌ Server manager error: {e}")

    try:
        from src.user_formatter import UserFormatter
        print("✅ User formatter imports successfully")
    except Exception as e:
        errors.append(f"❌ User formatter error: {e}")

    # Check for required Python packages
    required_packages = [
        'discord',
        'aiohttp',
        'aiosqlite',
        'yaml'
    ]

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} package available")
        except ImportError:
            errors.append(f"❌ {package} package not installed")

    # SSL patch check
    try:
        import ssl_patch
        print("✅ SSL patch available")
    except ImportError:
        warnings.append("⚠️ SSL patch not available")

    # Summary
    print("\n" + "=" * 40)
    print("📋 Validation Summary:")

    if errors:
        print(f"\n❌ {len(errors)} Error(s):")
        for error in errors:
            print(f"   {error}")

    if warnings:
        print(f"\n⚠️ {len(warnings)} Warning(s):")
        for warning in warnings:
            print(f"   {warning}")

    if not errors and not warnings:
        print("🎉 All validations passed! Bot should work correctly.")
        return True
    elif not errors:
        print("✅ No critical errors found. Bot should work with minor issues.")
        return True
    else:
        print("❌ Critical errors found. Please fix before running bot.")
        return False

def check_recent_activity():
    """Check for recent bot activity"""
    print("\n🔍 Checking Recent Activity:")

    try:
        import sqlite3
        with sqlite3.connect("data/member_joins.db") as conn:
            # Check recent joins
            cursor = conn.execute("""
                SELECT COUNT(*) FROM member_joins
                WHERE join_timestamp >= datetime('now', '-24 hours')
            """)
            recent_joins = cursor.fetchone()[0]

            # Check recent notifications
            cursor = conn.execute("""
                SELECT COUNT(*) FROM notifications_sent
                WHERE notification_timestamp >= datetime('now', '-24 hours')
            """)
            recent_notifications = cursor.fetchone()[0]

            print(f"📈 Last 24 hours:")
            print(f"   - Member joins detected: {recent_joins}")
            print(f"   - Notifications sent: {recent_notifications}")

            # Check for any duplicates
            cursor = conn.execute("""
                SELECT COUNT(*) FROM (
                    SELECT user_id, server_id, COUNT(*) as cnt
                    FROM notifications_sent
                    GROUP BY user_id, server_id
                    HAVING cnt > 1
                )
            """)
            duplicates = cursor.fetchone()[0]

            if duplicates > 0:
                print(f"⚠️ Found {duplicates} duplicate notifications")
            else:
                print("✅ No duplicate notifications found")

    except Exception as e:
        print(f"❌ Could not check recent activity: {e}")

async def main():
    """Main validation function"""
    try:
        success = await validate_bot()
        check_recent_activity()

        print("\n" + "=" * 40)
        if success:
            print("🚀 Bot validation completed successfully!")
            print("   You can now start the bot with: python main.py")
        else:
            print("🛠️ Please fix the errors above before starting the bot.")

        return success

    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
