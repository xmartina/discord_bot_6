#!/usr/bin/env python3
"""
Enhanced Detection Test Script for Discord Bot
Tests the new activity-based detection methods to ensure real usernames are captured
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config_manager import ConfigManager
from src.database_manager import DatabaseManager
from src.user_formatter import UserFormatter
from src.user_client import DiscordUserClient

# Set up logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/enhanced_detection_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class EnhancedDetectionTester:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.user_client = None

    async def initialize(self):
        """Initialize the user client for testing"""
        try:
            # Initialize components
            db = DatabaseManager(self.config.get_database_config()['path'])
            await db.initialize()

            formatter = UserFormatter(self.config)

            # Create user client
            self.user_client = DiscordUserClient(self.config, db, formatter)

            # Initialize with user token
            user_token = self.config.get_user_token()
            if not user_token:
                logger.error("No user token configured")
                return False

            success = await self.user_client.initialize(user_token)
            if success:
                logger.info("User client initialized successfully")
                return True
            else:
                logger.error("Failed to initialize user client")
                return False

        except Exception as e:
            logger.error(f"Error initializing: {e}")
            return False

    async def test_activity_detection_methods(self):
        """Test all activity-based detection methods"""
        logger.info("="*60)
        logger.info("Testing Activity-Based Detection Methods")
        logger.info("="*60)

        # Get user guilds
        guilds = await self.user_client.discover_user_guilds()
        if not guilds:
            logger.error("No guilds found")
            return False

        logger.info(f"Testing on {len(guilds)} guilds...")

        for guild in guilds[:3]:  # Test on first 3 guilds
            guild_id = guild.get('id')
            guild_name = guild.get('name', 'Unknown')

            logger.info(f"\n{'='*40}")
            logger.info(f"Testing Guild: {guild_name}")
            logger.info(f"Guild ID: {guild_id}")
            logger.info(f"{'='*40}")

            # Test Method 2: Channel Activity Monitoring
            await self._test_channel_activity(guild_id, guild_name)

            # Test Method 3: Message Pattern Analysis
            await self._test_message_patterns(guild_id, guild_name)

            # Test Method 5: Deep Channel Scanning
            await self._test_deep_scanning(guild_id, guild_name)

            # Test Enhanced Message Scanning
            await self._test_recent_message_scanning(guild_id, guild_name)

        return True

    async def _test_channel_activity(self, guild_id: str, guild_name: str):
        """Test channel activity monitoring"""
        logger.info(f"\n--- Testing Channel Activity Monitoring ---")
        try:
            results = await self.user_client._method_2_channel_activity_monitoring(guild_id, guild_name, True)
            if results:
                logger.info(f"✅ Channel activity detected {len(results)} members:")
                for member in results:
                    username = member.get('username', 'Unknown')
                    monitoring_source = member.get('monitoring_source', 'Unknown')
                    logger.info(f"  - {username} (via {monitoring_source})")
            else:
                logger.info("❌ No channel activity detected")
        except Exception as e:
            logger.error(f"Error in channel activity test: {e}")

    async def _test_message_patterns(self, guild_id: str, guild_name: str):
        """Test message pattern analysis"""
        logger.info(f"\n--- Testing Message Pattern Analysis ---")
        try:
            results = await self.user_client._method_3_message_pattern_analysis(guild_id, guild_name, True)
            if results:
                logger.info(f"✅ Message patterns detected {len(results)} members:")
                for member in results:
                    username = member.get('username', 'Unknown')
                    monitoring_source = member.get('monitoring_source', 'Unknown')
                    logger.info(f"  - {username} (via {monitoring_source})")
            else:
                logger.info("❌ No message patterns detected")
        except Exception as e:
            logger.error(f"Error in message pattern test: {e}")

    async def _test_deep_scanning(self, guild_id: str, guild_name: str):
        """Test deep channel scanning"""
        logger.info(f"\n--- Testing Deep Channel Scanning ---")
        try:
            results = await self.user_client._method_5_deep_channel_scanning(guild_id, guild_name, True)
            if results:
                logger.info(f"✅ Deep scanning detected {len(results)} members:")
                for member in results:
                    username = member.get('username', 'Unknown')
                    monitoring_source = member.get('monitoring_source', 'Unknown')
                    logger.info(f"  - {username} (via {monitoring_source})")
            else:
                logger.info("❌ No deep scanning results")
        except Exception as e:
            logger.error(f"Error in deep scanning test: {e}")

    async def _test_recent_message_scanning(self, guild_id: str, guild_name: str):
        """Test recent message scanning for real usernames"""
        logger.info(f"\n--- Testing Recent Message Scanning ---")
        try:
            result = await self.user_client._scan_recent_messages_for_new_members(guild_id, guild_name)
            if result:
                username = result.get('username', 'Unknown')
                account_age = result.get('account_age_formatted', 'Unknown')
                detection_method = result.get('raw_data', {}).get('detection_method', 'Unknown')
                logger.info(f"✅ Recent message scan found: {username}")
                logger.info(f"  - Account age: {account_age}")
                logger.info(f"  - Detection method: {detection_method}")
            else:
                logger.info("❌ No recent activity found")
        except Exception as e:
            logger.error(f"Error in recent message scanning: {e}")

    async def test_count_vs_activity_detection(self):
        """Compare count-based vs activity-based detection"""
        logger.info("\n" + "="*60)
        logger.info("Comparing Count-Based vs Activity-Based Detection")
        logger.info("="*60)

        guilds = await self.user_client.discover_user_guilds()
        if not guilds:
            return

        for guild in guilds[:2]:  # Test on first 2 guilds
            guild_id = guild.get('id')
            guild_name = guild.get('name', 'Unknown')

            logger.info(f"\n--- Testing {guild_name} ---")

            # Test count-based detection
            logger.info("Testing count-based detection...")
            count_results = await self.user_client._method_1_member_count_tracking(guild_id, guild_name, True)

            # Test activity-based detection
            logger.info("Testing activity-based detection...")
            activity_results = []

            # Method 2
            results = await self.user_client._method_2_channel_activity_monitoring(guild_id, guild_name, False)
            activity_results.extend(results)

            # Method 3
            results = await self.user_client._method_3_message_pattern_analysis(guild_id, guild_name, False)
            activity_results.extend(results)

            # Compare results
            logger.info(f"\nResults for {guild_name}:")
            logger.info(f"  Count-based detections: {len(count_results)}")
            logger.info(f"  Activity-based detections: {len(activity_results)}")

            if count_results:
                logger.info("  Count-based usernames:")
                for member in count_results:
                    username = member.get('username', 'Unknown')
                    logger.info(f"    - {username}")

            if activity_results:
                logger.info("  Activity-based usernames:")
                for member in activity_results:
                    username = member.get('username', 'Unknown')
                    logger.info(f"    - {username}")

            # Determine which method provides better data
            activity_real_users = sum(1 for m in activity_results if not m.get('username', '').startswith('New Member'))
            count_real_users = sum(1 for m in count_results if not m.get('username', '').startswith('New Member'))

            logger.info(f"\n  Real usernames found:")
            logger.info(f"    Activity-based: {activity_real_users}")
            logger.info(f"    Count-based: {count_real_users}")

            if activity_real_users > count_real_users:
                logger.info("  ✅ Activity-based detection is better!")
            elif count_real_users > activity_real_users:
                logger.info("  ✅ Count-based detection is better!")
            else:
                logger.info("  🤔 Both methods are equal")

    async def test_comprehensive_monitoring(self):
        """Test the comprehensive monitoring that mimics real bot behavior"""
        logger.info("\n" + "="*60)
        logger.info("Testing Comprehensive Monitoring (Real Bot Behavior)")
        logger.info("="*60)

        guilds = await self.user_client.discover_user_guilds()
        if not guilds:
            return

        # Test on first guild
        guild = guilds[0]
        guild_id = guild.get('id')
        guild_name = guild.get('name', 'Unknown')

        logger.info(f"Running comprehensive monitoring on: {guild_name}")

        try:
            results = await self.user_client.comprehensive_guild_monitoring(guild_id, guild_name)

            logger.info(f"\nComprehensive monitoring results:")
            logger.info(f"  Total detections: {len(results)}")

            if results:
                real_usernames = 0
                generic_usernames = 0

                for member in results:
                    username = member.get('username', 'Unknown')
                    monitoring_source = member.get('monitoring_source', 'Unknown')
                    detection_method = member.get('raw_data', {}).get('detection_method', 'Unknown')

                    logger.info(f"  - {username}")
                    logger.info(f"    Source: {monitoring_source}")
                    logger.info(f"    Method: {detection_method}")

                    if username.startswith('New Member'):
                        generic_usernames += 1
                    else:
                        real_usernames += 1

                logger.info(f"\nSummary:")
                logger.info(f"  Real usernames: {real_usernames}")
                logger.info(f"  Generic usernames: {generic_usernames}")

                success_rate = (real_usernames / len(results)) * 100 if results else 0
                logger.info(f"  Success rate: {success_rate:.1f}%")

                if success_rate >= 80:
                    logger.info("  ✅ EXCELLENT - Bot is getting real usernames!")
                elif success_rate >= 60:
                    logger.info("  ✅ GOOD - Bot is mostly getting real usernames")
                elif success_rate >= 40:
                    logger.info("  ⚠️ FAIR - Bot is getting some real usernames")
                else:
                    logger.info("  ❌ POOR - Bot is mostly getting generic usernames")
            else:
                logger.info("  No members detected in this cycle")

        except Exception as e:
            logger.error(f"Error in comprehensive monitoring test: {e}")

    async def close(self):
        """Clean up resources"""
        if self.user_client:
            await self.user_client.close()

async def main():
    """Main test function"""
    try:
        # Create logs directory
        os.makedirs('logs', exist_ok=True)

        logger.info("Loading configuration...")
        config = ConfigManager()

        if not config.get_user_token():
            logger.error("No user token configured. Please update config.yaml")
            return

        logger.info("Starting Enhanced Detection Tests...")

        tester = EnhancedDetectionTester(config)

        if await tester.initialize():
            # Run all tests
            await tester.test_activity_detection_methods()
            await tester.test_count_vs_activity_detection()
            await tester.test_comprehensive_monitoring()

            logger.info("\n" + "="*60)
            logger.info("All Enhanced Detection Tests Completed!")
            logger.info("="*60)
            logger.info("\nCheck the logs above to see:")
            logger.info("1. Which detection methods are working")
            logger.info("2. Whether you're getting real usernames or generic ones")
            logger.info("3. The success rate of real username detection")
            logger.info("\nIf you see mostly 'New Member(s) Online' messages,")
            logger.info("the bot will now prioritize activity-based detection!")

        await tester.close()

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
