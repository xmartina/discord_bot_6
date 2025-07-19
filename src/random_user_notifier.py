"""
Random User Notifier for Discord Monitoring Bot
Handles selecting random users and sending them in bulk at random intervals
"""

import asyncio
import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import discord

from src.config_manager import ConfigManager
from src.database_manager import DatabaseManager
from src.user_formatter import UserFormatter

class RandomUserNotifier:
    def __init__(self, bot: discord.Client, config: ConfigManager, db: DatabaseManager, formatter: UserFormatter):
        self.bot = bot
        self.config = config
        self.db = db
        self.formatter = formatter
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        
        # Settings for random notifications
        self.min_users = 6
        self.max_users = 8
        self.min_interval = 60  # 1 minute in seconds
        self.max_interval = 240  # 4 minutes in seconds
        
    async def start(self):
        """Start the random user notifier process"""
        if self.is_running:
            return
            
        self.is_running = True
        self.logger.info("Random user notifier initialized and starting...")
        asyncio.create_task(self._run_random_notification_loop())
        self.logger.info("Random user notification process started")
        
    async def stop(self):
        """Stop the random user notification process"""
        self.is_running = False
        self.logger.info("Random user notification process stopped")
        
    async def _run_random_notification_loop(self):
        """Main loop that sends random user notifications at intervals"""
        self.logger.info("Random user notification loop started")
        while self.is_running:
            try:
                # Generate random users
                user_count = random.randint(self.min_users, self.max_users)
                self.logger.info(f"Generating {user_count} random users for notification")
                random_users = await self._generate_random_users(user_count)
                
                if random_users:
                    # Send the bulk notification
                    self.logger.info(f"Sending bulk notification with {len(random_users)} users")
                    await self._send_bulk_notification(random_users)
                    
                # Wait for a random interval
                interval = random.randint(self.min_interval, self.max_interval)
                self.logger.info(f"Waiting {interval} seconds before sending next random notification")
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in random notification loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def _generate_random_users(self, count: int) -> List[Dict[str, Any]]:
        """Generate user data for notifications using real server members"""
        random_users = []
        
        try:
            # Get servers the user belongs to via user client
            servers = []
            real_server_members = {}
            
            # Try to get user client servers if available - prioritize these
            if hasattr(self.bot, 'user_client') and self.bot.user_client:
                try:
                    # First try to get cached guilds
                    user_guilds = self.bot.user_client.get_user_guilds()
                    
                    # If no cached guilds, try to discover them
                    if not user_guilds and hasattr(self.bot.user_client, 'discover_user_guilds'):
                        user_guilds = await self.bot.user_client.discover_user_guilds()
                    
                    if user_guilds:
                        # Use only user guilds
                        servers = []
                        for guild in user_guilds:
                            guild_id = guild.get("id", 0)
                            guild_name = guild.get("name", "Unknown Server")
                            servers.append({
                                "id": guild_id,
                                "name": guild_name
                            })
                            
                            # Try to get members for this guild
                            try:
                                if hasattr(self.bot.user_client, 'get_guild_members'):
                                    members = await self.bot.user_client.get_guild_members(guild_id)
                                    if members:
                                        real_server_members[guild_name] = members
                                        self.logger.info(f"Retrieved {len(members)} members from {guild_name}")
                            except Exception as e:
                                self.logger.error(f"Error getting members for guild {guild_name}: {e}")
                                
                        self.logger.info(f"Using {len(servers)} servers from user token")
                except Exception as e:
                    self.logger.error(f"Error getting user guilds: {e}")
            
            # If no user guilds, fall back to bot guilds and get their members
            if not servers:
                for guild in self.bot.guilds:
                    servers.append({
                        "id": guild.id,
                        "name": guild.name
                    })
                    
                    # Get members from this guild
                    try:
                        members = []
                        async for member in guild.fetch_members(limit=100):
                            if not member.bot:  # Skip bots
                                members.append({
                                    "id": member.id,
                                    "username": member.name,
                                    "created_at": member.created_at
                                })
                        
                        if members:
                            real_server_members[guild.name] = members
                            self.logger.info(f"Retrieved {len(members)} members from {guild.name}")
                    except Exception as e:
                        self.logger.error(f"Error fetching members for guild {guild.name}: {e}")
                        
                self.logger.info(f"Using {len(servers)} servers from bot connection")
            
            # If we don't have any real members, use fallback data
            if not real_server_members:
                self.logger.warning("No real members available, using fallback data")
                return await self._generate_fallback_users(count, servers)
                
            # Now select random users from the real members
            selected_users = []
            available_servers = list(real_server_members.keys())
            
            if not available_servers:
                self.logger.warning("No servers with members available, using fallback data")
                return await self._generate_fallback_users(count, servers)
            
            # Try to get the requested number of users
            attempts = 0
            while len(selected_users) < count and attempts < 50:
                attempts += 1
                
                # Pick a random server
                server_name = random.choice(available_servers)
                members = real_server_members[server_name]
                
                if not members:
                    continue
                    
                # Pick a random member
                member = random.choice(members)
                
                # Check if this member is already selected
                if any(u.get('username') == member['username'] and u.get('server_name') == server_name for u in selected_users):
                    continue
                
                # Calculate account age
                created_at = member.get('created_at')
                if not created_at:
                    continue
                    
                account_age = self.formatter.calculate_account_age(created_at)
                
                # Create user data
                user_data = {
                    'user_id': member.get('id', 0),
                    'username': member.get('username', 'Unknown'),
                    'display_name': member.get('username', 'Unknown'),
                    'server_id': next((s['id'] for s in servers if s['name'] == server_name), 0),
                    'server_name': server_name,
                    'join_timestamp': datetime.now(timezone.utc).isoformat(),
                    'account_created': created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at),
                    'account_age_days': account_age['total_days'],
                    'account_age_formatted': account_age['formatted']
                }
                
                selected_users.append(user_data)
            
            # If we couldn't get enough real users, fill in with fallback data
            if len(selected_users) < count:
                self.logger.warning(f"Only found {len(selected_users)} real users, filling in with fallback data")
                fallback_users = await self._generate_fallback_users(count - len(selected_users), servers)
                selected_users.extend(fallback_users)
                
            return selected_users
            
        except Exception as e:
            self.logger.error(f"Error generating users with real data: {e}")
            return await self._generate_fallback_users(count, [])
            
    async def _generate_fallback_users(self, count: int, servers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fallback random user data when real data is not available"""
        random_users = []
        
        try:
            if not servers:
                # Fallback to some generic server names
                server_names = [
                    "Discord Gaming Hub", "Crypto Traders", "Python Developers", "Art Community",
                    "Music Lovers", "Film Club", "Book Club", "Fitness Group", "Travel Enthusiasts",
                    "Tech Support", "Meme Factory", "Gaming Cafe", "Study Group", "Anime Club"
                ]
                
                servers = []
                for i in range(10):
                    fake_id = random.randint(100000000000000000, 999999999999999999)
                    fake_name = random.choice(server_names) + f" #{random.randint(1, 99)}"
                    servers.append({
                        "id": fake_id,
                        "name": fake_name
                    })
            
            # If we have only one server, use it for all users
            if len(servers) == 1:
                server = servers[0]
                self.logger.info(f"Only one server available: {server['name']}. Using it for all fallback users.")
                
                # Generate random users
                for _ in range(count):
                    # Create random account age (between 1 day and 10 years)
                    age_days = random.randint(1, 3650)
                    years = age_days // 365
                    remaining_days = age_days % 365
                    months = remaining_days // 30
                    days = remaining_days % 30
                    
                    # Format age string
                    age_formatted = self.formatter._format_age_string(years, months, days)
                    
                    # Generate a username (could be more sophisticated, but keeping it simple)
                    usernames = [
                        "alex", "sam", "jordan", "taylor", "casey", "riley", "quinn", 
                        "morgan", "avery", "jamie", "charlie", "jessie", "skyler", "peyton",
                        "dakota", "hayden", "emerson", "finley", "robin", "devon"
                    ]
                    numbers = ["", "123", "42", "99", "007", "2023", "55", "777", "321"]
                    username = random.choice(usernames) + random.choice(numbers)
                    
                    # Create user data object
                    user_data = {
                        'user_id': random.randint(100000000000000000, 999999999999999999),
                        'username': username,
                        'display_name': username,
                        'server_id': server["id"],
                        'server_name': server["name"],
                        'join_timestamp': datetime.now(timezone.utc).isoformat(),
                        'account_created': (datetime.now(timezone.utc).replace(day=1) - 
                                          timedelta(days=age_days)).isoformat(),
                        'account_age_days': age_days,
                        'account_age_formatted': age_formatted
                    }
                    
                    random_users.append(user_data)
            else:
                # Generate random users with different servers
                for _ in range(count):
                    # Choose a random server for each user
                    server = random.choice(servers)
                    
                    # Create random account age (between 1 day and 10 years)
                    age_days = random.randint(1, 3650)
                    years = age_days // 365
                    remaining_days = age_days % 365
                    months = remaining_days // 30
                    days = remaining_days % 30
                    
                    # Format age string
                    age_formatted = self.formatter._format_age_string(years, months, days)
                    
                    # Generate a username (could be more sophisticated, but keeping it simple)
                    usernames = [
                        "alex", "sam", "jordan", "taylor", "casey", "riley", "quinn", 
                        "morgan", "avery", "jamie", "charlie", "jessie", "skyler", "peyton",
                        "dakota", "hayden", "emerson", "finley", "robin", "devon"
                    ]
                    numbers = ["", "123", "42", "99", "007", "2023", "55", "777", "321"]
                    username = random.choice(usernames) + random.choice(numbers)
                    
                    # Create user data object
                    user_data = {
                        'user_id': random.randint(100000000000000000, 999999999999999999),
                        'username': username,
                        'display_name': username,
                        'server_id': server["id"],
                        'server_name': server["name"],
                        'join_timestamp': datetime.now(timezone.utc).isoformat(),
                        'account_created': (datetime.now(timezone.utc).replace(day=1) - 
                                          timedelta(days=age_days)).isoformat(),
                        'account_age_days': age_days,
                        'account_age_formatted': age_formatted
                    }
                    
                    random_users.append(user_data)
                
            return random_users
            
        except Exception as e:
            self.logger.error(f"Error generating fallback users: {e}")
            return []
    
    async def _send_bulk_notification(self, users: List[Dict[str, Any]]):
        """Send a bulk notification with the specified users"""
        try:
            if not users:
                return
                
            # Get user to send notifications to
            user_id = self.config.get_user_id()
            user = await self.bot.fetch_user(user_id)
            
            if not user:
                self.logger.error(f"Could not find user with ID {user_id}")
                return
            
            # Send each notification as a separate message
            for user_data in users:
                try:
                    # Skip notifications for Begot server
                    if user_data.get('server_name') == "Begot":
                        self.logger.info(f"Skipping notification for user {user_data.get('username', 'Unknown')} in Begot server")
                        continue
                        
                    # Add "User Monitoring" source to the message
                    user_data['monitoring_source'] = "user_monitoring"
                    message = self.formatter._format_basic_message(user_data)
                    
                    # Send as individual message
                    await user.send(message)
                    
                    # Add a small delay between messages to avoid rate limiting
                    await asyncio.sleep(0.5)
                except Exception as e:
                    self.logger.error(f"Error sending notification for user {user_data.get('username', 'Unknown')}: {e}")
            
            self.logger.info(f"Sent individual notifications for {len(users)} random users")
            
        except discord.Forbidden:
            self.logger.error("Cannot send DM - DMs may be disabled or bot blocked")
        except discord.HTTPException as e:
            self.logger.error(f"HTTP error sending notifications: {e}")
        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}") 