"""
Test script for the random user notifier
"""

import asyncio
import logging
from src.config_manager import ConfigManager
from src.database_manager import DatabaseManager
from src.user_formatter import UserFormatter
from src.random_user_notifier import RandomUserNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class MockDiscordClient:
    """Mock Discord client for testing"""
    def __init__(self):
        self.logger = logging.getLogger("MockClient")
        self.guilds = [
            MockGuild(1, "Test Server 1"),
            MockGuild(2, "Test Server 2"),
            MockGuild(3, "Test Server 3")
        ]
        
    async def fetch_user(self, user_id):
        """Mock fetch_user method"""
        self.logger.info(f"Fetching user with ID: {user_id}")
        return MockUser(user_id)

class MockGuild:
    """Mock Discord guild for testing"""
    def __init__(self, id, name):
        self.id = id
        self.name = name

class MockUser:
    """Mock Discord user for testing"""
    def __init__(self, id):
        self.id = id
        self.name = f"TestUser_{id}"
        self.logger = logging.getLogger("MockUser")
        
    async def send(self, message):
        """Mock send method"""
        self.logger.info(f"Message sent to user {self.id}: {message}")
        return True

async def test_random_notifier():
    """Test the random user notifier"""
    logger = logging.getLogger("TestRandomNotifier")
    logger.info("Starting random notifier test")
    
    # Create mock components
    config = ConfigManager()
    db = DatabaseManager(":memory:")  # Use in-memory database for testing
    await db.initialize()
    
    formatter = UserFormatter(config)
    mock_client = MockDiscordClient()
    
    # Create random user notifier
    notifier = RandomUserNotifier(mock_client, config, db, formatter)
    
    # Start the notifier
    await notifier.start()
    
    # Let it run for a short time to test
    logger.info("Random notifier started, waiting for notifications...")
    await asyncio.sleep(10)  # Wait for 10 seconds
    
    # Stop the notifier
    await notifier.stop()
    logger.info("Random notifier test completed")

if __name__ == "__main__":
    asyncio.run(test_random_notifier()) 