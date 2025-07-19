#!/usr/bin/env python3
"""
Rate Limiting Test Script for Discord Bot
Tests API rate limiting and helps debug connection issues
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timezone
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config_manager import ConfigManager

# Set up logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/rate_limit_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class RateLimitTester:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.user_token = config.get_user_token()
        self.session = None
        self.api_base = "https://discord.com/api/v9"
        self.last_api_call = 0
        self.rate_limit_buffer = 2.0  # 2 seconds between calls

    async def initialize(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': self.user_token,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            connector=connector
        )

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

    async def _rate_limit_check(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_api_call

        if time_since_last < self.rate_limit_buffer:
            sleep_time = self.rate_limit_buffer - time_since_last
            logger.info(f"Rate limiting: waiting {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)

        self.last_api_call = time.time()

    async def test_user_info(self):
        """Test getting user information"""
        logger.info("Testing user info API call...")
        try:
            await self._rate_limit_check()
            async with self.session.get(f"{self.api_base}/users/@me") as response:
                logger.info(f"User info status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"User: {data.get('username', 'Unknown')}#{data.get('discriminator', '0000')}")
                    return True
                elif response.status == 429:
                    retry_after = response.headers.get('Retry-After', '5')
                    logger.warning(f"Rate limited! Retry after: {retry_after} seconds")
                    return False
                else:
                    logger.error(f"Failed to get user info: {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text}")
                    return False
        except Exception as e:
            logger.error(f"Exception getting user info: {e}")
            return False

    async def test_guilds_list(self):
        """Test getting guilds list"""
        logger.info("Testing guilds list API call...")
        try:
            await self._rate_limit_check()
            async with self.session.get(f"{self.api_base}/users/@me/guilds") as response:
                logger.info(f"Guilds list status: {response.status}")
                if response.status == 200:
                    guilds = await response.json()
                    logger.info(f"Found {len(guilds)} guilds")
                    for guild in guilds[:3]:  # Show first 3 guilds
                        logger.info(f"  - {guild.get('name', 'Unknown')} (ID: {guild.get('id', 'Unknown')})")
                    return guilds
                elif response.status == 429:
                    retry_after = response.headers.get('Retry-After', '5')
                    logger.warning(f"Rate limited! Retry after: {retry_after} seconds")
                    return []
                else:
                    logger.error(f"Failed to get guilds: {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text}")
                    return []
        except Exception as e:
            logger.error(f"Exception getting guilds: {e}")
            return []

    async def test_guild_info(self, guild_id: str, guild_name: str):
        """Test getting specific guild information"""
        logger.info(f"Testing guild info for {guild_name} (ID: {guild_id})...")
        try:
            await self._rate_limit_check()
            async with self.session.get(f"{self.api_base}/guilds/{guild_id}?with_counts=true") as response:
                logger.info(f"Guild info status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    member_count = data.get('approximate_member_count', 'Unknown')
                    online_count = data.get('approximate_presence_count', 'Unknown')
                    logger.info(f"  Members: {member_count}, Online: {online_count}")
                    return data
                elif response.status == 429:
                    retry_after = response.headers.get('Retry-After', '5')
                    logger.warning(f"Rate limited! Retry after: {retry_after} seconds")
                    return None
                elif response.status == 403:
                    logger.warning(f"Access denied to guild {guild_name} - this is normal for some servers")
                    return None
                else:
                    logger.error(f"Failed to get guild info: {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text}")
                    return None
        except Exception as e:
            logger.error(f"Exception getting guild info: {e}")
            return None

    async def test_guild_members(self, guild_id: str, guild_name: str, limit: int = 10):
        """Test getting guild members"""
        logger.info(f"Testing guild members for {guild_name} (limit: {limit})...")
        try:
            await self._rate_limit_check()
            async with self.session.get(f"{self.api_base}/guilds/{guild_id}/members?limit={limit}") as response:
                logger.info(f"Guild members status: {response.status}")
                if response.status == 200:
                    members = await response.json()
                    logger.info(f"  Found {len(members)} members")
                    for member in members[:3]:  # Show first 3 members
                        user = member.get('user', {})
                        username = user.get('username', 'Unknown')
                        joined_at = member.get('joined_at', 'Unknown')
                        logger.info(f"    - {username} (joined: {joined_at})")
                    return members
                elif response.status == 429:
                    retry_after = response.headers.get('Retry-After', '5')
                    logger.warning(f"Rate limited! Retry after: {retry_after} seconds")
                    return []
                elif response.status == 403:
                    logger.warning(f"Access denied to members of {guild_name} - need higher permissions")
                    return []
                else:
                    logger.error(f"Failed to get guild members: {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text}")
                    return []
        except Exception as e:
            logger.error(f"Exception getting guild members: {e}")
            return []

    async def run_comprehensive_test(self):
        """Run comprehensive rate limiting tests"""
        logger.info("="*60)
        logger.info("Starting Comprehensive Rate Limiting Test")
        logger.info("="*60)

        # Test 1: User info
        logger.info("\n" + "-"*40)
        logger.info("TEST 1: User Information")
        logger.info("-"*40)
        success = await self.test_user_info()
        if not success:
            logger.error("User info test failed - check your user token")
            return False

        # Test 2: Guilds list
        logger.info("\n" + "-"*40)
        logger.info("TEST 2: Guilds List")
        logger.info("-"*40)
        guilds = await self.test_guilds_list()
        if not guilds:
            logger.error("Guilds list test failed")
            return False

        # Test 3: Guild info for first few guilds
        logger.info("\n" + "-"*40)
        logger.info("TEST 3: Guild Information")
        logger.info("-"*40)
        for guild in guilds[:3]:
            guild_id = guild.get('id')
            guild_name = guild.get('name', 'Unknown')
            await self.test_guild_info(guild_id, guild_name)

        # Test 4: Guild members for first guild
        logger.info("\n" + "-"*40)
        logger.info("TEST 4: Guild Members")
        logger.info("-"*40)
        if guilds:
            first_guild = guilds[0]
            await self.test_guild_members(first_guild.get('id'), first_guild.get('name', 'Unknown'))

        logger.info("\n" + "="*60)
        logger.info("Rate Limiting Test Completed Successfully!")
        logger.info("="*60)
        return True

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

        tester = RateLimitTester(config)
        await tester.initialize()

        try:
            await tester.run_comprehensive_test()
        finally:
            await tester.close()

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
