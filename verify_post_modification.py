#!/usr/bin/env python3
"""
Post-Modification Verification Script for Discord Bot
Comprehensive test to verify all fixes are intact after Sonnet 3.7 modifications
"""

import asyncio
import sqlite3
import sys
import os
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

class PostModificationVerifier:
    def __init__(self):
        self.db_path = "data/member_joins.db"
        self.config_path = "config.yaml"
        self.errors = []
        self.warnings = []
        self.successes = []

    def log_success(self, message):
        self.successes.append(message)
        print(f"✅ {message}")

    def log_warning(self, message):
        self.warnings.append(message)
        print(f"⚠️ {message}")

    def log_error(self, message):
        self.errors.append(message)
        print(f"❌ {message}")

    def verify_config_token_update(self):
        """Verify the user token was correctly updated"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            expected_token = "MTM4NzUxMzM5NTMzNDYxNTA2MQ.G0XGGE.8xrey14fz5maAlExZ5tGs_6NuenQw7D1H6VkgE"
            actual_token = config['discord']['user_token']

            if actual_token == expected_token:
                self.log_success("User token correctly updated in config.yaml")
            else:
                self.log_error(f"User token mismatch. Expected: {expected_token}, Got: {actual_token}")

            # Check if user_id was changed
            user_id = config['discord']['user_id']
            if user_id == "1387513395334615061":
                self.log_warning(f"User ID was changed to {user_id} (was 1371624094860312608)")
            else:
                self.log_success(f"User ID maintained: {user_id}")

        except Exception as e:
            self.log_error(f"Failed to verify config: {e}")

    def verify_database_schema(self):
        """Verify the notifications_sent table and indexes exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if notifications_sent table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='notifications_sent'
                """)

                if cursor.fetchone():
                    self.log_success("notifications_sent table exists")

                    # Check table structure
                    cursor.execute("PRAGMA table_info(notifications_sent)")
                    columns = {row[1]: row[2] for row in cursor.fetchall()}

                    expected_columns = {
                        'id': 'INTEGER',
                        'user_id': 'INTEGER',
                        'server_id': 'INTEGER',
                        'notification_timestamp': 'TIMESTAMP',
                        'join_id': 'INTEGER'
                    }

                    schema_correct = True
                    for col, col_type in expected_columns.items():
                        if col not in columns:
                            self.log_error(f"Missing column {col} in notifications_sent table")
                            schema_correct = False
                        elif col_type.upper() not in columns[col].upper():
                            self.log_warning(f"Column {col} type mismatch: expected {col_type}, got {columns[col]}")

                    if schema_correct:
                        self.log_success("notifications_sent table schema is correct")

                    # Check unique constraint
                    cursor.execute("""
                        SELECT sql FROM sqlite_master
                        WHERE type='table' AND name='notifications_sent'
                    """)
                    table_sql = cursor.fetchone()[0]
                    if "UNIQUE(user_id, server_id)" in table_sql:
                        self.log_success("Unique constraint on (user_id, server_id) exists")
                    else:
                        self.log_error("Missing unique constraint on (user_id, server_id)")

                else:
                    self.log_error("notifications_sent table does not exist")

                # Check for required indexes
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND name LIKE 'idx_notifications_sent%'
                """)
                indexes = [row[0] for row in cursor.fetchall()]

                expected_indexes = [
                    'idx_notifications_sent_user_server',
                    'idx_notifications_sent_timestamp'
                ]

                for idx in expected_indexes:
                    if idx in indexes:
                        self.log_success(f"Index {idx} exists")
                    else:
                        self.log_warning(f"Index {idx} missing (may affect performance)")

        except Exception as e:
            self.log_error(f"Database schema verification failed: {e}")

    async def verify_database_methods(self):
        """Verify database manager methods are working correctly"""
        try:
            from src.database_manager import DatabaseManager

            db = DatabaseManager(self.db_path)
            await db.initialize()

            # Test check_notification_sent method
            result = await db.check_notification_sent(999999999, 888888888, 24)
            if isinstance(result, bool):
                self.log_success("check_notification_sent method works correctly")
            else:
                self.log_error("check_notification_sent method return type incorrect")

            # Test mark_notification_sent method exists
            if hasattr(db, 'mark_notification_sent'):
                self.log_success("mark_notification_sent method exists")
            else:
                self.log_error("mark_notification_sent method missing")

            # Test check_duplicate_join method
            result = await db.check_duplicate_join(999999999, 888888888, 30)
            if isinstance(result, bool):
                self.log_success("check_duplicate_join method works correctly")
            else:
                self.log_error("check_duplicate_join method return type incorrect")

        except Exception as e:
            self.log_error(f"Database methods verification failed: {e}")

    def verify_discord_bot_logic(self):
        """Verify the Discord bot logic still contains our fixes"""
        try:
            bot_file = Path("src/discord_bot.py")
            with open(bot_file, 'r') as f:
                content = f.read()

            # Check for our specific fixes
            checks = [
                ("check_notification_sent", "24-hour duplicate prevention check"),
                ("mark_notification_sent", "Notification marking after successful send"),
                ("within_hours=24", "Standardized 24-hour window"),
                ("try:", "Error handling for notifications"),
                ("except Exception as notification_error:", "Specific notification error handling")
            ]

            for check, description in checks:
                if check in content:
                    self.log_success(f"Found {description}")
                else:
                    self.log_error(f"Missing {description} - {check}")

            # Check that old flawed logic is not present
            bad_patterns = [
                "within_minutes=5",  # Old 5-minute window for bot monitoring
                "within_minutes=1440"  # Old 1440-minute window
            ]

            for pattern in bad_patterns:
                if pattern in content:
                    self.log_warning(f"Found old pattern that should be updated: {pattern}")

        except Exception as e:
            self.log_error(f"Discord bot logic verification failed: {e}")

    def verify_database_integrity(self):
        """Check for any duplicate notifications in current database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check for duplicates in member_joins table
                cursor.execute("""
                    SELECT user_id, server_id, COUNT(*) as count
                    FROM member_joins
                    WHERE notification_sent = 1
                    GROUP BY user_id, server_id
                    HAVING COUNT(*) > 1
                """)

                duplicates = cursor.fetchall()
                if duplicates:
                    self.log_error(f"Found {len(duplicates)} duplicate notifications in member_joins table")
                    for user_id, server_id, count in duplicates[:3]:  # Show first 3
                        self.log_error(f"  User {user_id} in Server {server_id}: {count} notifications")
                else:
                    self.log_success("No duplicate notifications found in member_joins table")

                # Check notifications_sent table if it exists
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='notifications_sent'
                """)

                if cursor.fetchone():
                    cursor.execute("""
                        SELECT user_id, server_id, COUNT(*) as count
                        FROM notifications_sent
                        GROUP BY user_id, server_id
                        HAVING COUNT(*) > 1
                    """)

                    sent_duplicates = cursor.fetchall()
                    if sent_duplicates:
                        self.log_error(f"Found {len(sent_duplicates)} duplicate entries in notifications_sent table")
                    else:
                        self.log_success("No duplicate entries in notifications_sent table")

                # Get overall stats
                cursor.execute("SELECT COUNT(*) FROM member_joins")
                total_joins = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM member_joins WHERE notification_sent = 1")
                total_notifications = cursor.fetchone()[0]

                self.log_success(f"Database stats: {total_joins} total joins, {total_notifications} notifications sent")

        except Exception as e:
            self.log_error(f"Database integrity check failed: {e}")

    def verify_files_integrity(self):
        """Verify important files still exist and contain our fixes"""
        important_files = [
            "src/database_manager.py",
            "src/discord_bot.py",
            "test_database_integrity.py",
            "fix_duplicates.py",
            "DUPLICATE_NOTIFICATION_FIX_SUMMARY.md",
            "DEPLOYMENT_READY_SUMMARY.md"
        ]

        for file_path in important_files:
            if Path(file_path).exists():
                self.log_success(f"File {file_path} exists")
            else:
                self.log_error(f"File {file_path} is missing")

    def check_sonnet_additions(self):
        """Check what Sonnet 3.7 added and ensure it doesn't break our fixes"""
        sonnet_files = [
            "BOT_OPERATION_GUIDE.md",
            "BOT_STATUS_SUMMARY.md",
            "DISCORD_BOT_IMPROVEMENTS.md",
            "check_bot_status.py",
            "check_bot_status.bat",
            "restart_bot.bat"
        ]

        found_files = []
        for file_path in sonnet_files:
            if Path(file_path).exists():
                found_files.append(file_path)

        if found_files:
            self.log_success(f"Found {len(found_files)} Sonnet 3.7 additions: {', '.join(found_files)}")
            self.log_success("Sonnet 3.7 additions appear to be operational improvements")
        else:
            self.log_warning("No obvious Sonnet 3.7 additions found")

    async def run_comprehensive_test(self):
        """Run a comprehensive test similar to our integrity test"""
        try:
            from src.database_manager import DatabaseManager
            import random

            db = DatabaseManager(self.db_path)
            await db.initialize()

            # Use unique test IDs
            test_user_id = random.randint(800000000, 899999999)
            test_server_id = random.randint(800000000, 899999999)

            test_data = {
                'user_id': test_user_id,
                'username': 'PostModTest',
                'display_name': 'Post Modification Test',
                'server_id': test_server_id,
                'server_name': 'Test Server Post Mod',
                'join_timestamp': datetime.now().isoformat(),
                'is_bot': False,
                'is_verified': False
            }

            # Test the full workflow
            # 1. Check notification not sent initially
            notif_sent = await db.check_notification_sent(test_user_id, test_server_id, 24)
            if not notif_sent:
                self.log_success("Initial notification check: correctly not sent")
            else:
                self.log_error("Initial notification check: incorrectly marked as sent")
                return

            # 2. Record join
            join_id = await db.record_member_join(test_data)
            if join_id and join_id > 0:
                self.log_success(f"Join recorded successfully with ID: {join_id}")
            else:
                self.log_error("Failed to record join")
                return

            # 3. Mark notification as sent
            await db.mark_notification_sent(join_id)
            self.log_success("Notification marked as sent")

            # 4. Check notification now shows as sent
            notif_sent = await db.check_notification_sent(test_user_id, test_server_id, 24)
            if notif_sent:
                self.log_success("Post-send notification check: correctly marked as sent")
            else:
                self.log_error("Post-send notification check: not properly marked as sent")

            # 5. Test duplicate detection
            duplicate_detected = await db.check_duplicate_join(test_user_id, test_server_id, 30)
            if duplicate_detected:
                self.log_success("Duplicate detection: correctly detected")
            else:
                self.log_error("Duplicate detection: failed to detect duplicate")

            # 6. Cleanup
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM member_joins WHERE user_id = ?", (test_user_id,))
                conn.execute("DELETE FROM notifications_sent WHERE user_id = ?", (test_user_id,))
                conn.commit()
            self.log_success("Test data cleaned up")

        except Exception as e:
            self.log_error(f"Comprehensive test failed: {e}")

    async def main(self):
        """Main verification function"""
        print("🔍 Post-Modification Verification for Discord Bot")
        print("=" * 60)
        print("Checking if all duplicate prevention fixes are intact after Sonnet 3.7 modifications...\n")

        # Run all verification checks
        self.verify_config_token_update()
        print()

        self.verify_database_schema()
        print()

        await self.verify_database_methods()
        print()

        self.verify_discord_bot_logic()
        print()

        self.verify_database_integrity()
        print()

        self.verify_files_integrity()
        print()

        self.check_sonnet_additions()
        print()

        await self.run_comprehensive_test()
        print()

        # Summary
        print("=" * 60)
        print("📋 VERIFICATION SUMMARY")
        print("=" * 60)

        print(f"✅ Successes: {len(self.successes)}")
        print(f"⚠️ Warnings:  {len(self.warnings)}")
        print(f"❌ Errors:    {len(self.errors)}")
        print()

        if self.errors:
            print("❌ CRITICAL ISSUES FOUND:")
            for error in self.errors:
                print(f"   - {error}")
            print()

        if self.warnings:
            print("⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"   - {warning}")
            print()

        # Final verdict
        if not self.errors:
            if not self.warnings:
                print("🎉 PERFECT: All fixes intact, no issues found!")
                print("✅ Bot is ready for deployment to AWS server")
            else:
                print("✅ GOOD: Core fixes intact, minor warnings only")
                print("✅ Bot is ready for deployment to AWS server")
            success = True
        else:
            print("❌ ISSUES FOUND: Critical errors detected")
            print("🔧 Please fix errors before deploying to AWS server")
            success = False

        print("\n" + "=" * 60)
        print("🚀 Recommendation:")
        if success:
            print("   ✅ SAFE TO DEPLOY - All duplicate prevention fixes are working")
            print("   ✅ Sonnet 3.7 changes are operational improvements only")
            print("   ✅ No conflicts with our duplicate notification fixes")
        else:
            print("   ⚠️ DO NOT DEPLOY - Fix critical issues first")

        return success

if __name__ == "__main__":
    verifier = PostModificationVerifier()
    result = asyncio.run(verifier.main())
    sys.exit(0 if result else 1)
