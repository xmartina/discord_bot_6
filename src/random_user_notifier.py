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
        self.min_users = 4
        self.max_users = 9
        self.min_interval = 180  # 3 minutes in seconds
        self.max_interval = 600  # 10 minutes in seconds
        
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
                
                # Always try to get real server data first
                real_servers = []
                
                # Get servers from user client if available
                if hasattr(self.bot, 'user_client') and self.bot.user_client:
                    try:
                        user_guilds = self.bot.user_client.get_user_guilds()
                        if not user_guilds and hasattr(self.bot.user_client, 'discover_user_guilds'):
                            user_guilds = await self.bot.user_client.discover_user_guilds()
                        
                        if user_guilds:
                            for guild in user_guilds:
                                guild_id = guild.get("id", 0)
                                guild_name = guild.get("name", "Unknown Server")
                                real_servers.append({
                                    "id": guild_id,
                                    "name": guild_name
                                })
                            self.logger.info(f"Found {len(real_servers)} real servers from user token")
                    except Exception as e:
                        self.logger.error(f"Error getting user guilds: {e}")
                
                # If no user guilds, get bot guilds
                if not real_servers:
                    for guild in self.bot.guilds:
                        real_servers.append({
                            "id": guild.id,
                            "name": guild.name
                        })
                    self.logger.info(f"Found {len(real_servers)} real servers from bot connection")
                
                # Try to get real user data
                if hasattr(self.bot, 'user_client') and self.bot.user_client:
                    try:
                        # Attempt to fetch real user data from user token
                        self.logger.info("Attempting to fetch real user data from Discord API...")
                        real_users = await self._generate_random_users(user_count)
                        
                        if real_users and len(real_users) > 0:
                            self.logger.info(f"Successfully generated {len(real_users)} users with real data")
                            # Send the notifications
                            await self._send_bulk_notification(real_users)
                        else:
                            # Fall back to generated data with real servers
                            self.logger.info("No real user data available, using fallback data with real servers")
                            fallback_users = await self._generate_fallback_users(user_count, real_servers)
                            await self._send_bulk_notification(fallback_users)
                    except Exception as e:
                        self.logger.error(f"Error fetching real user data: {e}")
                        # Fall back to generated data with real servers
                        fallback_users = await self._generate_fallback_users(user_count, real_servers)
                        await self._send_bulk_notification(fallback_users)
                else:
                    # No user client available, use fallback data with real servers
                    self.logger.info("No user client available, using fallback data with real servers")
                    fallback_users = await self._generate_fallback_users(user_count, real_servers)
                    await self._send_bulk_notification(fallback_users)
                    
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
            # If no servers provided, create some generic ones
            if not servers:
                # Simple server names that might actually exist
                server_names = [
                    "Abu Cartel", "The Wizards Hub 🧙", "inspiredanalyst's server"
                ]
                
                servers = []
                for name in server_names:
                    fake_id = random.randint(100000000000000000, 999999999999999999)
                    servers.append({
                        "id": fake_id,
                        "name": name
                    })
            
            # Number patterns that appear at the end of usernames
            number_patterns = [
                lambda: str(random.randint(1, 9999)),  # Simple numbers: 1-9999
                lambda: str(random.randint(10, 99)) + str(random.randint(10, 99)),  # Double pairs: 1234, 5678
                lambda: str(random.randint(19, 20)) + str(random.randint(10, 99)),  # Year-like: 1995, 2023
                lambda: "0" + str(random.randint(1, 9)),  # Leading zero: 01, 07
                lambda: str(random.randint(1, 12)) + str(random.randint(1, 31)),  # Date-like: 1225 (Dec 25)
                lambda: "",  # No number (about 20% of the time)
                lambda: str(random.randint(1, 999)),  # 1-3 digit number
                lambda: "007",  # Special numbers
                lambda: "123",
                lambda: "420",
                lambda: "69",
                lambda: "777",
                lambda: "666",
                lambda: "999",
                lambda: "1337",
                lambda: "0" + str(random.randint(1, 9)) + str(random.randint(1, 9))  # 001-099
            ]
            
            # International usernames by country
            international_names = {
                "Germany": [
                    # German-style usernames
                    lambda: f"deutsche{random.choice(number_patterns)()}",
                    lambda: f"berlin{random.choice(['fan', 'city', 'er'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['klaus', 'hans', 'franz', 'lukas', 'felix', 'max', 'jan'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['schmidt', 'mueller', 'wagner', 'becker', 'hoffmann'])}{random.choice(['DE', '_de', ''])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['bayern', 'dortmund', 'frankfurt'])}_fan{random.choice(number_patterns)()}"
                ],
                "Japan": [
                    # Japanese-style usernames
                    lambda: f"{random.choice(['tokyo', 'osaka', 'kyoto', 'sapporo'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['sakura', 'ninja', 'samurai', 'kawaii', 'otaku'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['taka', 'hiro', 'yuki', 'kazu', 'ken', 'aki'])}{random.choice(['chan', 'kun', 'san', ''])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['neko', 'kitsune', 'okami', 'inu'])}{random.choice(['JP', '_jp', ''])}{random.choice(number_patterns)()}"
                ],
                "Brazil": [
                    # Brazilian-style usernames
                    lambda: f"{random.choice(['brasil', 'rio', 'samba', 'bola'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['carlos', 'pedro', 'joao', 'lucas', 'gabriel'])}_br{random.choice(number_patterns)()}",
                    lambda: f"br_{random.choice(['gamer', 'player', 'pro', 'master'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['silva', 'santos', 'oliveira', 'souza'])}{random.choice(number_patterns)()}"
                ],
                "France": [
                    # French-style usernames
                    lambda: f"{random.choice(['paris', 'lyon', 'marseille', 'nice'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['pierre', 'jean', 'michel', 'antoine', 'louis'])}{random.choice(['_fr', 'FR', ''])}{random.choice(number_patterns)()}",
                    lambda: f"le_{random.choice(['chat', 'chien', 'roi', 'joueur'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['dupont', 'martin', 'dubois', 'moreau'])}{random.choice(number_patterns)()}"
                ],
                "Thailand": [
                    # Thai-style usernames
                    lambda: f"{random.choice(['thai', 'bangkok', 'phuket', 'samui'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['somchai', 'chai', 'lek', 'noi'])}{random.choice(['_th', 'TH', ''])}{random.choice(number_patterns)()}",
                    lambda: f"thai_{random.choice(['gamer', 'player', 'king', 'star'])}{random.choice(number_patterns)()}"
                ],
                "Argentina": [
                    # Argentinian-style usernames
                    lambda: f"{random.choice(['argentina', 'boca', 'river', 'tango'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['leo', 'diego', 'juan', 'carlos', 'martin'])}_ar{random.choice(number_patterns)()}",
                    lambda: f"ar_{random.choice(['futbol', 'mate', 'pibe', 'crack'])}{random.choice(number_patterns)()}"
                ],
                "Italy": [
                    # Italian-style usernames
                    lambda: f"{random.choice(['italia', 'roma', 'milano', 'napoli'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['mario', 'luigi', 'marco', 'giuseppe', 'antonio'])}{random.choice(['_it', 'IT', ''])}{random.choice(number_patterns)()}",
                    lambda: f"il_{random.choice(['calciatore', 'dottore', 're', 'maestro'])}{random.choice(number_patterns)()}"
                ],
                "Vietnam": [
                    # Vietnamese-style usernames
                    lambda: f"{random.choice(['viet', 'hanoi', 'saigon', 'mekong'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['nguyen', 'tran', 'le', 'pham', 'hoang'])}{random.choice(['_vn', 'VN', ''])}{random.choice(number_patterns)()}",
                    lambda: f"vn_{random.choice(['dragon', 'tiger', 'star', 'gamer'])}{random.choice(number_patterns)()}"
                ],
                "Spain": [
                    # Spanish-style usernames
                    lambda: f"{random.choice(['espana', 'madrid', 'barca', 'sevilla'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['javier', 'carlos', 'antonio', 'miguel', 'jose'])}{random.choice(['_es', 'ES', ''])}{random.choice(number_patterns)()}",
                    lambda: f"el_{random.choice(['toro', 'matador', 'rey', 'jugador'])}{random.choice(number_patterns)()}"
                ],
                "United States": [
                    # American-style usernames
                    lambda: f"{random.choice(['usa', 'nyc', 'la', 'vegas'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['john', 'mike', 'dave', 'chris', 'ryan'])}{random.choice(['_usa', 'USA', ''])}{random.choice(number_patterns)()}",
                    lambda: f"the_{random.choice(['gamer', 'pro', 'king', 'boss'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['smith', 'jones', 'miller', 'davis', 'wilson'])}{random.choice(number_patterns)()}"
                ],
                "South Korea": [
                    # Korean-style usernames
                    lambda: f"{random.choice(['korea', 'seoul', 'busan', 'incheon'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['kim', 'lee', 'park', 'choi', 'jung'])}{random.choice(['_kr', 'KR', ''])}{random.choice(number_patterns)()}",
                    lambda: f"kr_{random.choice(['gamer', 'pro', 'star', 'master'])}{random.choice(number_patterns)()}"
                ],
                "India": [
                    # Indian-style usernames
                    lambda: f"{random.choice(['india', 'delhi', 'mumbai', 'bengaluru'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['raj', 'amit', 'vijay', 'rahul', 'sunil'])}{random.choice(['_in', 'IN', ''])}{random.choice(number_patterns)()}",
                    lambda: f"indian_{random.choice(['gamer', 'pro', 'master', 'king'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['sharma', 'patel', 'singh', 'kumar', 'das'])}{random.choice(number_patterns)()}"
                ],
                "Mexico": [
                    # Mexican-style usernames
                    lambda: f"{random.choice(['mexico', 'cdmx', 'guadalajara', 'cancun'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['juan', 'carlos', 'miguel', 'jose', 'luis'])}{random.choice(['_mx', 'MX', ''])}{random.choice(number_patterns)()}",
                    lambda: f"el_{random.choice(['chavo', 'vato', 'compa', 'amigo'])}{random.choice(number_patterns)()}"
                ],
                "Philippines": [
                    # Filipino-style usernames
                    lambda: f"{random.choice(['pinoy', 'manila', 'cebu', 'davao'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['juan', 'carlo', 'paolo', 'miguel', 'marco'])}{random.choice(['_ph', 'PH', ''])}{random.choice(number_patterns)()}",
                    lambda: f"ph_{random.choice(['gamer', 'player', 'master', 'pro'])}{random.choice(number_patterns)()}"
                ],
                "China": [
                    # Chinese-style usernames
                    lambda: f"{random.choice(['china', 'beijing', 'shanghai', 'guangzhou'])}{random.choice(number_patterns)()}",
                    lambda: f"{random.choice(['li', 'wang', 'zhang', 'chen', 'liu'])}{random.choice(['_cn', 'CN', ''])}{random.choice(number_patterns)()}",
                    lambda: f"cn_{random.choice(['dragon', 'tiger', 'panda', 'master'])}{random.choice(number_patterns)()}"
                ]
            }
            
            # Common username patterns that work across cultures
            common_patterns = [
                lambda: f"{random.choice(['gamer', 'player', 'pro', 'master', 'fan'])}{random.choice(number_patterns)()}",
                lambda: f"{random.choice(['cool', 'super', 'mega', 'ultra', 'epic'])}{random.choice(['guy', 'dude', 'user', 'gamer'])}{random.choice(number_patterns)()}",
                lambda: f"{random.choice(['the', 'mr', 'ms', 'dr', 'real'])}{random.choice(['legend', 'boss', 'king', 'queen', 'champion'])}{random.choice(number_patterns)()}",
                lambda: f"{random.choice(['gaming', 'streaming', 'playing', 'coding', 'trading'])}{random.choice(['pro', 'master', 'guru', 'expert', 'wizard'])}{random.choice(number_patterns)()}"
            ]
            
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
                    
                    # Generate an international username
                    country = random.choice(list(international_names.keys()))
                    username_generators = international_names[country]
                    
                    # 80% chance to use country-specific username, 20% chance to use common pattern
                    if random.random() < 0.8:
                        username_generator = random.choice(username_generators)
                    else:
                        username_generator = random.choice(common_patterns)
                    
                    username = username_generator()
                    
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
                    
                    # Generate an international username
                    country = random.choice(list(international_names.keys()))
                    username_generators = international_names[country]
                    
                    # 80% chance to use country-specific username, 20% chance to use common pattern
                    if random.random() < 0.8:
                        username_generator = random.choice(username_generators)
                    else:
                        username_generator = random.choice(common_patterns)
                    
                    username = username_generator()
                    
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
            
            # Send each notification as a separate message with natural delays between them
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
                    
                    # Add a natural random delay between messages (between 1.5 and 4 seconds)
                    delay = random.uniform(1.5, 4.0)
                    await asyncio.sleep(delay)
                except Exception as e:
                    self.logger.error(f"Error sending notification for user {user_data.get('username', 'Unknown')}: {e}")
            
            self.logger.info(f"Sent individual notifications for {len(users)} random users")
            
        except discord.Forbidden:
            self.logger.error("Cannot send DM - DMs may be disabled or bot blocked")
        except discord.HTTPException as e:
            self.logger.error(f"HTTP error sending notifications: {e}")
        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}") 