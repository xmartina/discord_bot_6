#!/usr/bin/env python3
"""
Enhanced Monitoring Test Script
Tests the new 7-second monitoring and Abu Cartel detection features
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config_manager import ConfigManager
from src.user_client import DiscordUserClient
from src.database_manager import DatabaseManager
from src.user_formatter import UserFormatter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/enhanced_monitoring_test.log')
    ]
)

logger = logging.getLogger(__name__)

class EnhancedMonitoringTest:
    def __init__(self):
        self.config = ConfigManager()
        self.db = DatabaseManager(self.config.get_database_config()['path'])
        self.formatter = UserFormatter(self.config)
        self.user_client = None
        self.test_results = []

    async def setup(self):
        """Setup test environment"""
        logger.info("🔧 Setting up enhanced monitoring test...")

        # Initialize database
        await self.db.initialize()

        # Create directories
        self.config.create_directories()

        # Initialize user client
        self.user_client = DiscordUserClient(
            self.config,
            self.db,
            self.formatter,
            self._test_callback
        )

        # Initialize user client
        user_token = self.config.get_user_token()
        if not user_token:
            raise ValueError("User token not configured - cannot test user monitoring")

        if not await self.user_client.initialize(user_token):
            raise ValueError("Failed to initialize user client")

        logger.info("✅ Setup completed successfully")

    async def _test_callback(self, user_data: dict, source: str = "test"):
        """Test callback for new member notifications"""
        logger.info(f"🔔 TEST CALLBACK: New member detected via {source}")
        logger.info(f"   User: {user_data['username']} in {user_data['server_name']}")
        logger.info(f"   User ID: {user_data['user_id']}")
        logger.info(f"   Source: {user_data.get('monitoring_source', 'unknown')}")

        self.test_results.append({
            'timestamp': datetime.now(timezone.utc),
            'user_data': user_data,
            'source': source
        })

    async def test_configuration(self):
        """Test new configuration values"""
        logger.info("🧪 Testing configuration...")

        # Test monitoring interval
        interval = self.config.get_user_monitoring_interval()
        logger.info(f"   Monitoring interval: {interval} seconds")

        if interval == 7:
            logger.info("   ✅ Monitoring interval correctly set to 7 seconds")
        else:
            logger.warning(f"   ⚠️ Expected 7 seconds, got {interval} seconds")

        # Test other settings
        logger.info(f"   User monitoring enabled: {self.config.is_user_monitoring_enabled()}")
        logger.info(f"   Monitor user servers: {self.config.should_monitor_user_servers()}")

        logger.info("✅ Configuration test completed")

    async def test_guild_discovery(self):
        """Test guild discovery and Abu Cartel detection"""
        logger.info("🔍 Testing guild discovery...")

        guilds = await self.user_client.discover_user_guilds()
        logger.info(f"   Found {len(guilds)} guilds")

        abu_cartel_found = False
        for guild in guilds:
            guild_name = guild['name']
            guild_id = guild['id']
            logger.info(f"   - {guild_name} ({guild_id})")

            if "abu cartel" in guild_name.lower():
                abu_cartel_found = True
                logger.info(f"   🎯 ABU CARTEL FOUND: {guild_name}")

        if abu_cartel_found:
            logger.info("   ✅ Abu Cartel successfully discovered")
        else:
            logger.warning("   ⚠️ Abu Cartel not found in guild list")

        logger.info("✅ Guild discovery test completed")

    async def test_abu_cartel_monitoring(self):
        """Test Abu Cartel specific monitoring"""
        logger.info("🎯 Testing Abu Cartel monitoring...")

        guilds = await self.user_client.discover_user_guilds()
        abu_cartel_guild = None

        for guild in guilds:
            if "abu cartel" in guild['name'].lower():
                abu_cartel_guild = guild
                break

        if not abu_cartel_guild:
            logger.warning("   ⚠️ Abu Cartel not found - skipping specific test")
            return

        guild_id = abu_cartel_guild['id']
        guild_name = abu_cartel_guild['name']

        logger.info(f"   Testing monitoring for: {guild_name} ({guild_id})")

        # Test guild info retrieval
        guild_info = await self.user_client.get_guild_info(guild_id)
        if guild_info:
            logger.info(f"   ✅ Guild info retrieved successfully")
            logger.info(f"   Available fields: {list(guild_info.keys())}")
        else:
            logger.warning(f"   ⚠️ Could not retrieve guild info")

        # Test channel access
        channels = await self.user_client.get_guild_channels(guild_id)
        if channels:
            logger.info(f"   ✅ Found {len(channels)} accessible channels")
            for i, channel in enumerate(channels[:5]):  # Show first 5
                logger.info(f"     - Channel {i+1}: {channel.get('name', 'Unknown')} (ID: {channel['id']})")
        else:
            logger.warning(f"   ⚠️ No accessible channels found")

        # Test member monitoring
        logger.info("   Testing member monitoring...")
        new_members = await self.user_client.monitor_guild_for_new_members(guild_id, guild_name)
        logger.info(f"   New members detected: {len(new_members)}")

        for member in new_members:
            logger.info(f"     - {member['username']} (source: {member.get('monitoring_source', 'unknown')})")

        logger.info("✅ Abu Cartel monitoring test completed")

    async def test_monitoring_cycle(self, cycles: int = 3):
        """Test the monitoring cycle"""
        logger.info(f"🔄 Testing monitoring cycle ({cycles} cycles)...")

        initial_results = len(self.test_results)

        # Run a few monitoring cycles
        for cycle in range(cycles):
            logger.info(f"   Cycle {cycle + 1}/{cycles}")

            # Get guilds
            guilds = await self.user_client.discover_user_guilds()

            # Monitor each guild
            for guild in guilds:
                guild_id = guild['id']
                guild_name = guild['name']

                # Skip excluded servers
                if int(guild_id) in self.config.get_excluded_servers():
                    continue

                try:
                    new_members = await self.user_client.monitor_guild_for_new_members(guild_id, guild_name)

                    for member_data in new_members:
                        if self.formatter.should_notify(member_data):
                            await self._test_callback(member_data, "test_cycle")

                except Exception as e:
                    logger.error(f"   Error monitoring {guild_name}: {e}")

            # Wait 7 seconds between cycles
            if cycle < cycles - 1:
                logger.info("   Waiting 7 seconds...")
                await asyncio.sleep(7)

        new_results = len(self.test_results) - initial_results
        logger.info(f"   Detected {new_results} new members during test")

        logger.info("✅ Monitoring cycle test completed")

    async def test_alternative_monitoring(self):
        """Test alternative monitoring methods"""
        logger.info("🔀 Testing alternative monitoring methods...")

        guilds = await self.user_client.discover_user_guilds()

        for guild in guilds:
            guild_id = guild['id']
            guild_name = guild['name']

            logger.info(f"   Testing alternative monitoring for: {guild_name}")

            # Test the alternative monitoring method directly
            try:
                new_members = await self.user_client._try_alternative_monitoring(guild_id, guild_name)
                logger.info(f"     Alternative monitoring result: {len(new_members)} members")

                for member in new_members:
                    logger.info(f"       - {member['username']} (source: {member.get('monitoring_source', 'unknown')})")

            except Exception as e:
                logger.error(f"     Error in alternative monitoring: {e}")

        logger.info("✅ Alternative monitoring test completed")

    async def run_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting Enhanced Monitoring Test Suite")
        logger.info("=" * 50)

        try:
            await self.setup()

            # Run individual tests
            await self.test_configuration()
            await self.test_guild_discovery()
            await self.test_abu_cartel_monitoring()
            await self.test_alternative_monitoring()
            await self.test_monitoring_cycle(cycles=3)

            # Summary
            logger.info("=" * 50)
            logger.info("🎉 Test Suite Completed")
            logger.info(f"Total detections during test: {len(self.test_results)}")

            if self.test_results:
                logger.info("Detection summary:")
                for result in self.test_results:
                    user_data = result['user_data']
                    logger.info(f"  - {user_data['username']} in {user_data['server_name']} (via {result['source']})")

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            raise
        finally:
            if self.user_client:
                await self.user_client.close()

    async def run_live_monitoring(self, duration_minutes: int = 5):
        """Run live monitoring for specified duration"""
        logger.info(f"🔴 Starting live monitoring for {duration_minutes} minutes...")
        logger.info("This will run the actual monitoring loop - watch for Abu Cartel detections!")

        try:
            await self.setup()

            # Start monitoring
            end_time = datetime.now(timezone.utc).timestamp() + (duration_minutes * 60)

            while datetime.now(timezone.utc).timestamp() < end_time:
                remaining = int(end_time - datetime.now(timezone.utc).timestamp())
                logger.info(f"⏱️ Live monitoring... {remaining} seconds remaining")

                # Run one monitoring cycle
                guilds = await self.user_client.discover_user_guilds()

                for guild in guilds:
                    guild_id = guild['id']
                    guild_name = guild['name']

                    if int(guild_id) in self.config.get_excluded_servers():
                        continue

                    try:
                        new_members = await self.user_client.monitor_guild_for_new_members(guild_id, guild_name)

                        for member_data in new_members:
                            if self.formatter.should_notify(member_data):
                                await self._test_callback(member_data, "live_monitoring")

                    except Exception as e:
                        logger.error(f"Error monitoring {guild_name}: {e}")

                # Wait 7 seconds
                await asyncio.sleep(7)

            logger.info("🔴 Live monitoring completed")

        except Exception as e:
            logger.error(f"❌ Live monitoring failed: {e}")
            raise
        finally:
            if self.user_client:
                await self.user_client.close()

async def main():
    """Main test function"""
    test_suite = EnhancedMonitoringTest()

    if len(sys.argv) > 1 and sys.argv[1] == "live":
        # Run live monitoring
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        await test_suite.run_live_monitoring(duration)
    else:
        # Run test suite
        await test_suite.run_tests()

if __name__ == "__main__":
    asyncio.run(main())
