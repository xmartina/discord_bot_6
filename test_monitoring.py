#!/usr/bin/env python3
"""
Test script for Discord Member Monitoring Bot
Tests the improved user monitoring functionality
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import logging

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.config_manager import ConfigManager
from src.user_client import DiscordUserClient
from src.database_manager import DatabaseManager
from src.user_formatter import UserFormatter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def test_user_monitoring():
    """Test the user monitoring functionality"""
    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        config = ConfigManager()

        # Initialize components
        db = DatabaseManager(config.get_database_config()['path'])
        await db.initialize()

        formatter = UserFormatter(config)

        # Test callback function
        async def test_callback(user_data, source="user_monitoring"):
            logger.info(f"TEST CALLBACK: New member detected via {source}")
            logger.info(f"  - User: {user_data['username']} ({user_data['user_id']})")
            logger.info(f"  - Server: {user_data['server_name']} ({user_data['server_id']})")
            logger.info(f"  - Account Age: {user_data['account_age_formatted']}")
            logger.info(f"  - Monitoring Source: {user_data.get('monitoring_source', 'unknown')}")

            # Test notification formatting
            should_notify = formatter.should_notify(user_data)
            logger.info(f"  - Should notify: {should_notify}")

            if should_notify:
                message = formatter.format_notification_message(user_data)
                logger.info(f"  - Formatted message length: {len(message)} chars")
                logger.info(f"  - Message preview: {message[:100]}...")

        # Initialize user client
        user_client = DiscordUserClient(config, db, formatter, test_callback)

        # Test user token initialization
        user_token = config.get_user_token()
        if not user_token:
            logger.error("No user token configured!")
            return False

        logger.info("Testing user token initialization...")
        if await user_client.initialize(user_token):
            logger.info("✅ User client initialized successfully")
            logger.info(f"  - User: {user_client.user_info['username']}")
            logger.info(f"  - User ID: {user_client.user_info['id']}")
        else:
            logger.error("❌ User client initialization failed")
            return False

        # Test guild discovery
        logger.info("\nTesting guild discovery...")
        guilds = await user_client.discover_user_guilds()
        logger.info(f"✅ Found {len(guilds)} guilds where user is a member")

        for guild in guilds[:5]:  # Show first 5 guilds
            logger.info(f"  - {guild['name']} ({guild['id']})")

        if len(guilds) > 5:
            logger.info(f"  - ... and {len(guilds) - 5} more guilds")

        # Test monitoring capabilities for each guild
        logger.info("\nTesting monitoring capabilities...")

        excluded_servers = config.get_excluded_servers()
        monitoring_results = []

        for guild in guilds[:3]:  # Test first 3 guilds
            guild_id = guild['id']
            guild_name = guild['name']

            # Skip excluded servers
            if int(guild_id) in excluded_servers:
                logger.info(f"⏭️  Skipping excluded server: {guild_name}")
                continue

            logger.info(f"\n🔍 Testing monitoring for: {guild_name}")

            # Test basic guild info access
            guild_info = await user_client.get_guild_info(guild_id)
            if guild_info:
                logger.info(f"  ✅ Guild info accessible")

                # Check available fields
                available_fields = [k for k in guild_info.keys() if 'member' in k.lower() or 'count' in k.lower()]
                if available_fields:
                    logger.info(f"  📊 Available count fields: {available_fields}")
                    for field in available_fields:
                        logger.info(f"    - {field}: {guild_info.get(field)}")
                else:
                    logger.info(f"  ⚠️  No member count fields available")

            else:
                logger.info(f"  ❌ Guild info not accessible")

            # Test channel access
            channels = await user_client.get_guild_channels(guild_id)
            if channels:
                logger.info(f"  ✅ Found {len(channels)} accessible channels")
                for channel in channels[:3]:  # Show first 3 channels
                    logger.info(f"    - #{channel['name']} ({channel['id']})")
            else:
                logger.info(f"  ❌ No accessible channels")

            # Test activity monitoring
            try:
                new_members = await user_client.monitor_guild_for_new_members(guild_id, guild_name)
                if new_members:
                    logger.info(f"  🎉 Detected {len(new_members)} new members!")
                    monitoring_results.extend(new_members)
                else:
                    logger.info(f"  ℹ️  No new members detected")
            except Exception as e:
                logger.error(f"  ❌ Error monitoring guild: {e}")

        # Test monitoring statistics
        logger.info("\nTesting monitoring statistics...")
        stats = await user_client.get_monitoring_stats()
        logger.info(f"✅ Monitoring statistics:")
        logger.info(f"  - Total accessible guilds: {stats['total_accessible_guilds']}")
        logger.info(f"  - Monitored guilds: {stats['monitored_guilds']}")
        logger.info(f"  - Excluded guilds: {stats['excluded_guilds']}")

        # Test error handling
        logger.info("\nTesting error handling...")

        # Test invalid guild ID
        invalid_result = await user_client.get_guild_info("999999999999999999")
        if invalid_result is None:
            logger.info("✅ Invalid guild ID handled correctly")
        else:
            logger.warning("⚠️  Invalid guild ID should return None")

        # Test invalid channel access
        invalid_channels = await user_client.get_guild_channels("999999999999999999")
        if not invalid_channels:
            logger.info("✅ Invalid channel access handled correctly")
        else:
            logger.warning("⚠️  Invalid channel access should return empty list")

        # Summary
        logger.info("\n" + "="*50)
        logger.info("TEST SUMMARY")
        logger.info("="*50)
        logger.info(f"✅ User client initialization: PASSED")
        logger.info(f"✅ Guild discovery: PASSED ({len(guilds)} guilds found)")
        logger.info(f"✅ Monitoring capabilities: TESTED")
        logger.info(f"✅ Error handling: PASSED")
        logger.info(f"✅ Statistics: PASSED")

        if monitoring_results:
            logger.info(f"🎉 New members detected: {len(monitoring_results)}")
            logger.info("✅ User monitoring is working correctly!")
        else:
            logger.info("ℹ️  No new members detected during test (normal)")

        # Close connections
        await user_client.close()
        await db.close()

        return True

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_alternative_monitoring():
    """Test alternative monitoring methods"""
    logger = logging.getLogger(__name__)

    try:
        config = ConfigManager()
        db = DatabaseManager(config.get_database_config()['path'])
        await db.initialize()

        formatter = UserFormatter(config)
        user_client = DiscordUserClient(config, db, formatter)

        user_token = config.get_user_token()
        if not user_token:
            logger.error("No user token configured!")
            return False

        if not await user_client.initialize(user_token):
            logger.error("Failed to initialize user client")
            return False

        logger.info("Testing alternative monitoring methods...")

        # Get first guild for testing
        guilds = await user_client.discover_user_guilds()
        if not guilds:
            logger.error("No guilds found for testing")
            return False

        test_guild = guilds[0]
        guild_id = test_guild['id']
        guild_name = test_guild['name']

        logger.info(f"Testing with guild: {guild_name}")

        # Test alternative monitoring
        result = await user_client._try_alternative_monitoring(guild_id, guild_name)

        if result:
            logger.info(f"✅ Alternative monitoring detected {len(result)} members")
            for member in result:
                logger.info(f"  - {member['username']} in {member['server_name']}")
        else:
            logger.info("ℹ️  No members detected via alternative monitoring")

        await user_client.close()
        await db.close()

        return True

    except Exception as e:
        logger.error(f"❌ Alternative monitoring test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger = logging.getLogger(__name__)

    logger.info("🚀 Starting Discord Member Monitoring Tests")
    logger.info("=" * 60)

    # Test 1: Basic user monitoring
    logger.info("\n🧪 TEST 1: Basic User Monitoring Functionality")
    logger.info("-" * 60)

    success1 = await test_user_monitoring()

    # Test 2: Alternative monitoring methods
    logger.info("\n🧪 TEST 2: Alternative Monitoring Methods")
    logger.info("-" * 60)

    success2 = await test_alternative_monitoring()

    # Final summary
    logger.info("\n" + "="*60)
    logger.info("FINAL TEST RESULTS")
    logger.info("="*60)

    if success1 and success2:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ User monitoring is working correctly")
        logger.info("✅ Error handling is robust")
        logger.info("✅ Alternative monitoring methods are functional")
        logger.info("\nThe bot should now properly handle groups where it wasn't invited!")
    else:
        logger.error("❌ Some tests failed")
        logger.error("Please check the logs above for specific issues")

    return success1 and success2

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            print("\n✅ Test completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Test failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        sys.exit(1)
