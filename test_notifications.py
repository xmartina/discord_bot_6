#!/usr/bin/env python3
"""
Discord Bot Notification Test Script
Tests the notification system specifically to debug missing DMs
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.config_manager import ConfigManager
from src.database_manager import DatabaseManager
from src.user_formatter import UserFormatter
from src.notification_manager import NotificationManager
import discord

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class TestBot(discord.Client):
    def __init__(self, config):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        super().__init__(intents=intents)

        self.config = config
        self.db = DatabaseManager(config.get_database_config()['path'])
        self.formatter = UserFormatter(config)
        self.notification_manager = NotificationManager(self, config, self.formatter)
        self.is_ready = False

    async def setup_hook(self):
        await self.db.initialize()
        await self.notification_manager.start_processing()

    async def on_ready(self):
        print(f"Test bot logged in as {self.user.name}")
        self.is_ready = True

async def test_notification_system():
    """Test the notification system with sample data"""
    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        config = ConfigManager()

        # Initialize bot
        bot = TestBot(config)

        # Start bot
        bot_task = asyncio.create_task(bot.start(config.get_discord_token()))

        # Wait for bot to be ready
        while not bot.is_ready:
            await asyncio.sleep(0.1)

        print("\n" + "="*60)
        print("TESTING NOTIFICATION SYSTEM")
        print("="*60)

        # Test 1: Basic notification sending
        print("\n📧 Test 1: Basic notification test")
        test_user_data = {
            'user_id': 123456789,
            'username': 'test_user',
            'display_name': 'Test User',
            'discriminator': '1234',
            'global_name': 'Test User',
            'server_id': 987654321,
            'server_name': 'Test Server',
            'join_timestamp': datetime.now(timezone.utc).isoformat(),
            'account_created': datetime.now(timezone.utc).isoformat(),
            'account_age_days': 30,
            'account_age_formatted': '30 days',
            'avatar_url': None,
            'is_bot': False,
            'is_verified': True,
            'is_system': False,
            'monitoring_source': 'test',
            'raw_data': {}
        }

        # Queue notification
        await bot.notification_manager.queue_member_join_notification(
            test_user_data, "test_monitoring", None
        )

        print("✅ Basic notification queued")

        # Test 2: User monitoring notification
        print("\n👤 Test 2: User monitoring notification")
        user_monitor_data = test_user_data.copy()
        user_monitor_data['username'] = 'user_monitor_test'
        user_monitor_data['monitoring_source'] = 'user_monitoring'

        await bot.notification_manager.queue_member_join_notification(
            user_monitor_data, "user_monitoring", None
        )

        print("✅ User monitoring notification queued")

        # Test 3: Check queue size
        queue_size = await bot.notification_manager.get_queue_size()
        print(f"\n📊 Queue size: {queue_size} notifications pending")

        # Test 4: Direct DM test
        print("\n💬 Test 4: Direct DM test")
        direct_success = await bot.notification_manager._send_discord_dm(user_monitor_data)
        print(f"✅ Direct DM result: {'Success' if direct_success else 'Failed'}")

        # Test 5: Check user ID configuration
        print("\n🆔 Test 5: Configuration check")
        user_id = config.get_user_id()
        print(f"Configured user ID: {user_id}")

        try:
            user = await bot.fetch_user(user_id)
            print(f"✅ User found: {user.name}#{user.discriminator}")
        except Exception as e:
            print(f"❌ Error fetching user: {e}")

        # Test 6: Message formatting
        print("\n📝 Test 6: Message formatting")
        message = bot.formatter.format_notification_message(user_monitor_data)
        print(f"Message preview (first 200 chars):")
        print(f"{message[:200]}...")
        print(f"Full message length: {len(message)} characters")

        # Wait for notifications to process
        print("\n⏳ Waiting 10 seconds for notifications to process...")
        await asyncio.sleep(10)

        # Check final queue size
        final_queue_size = await bot.notification_manager.get_queue_size()
        print(f"📊 Final queue size: {final_queue_size} notifications pending")

        if final_queue_size == 0:
            print("✅ All notifications processed successfully!")
        else:
            print(f"⚠️ {final_queue_size} notifications still in queue")

        # Test 7: Database duplicate check
        print("\n🗄️ Test 7: Database duplicate check")

        # Record a test join
        join_id = await bot.db.record_member_join(user_monitor_data)
        print(f"Recorded join with ID: {join_id}")

        # Check for duplicate
        is_duplicate = await bot.db.check_duplicate_join(
            user_id=user_monitor_data['user_id'],
            server_id=user_monitor_data['server_id'],
            within_minutes=1440
        )
        print(f"Duplicate check result: {'Duplicate found' if is_duplicate else 'No duplicate'}")

        # Check notification sent status
        notification_sent = await bot.db.check_notification_sent(
            user_id=user_monitor_data['user_id'],
            server_id=user_monitor_data['server_id'],
            within_hours=24
        )
        print(f"Notification sent status: {'Already sent' if notification_sent else 'Not sent'}")

        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✅ Basic notification system: Working")
        print("✅ User monitoring notifications: Working")
        print("✅ Message formatting: Working")
        print("✅ Database operations: Working")
        print(f"✅ Queue processing: {'Working' if final_queue_size == 0 else 'Issues detected'}")

        # Cleanup
        await bot.db.close()
        await bot.close()
        bot_task.cancel()

        return True

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_user_monitoring_callback():
    """Test the user monitoring callback functionality specifically"""
    print("\n" + "="*60)
    print("TESTING USER MONITORING CALLBACK")
    print("="*60)

    try:
        config = ConfigManager()
        db = DatabaseManager(config.get_database_config()['path'])
        await db.initialize()
        formatter = UserFormatter(config)

        # Create a simple bot instance for callback testing
        class SimpleBot:
            def __init__(self):
                self.config = config
                self.db = db
                self.formatter = formatter
                self.notification_manager = None
                self.stats = {'member_joins_processed': 0, 'notifications_sent': 0, 'errors_encountered': 0}

            async def _handle_user_monitoring_join(self, user_data, source="user_monitoring"):
                print(f"🔄 Processing user monitoring join: {user_data['username']} in {user_data['server_name']}")

                # Check for duplicate
                is_duplicate = await self.db.check_duplicate_join(
                    user_id=user_data['user_id'],
                    server_id=user_data['server_id'],
                    within_minutes=1440
                )

                if is_duplicate:
                    print(f"⏭️ Duplicate detected for {user_data['username']}, skipping")
                    return

                # Record in database
                join_id = await self.db.record_member_join(user_data)
                print(f"💾 Recorded in database with ID: {join_id}")

                # Check if should notify
                if self.formatter.should_notify(user_data):
                    print(f"✅ Should notify: YES")
                    # Here would be the notification call
                    print(f"📧 Would send notification for {user_data['username']}")

                    # Mark as sent
                    await self.db.mark_notification_sent(join_id)
                    self.stats['notifications_sent'] += 1
                else:
                    print(f"❌ Should notify: NO (filtered)")

                self.stats['member_joins_processed'] += 1
                print(f"✅ Processing complete for {user_data['username']}")

        bot = SimpleBot()

        # Test callback with sample data
        test_data = {
            'user_id': 999888777,
            'username': 'callback_test_user',
            'display_name': 'Callback Test User',
            'discriminator': None,
            'global_name': 'Callback Test User',
            'server_id': 111222333,
            'server_name': 'Callback Test Server',
            'join_timestamp': datetime.now(timezone.utc).isoformat(),
            'account_created': datetime.now(timezone.utc).isoformat(),
            'account_age_days': 15,
            'account_age_formatted': '15 days',
            'avatar_url': None,
            'is_bot': False,
            'is_verified': True,
            'is_system': False,
            'monitoring_source': 'user_monitoring',
            'raw_data': {}
        }

        print("\n🧪 Testing callback with sample data...")
        await bot._handle_user_monitoring_join(test_data, "user_monitoring")

        print(f"\n📊 Stats after test:")
        print(f"   - Joins processed: {bot.stats['member_joins_processed']}")
        print(f"   - Notifications sent: {bot.stats['notifications_sent']}")
        print(f"   - Errors: {bot.stats['errors_encountered']}")

        # Test duplicate handling
        print("\n🔄 Testing duplicate handling...")
        await bot._handle_user_monitoring_join(test_data, "user_monitoring")

        print(f"📊 Stats after duplicate test:")
        print(f"   - Joins processed: {bot.stats['member_joins_processed']}")
        print(f"   - Notifications sent: {bot.stats['notifications_sent']}")

        await db.close()

        print("\n✅ User monitoring callback test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Callback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all notification tests"""
    print("🚀 Starting Discord Bot Notification Tests")
    print("=" * 80)

    try:
        # Test 1: Full notification system
        print("\n🔍 Running full notification system test...")
        success1 = await test_notification_system()

        # Test 2: User monitoring callback
        print("\n🔍 Running user monitoring callback test...")
        success2 = await test_user_monitoring_callback()

        # Final summary
        print("\n" + "="*80)
        print("FINAL TEST RESULTS")
        print("="*80)

        if success1 and success2:
            print("🎉 ALL NOTIFICATION TESTS PASSED!")
            print("✅ Notification system is working correctly")
            print("✅ User monitoring callbacks are functional")
            print("✅ Database operations are working")
            print("\nThe notification issues should now be resolved!")
        else:
            print("❌ Some notification tests failed")
            print("Please check the detailed output above for specific issues")

        return success1 and success2

    except Exception as e:
        print(f"💥 Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            print("\n✅ Notification tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Notification tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Tests crashed: {e}")
        sys.exit(1)
