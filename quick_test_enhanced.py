#!/usr/bin/env python3
"""
Quick Enhanced Monitoring Verification Script
Tests the new enhanced monitoring system quickly
"""

import asyncio
import logging
import sys
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def quick_test():
    """Quick test of enhanced monitoring"""
    logger.info("🚀 Starting Quick Enhanced Monitoring Test")
    logger.info("=" * 50)

    try:
        # Initialize components
        config = ConfigManager()
        db = DatabaseManager(config.get_database_config()['path'])
        formatter = UserFormatter(config)

        await db.initialize()

        # Test configuration
        interval = config.get_user_monitoring_interval()
        logger.info(f"✅ Monitoring interval: {interval} seconds")

        if interval == 7:
            logger.info("✅ Enhanced 7-second monitoring is active!")
        else:
            logger.warning(f"⚠️ Expected 7 seconds, got {interval}")

        # Initialize user client
        user_client = DiscordUserClient(config, db, formatter, None)

        user_token = config.get_user_token()
        if not user_token:
            logger.error("❌ No user token configured")
            return

        if await user_client.initialize(user_token):
            logger.info("✅ User client initialized successfully")
        else:
            logger.error("❌ Failed to initialize user client")
            return

        # Test guild discovery
        guilds = await user_client.discover_user_guilds()
        logger.info(f"✅ Found {len(guilds)} guilds:")

        problem_servers = ["abu cartel", "inspiredanalyst", "wizards hub", "no limit trades"]

        for guild in guilds:
            guild_name = guild['name']
            guild_id = guild['id']

            is_problem_server = any(server in guild_name.lower() for server in problem_servers)
            status = "🎯 ENHANCED" if is_problem_server else "📋 STANDARD"

            logger.info(f"   {status} - {guild_name} ({guild_id})")

        # Test monitoring methods on one problematic server
        test_guild = None
        for guild in guilds:
            if any(server in guild['name'].lower() for server in problem_servers):
                test_guild = guild
                break

        if test_guild:
            guild_id = test_guild['id']
            guild_name = test_guild['name']

            logger.info(f"🧪 Testing enhanced monitoring on: {guild_name}")

            # Test comprehensive monitoring
            try:
                new_members = await user_client.comprehensive_guild_monitoring(guild_id, guild_name)
                logger.info(f"✅ Enhanced monitoring test completed")
                logger.info(f"   Detected {len(new_members)} new members")

                for member in new_members:
                    source = member.get('monitoring_source', 'unknown')
                    logger.info(f"   - {member['username']} (via {source})")

            except Exception as e:
                logger.error(f"❌ Error testing enhanced monitoring: {e}")

        # Close session
        await user_client.close()

        logger.info("=" * 50)
        logger.info("🎉 Quick test completed!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Start the bot: start_bot.bat")
        logger.info("2. Test with friend joining Abu Cartel")
        logger.info("3. Watch for enhanced logs with 🔍 emojis")
        logger.info("4. Verify notifications are sent")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())
