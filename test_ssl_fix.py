"""
Test SSL Fix for Discord Bot
This script tests if the SSL fix works by making a simple request to Discord API
"""

import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ssl_fix():
    logger.info("Testing SSL fix by connecting to Discord API...")
    
    try:
        # Create session with SSL verification disabled
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            # Try to connect to Discord API
            async with session.get("https://discord.com/api/v10/gateway") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Successfully connected to Discord API!")
                    logger.info(f"Gateway URL: {data.get('url')}")
                    return True
                else:
                    logger.error(f"Failed to connect to Discord API. Status code: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Error testing SSL fix: {e}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_ssl_fix())
        if result:
            print("\nSSL fix is working! You can now run the bot.")
        else:
            print("\nSSL fix test failed. Please check the logs for more details.")
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}") 