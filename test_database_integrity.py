#!/usr/bin/env python3
"""
Database Integrity Test Script for Discord Bot
Tests the duplicate notification prevention system
"""

import asyncio
import sqlite3
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.database_manager import DatabaseManager

async def test_database_integrity():
    """Test database integrity and duplicate prevention"""
    print("🔍 Testing Discord Bot Database Integrity...")

    # Initialize database manager
    db = DatabaseManager("data/member_joins.db")
    await db.initialize()

    print("✅ Database initialized successfully")

    # Test data - use unique IDs to avoid conflicts
    import random
    test_user_id = random.randint(900000000, 999999999)
    test_server_id = random.randint(900000000, 999999999)
    test_user_data = {
        'user_id': test_user_id,
        'username': 'TestUser',
        'display_name': 'Test User',
        'discriminator': '1234',
        'server_id': test_server_id,
        'server_name': 'Test Server',
        'join_timestamp': '2024-01-01T12:00:00Z',
        'account_created': '2023-01-01T12:00:00Z',
        'account_age_days': 365,
        'avatar_url': 'https://example.com/avatar.png',
        'is_bot': False,
        'is_verified': False
    }

    print(f"🧪 Testing with user {test_user_id} in server {test_server_id}")

    # Clean up any existing test data first
    with sqlite3.connect("data/member_joins.db") as conn:
        conn.execute("DELETE FROM member_joins WHERE user_id = ?", (test_user_id,))
        conn.execute("DELETE FROM notifications_sent WHERE user_id = ?", (test_user_id,))
        conn.commit()

    # Test 1: Record a new join
    print("\n📝 Test 1: Recording new member join...")
    join_id = await db.record_member_join(test_user_data)
    print(f"✅ Join recorded with ID: {join_id}")

    # Test 2: Check notification not sent initially
    print("\n🔍 Test 2: Checking initial notification status...")
    notif_sent = await db.check_notification_sent(test_user_id, test_server_id, 24)
    if not notif_sent:
        print("✅ Notification correctly marked as NOT sent")
    else:
        print("❌ ERROR: Notification incorrectly marked as sent")
        return False

    # Test 3: Mark notification as sent
    print("\n📤 Test 3: Marking notification as sent...")
    await db.mark_notification_sent(join_id)
    print("✅ Notification marked as sent")

    # Test 4: Check notification sent status
    print("\n🔍 Test 4: Verifying notification sent status...")
    notif_sent = await db.check_notification_sent(test_user_id, test_server_id, 24)
    if notif_sent:
        print("✅ Notification correctly marked as sent")
    else:
        print("❌ ERROR: Notification not properly marked as sent")
        return False

    # Test 5: Test duplicate prevention
    print("\n🚫 Test 5: Testing duplicate prevention...")
    duplicate_detected = await db.check_duplicate_join(test_user_id, test_server_id, 30)
    if duplicate_detected:
        print("✅ Duplicate correctly detected")
    else:
        print("❌ ERROR: Duplicate not detected")
        return False

    # Test 6: Verify notifications_sent table
    print("\n🗃️ Test 6: Checking notifications_sent table...")
    with sqlite3.connect("data/member_joins.db") as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) FROM notifications_sent
            WHERE user_id = ? AND server_id = ?
        """, (test_user_id, test_server_id))
        count = cursor.fetchone()[0]

        if count == 1:
            print("✅ Notification properly tracked in notifications_sent table")
        else:
            print(f"❌ ERROR: Expected 1 notification record, found {count}")
            return False

    # Test 7: Test database stats
    print("\n📊 Test 7: Checking database statistics...")
    stats = await db.get_database_stats()
    print(f"✅ Database stats: {stats}")

    # Cleanup test data
    print("\n🧹 Cleaning up test data...")
    with sqlite3.connect("data/member_joins.db") as conn:
        conn.execute("DELETE FROM member_joins WHERE user_id = ?", (test_user_id,))
        conn.execute("DELETE FROM notifications_sent WHERE user_id = ?", (test_user_id,))
        conn.commit()
    print("✅ Test data cleaned up")

    # Also clean up any leftover test data from previous runs
    with sqlite3.connect("data/member_joins.db") as conn:
        conn.execute("DELETE FROM member_joins WHERE user_id BETWEEN 900000000 AND 999999999")
        conn.execute("DELETE FROM notifications_sent WHERE user_id BETWEEN 900000000 AND 999999999")
        conn.commit()

    print("\n🎉 All database integrity tests passed!")
    return True

async def check_existing_duplicates():
    """Check for existing duplicate notifications in the database"""
    print("\n🔍 Checking for existing duplicate notifications...")

    with sqlite3.connect("data/member_joins.db") as conn:
        # Check for users with multiple notifications sent for the same server
        cursor = conn.execute("""
            SELECT user_id, server_id, COUNT(*) as notification_count
            FROM member_joins
            WHERE notification_sent = 1
            GROUP BY user_id, server_id
            HAVING COUNT(*) > 1
            ORDER BY notification_count DESC
        """)

        duplicates = cursor.fetchall()

        if duplicates:
            print(f"⚠️ Found {len(duplicates)} users with duplicate notifications:")
            for user_id, server_id, count in duplicates[:10]:  # Show first 10
                print(f"   User {user_id} in Server {server_id}: {count} notifications")

            if len(duplicates) > 10:
                print(f"   ... and {len(duplicates) - 10} more")

            return len(duplicates)
        else:
            print("✅ No duplicate notifications found")
            return 0

async def main():
    """Main test function"""
    print("🤖 Discord Bot Database Integrity Checker")
    print("=" * 50)

    try:
        # Run integrity tests
        success = await test_database_integrity()

        if success:
            # Check for existing duplicates
            duplicate_count = await check_existing_duplicates()

            if duplicate_count > 0:
                print(f"\n⚠️ WARNING: Found {duplicate_count} existing duplicate notifications")
                print("   Consider running cleanup or investigating the cause")
            else:
                print("\n✅ Database is clean with no duplicates")

        print("\n" + "=" * 50)
        print("✅ Database integrity check completed successfully!")

    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
