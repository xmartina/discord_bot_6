"""
Enhanced User Client for Discord Monitoring Bot
Handles user token authentication to monitor servers with multiple robust detection methods
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
import aiohttp
import json

from src.config_manager import ConfigManager
from src.database_manager import DatabaseManager
from src.user_formatter import UserFormatter

class DiscordUserClient:
    """
    Enhanced Discord User Client for monitoring servers where you're a member
    but the bot isn't invited. Uses multiple detection methods for maximum reliability.
    """

    def __init__(self, config: ConfigManager, db: DatabaseManager, formatter: UserFormatter,
                 new_member_callback: Optional[Callable] = None):
        self.config = config
        self.db = db
        self.formatter = formatter
        self.new_member_callback = new_member_callback
        self.logger = logging.getLogger(__name__)

        # User client state
        self.user_token = None
        self.session = None
        self.user_info = None
        self.monitored_guilds = set()
        self.last_member_check = {}
        self.guild_snapshots = {}
        self.detection_methods = {}

        # Rate limiting
        self.last_api_call = 0
        self.rate_limit_delay = self.config.get('performance.rate_limit_buffer', 1.0)

        # API endpoints
        self.api_base = "https://discord.com/api/v10"

    async def initialize(self, user_token: str):
        """Initialize user client with user token"""
        self.user_token = user_token

        # Create aiohttp session with proper headers and SSL verification disabled
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': user_token,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            connector=connector
        )

        # Verify token
        if await self._verify_token():
            self.logger.info(f"User client initialized for {self.user_info.get('username', 'Unknown')}")
            return True
        else:
            self.logger.error("Failed to verify user token")
            return False

    async def _rate_limit_check(self):
        """Ensure we don't exceed rate limits"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_api_call

        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_api_call = asyncio.get_event_loop().time()

    async def _verify_token(self):
        """Verify user token and get user info"""
        try:
            await self._rate_limit_check()
            async with self.session.get(f"{self.api_base}/users/@me") as response:
                if response.status == 200:
                    self.user_info = await response.json()
                    return True
                else:
                    self.logger.error(f"Token verification failed: {response.status}")
                    return False
        except Exception as e:
            self.logger.error(f"Error verifying token: {e}")
            return False

    async def discover_user_guilds(self) -> List[Dict[str, Any]]:
        """Discover all guilds where user is a member"""
        try:
            await self._rate_limit_check()
            async with self.session.get(f"{self.api_base}/users/@me/guilds") as response:
                if response.status == 200:
                    guilds = await response.json()
                    self.logger.info(f"Found {len(guilds)} guilds where user is a member")
                    return guilds
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self.discover_user_guilds()
                else:
                    self.logger.error(f"Failed to get user guilds: {response.status}")
                    return []
        except Exception as e:
            self.logger.error(f"Error getting user guilds: {e}")
            return []

    def get_user_guilds(self) -> List[Dict[str, Any]]:
        """Get cached user guilds for random user notifier"""
        if hasattr(self, 'cached_user_guilds') and self.cached_user_guilds:
            return self.cached_user_guilds
        return []
        
    async def get_guild_members(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get members for a specific guild"""
        try:
            await self._rate_limit_check()
            
            # First try to get from cache
            cache_key = f"guild_members_{guild_id}"
            if hasattr(self, cache_key) and getattr(self, cache_key):
                self.logger.debug(f"Returning cached members for guild {guild_id}")
                return getattr(self, cache_key)
                
            # If not in cache, fetch from API
            members = []
            
            # Get guild channels first
            channels = await self.get_guild_channels(guild_id)
            if not channels:
                self.logger.warning(f"No channels found for guild {guild_id}")
                return []
                
            # Look for members in recent messages across channels
            for channel in channels[:5]:  # Limit to first 5 channels to avoid rate limits
                channel_id = channel.get('id')
                if not channel_id:
                    continue
                    
                try:
                    messages = await self._get_recent_messages(channel_id, 50)
                    for message in messages:
                        author = message.get('author', {})
                        if not author:
                            continue
                            
                        # Skip bots
                        if author.get('bot', False):
                            continue
                            
                        # Skip if already added
                        if any(m.get('id') == author.get('id') for m in members):
                            continue
                            
                        # Get user details including creation time
                        user_id = author.get('id')
                        if user_id:
                            user_details = await self._get_user_details(user_id)
                            if user_details:
                                # Parse the creation timestamp
                                created_at = None
                                if 'created_at' in user_details:
                                    try:
                                        timestamp = user_details.get('created_at')
                                        created_at = datetime.fromtimestamp(timestamp, timezone.utc)
                                    except:
                                        pass
                                
                                members.append({
                                    'id': user_id,
                                    'username': author.get('username', 'Unknown'),
                                    'created_at': created_at
                                })
                except Exception as e:
                    self.logger.debug(f"Error getting messages for channel {channel_id}: {e}")
            
            # Cache the results
            setattr(self, cache_key, members)
            self.logger.info(f"Found {len(members)} members in guild {guild_id}")
            return members
            
        except Exception as e:
            self.logger.error(f"Error getting guild members for {guild_id}: {e}")
            return []

    async def get_guild_info(self, guild_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed guild information"""
        try:
            await self._rate_limit_check()
            async with self.session.get(f"{self.api_base}/guilds/{guild_id}?with_counts=true") as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self.get_guild_info(guild_id)
                return None
        except Exception as e:
            self.logger.debug(f"Error getting guild info for {guild_id}: {e}")
            return None

    async def get_guild_channels(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get accessible channels in guild"""
        try:
            async with self.session.get(f"{self.api_base}/guilds/{guild_id}/channels") as response:
                if response.status == 200:
                    channels = await response.json()
                    # Filter to text channels only
                    text_channels = [ch for ch in channels if ch.get('type') == 0]
                    return text_channels
                return []
        except Exception as e:
            self.logger.debug(f"Error getting channels for {guild_id}: {e}")
            return []

    async def comprehensive_guild_monitoring(self, guild_id: str, guild_name: str) -> List[Dict[str, Any]]:
        """
        Comprehensive monitoring using multiple detection methods:
        1. Member count tracking
        2. Channel activity monitoring
        3. Message pattern analysis
        4. Presence change detection
        5. Member list comparison
        6. Activity timestamp tracking
        """
        new_members = []
        guild_key = f"{guild_id}_{guild_name}"

        # Enhanced logging for problematic servers
        problem_servers = ["abu cartel", "inspiredanalyst", "wizards hub", "no limit trades"]
        is_problem_server = any(server in guild_name.lower() for server in problem_servers)

        if is_problem_server:
            self.logger.info(f"[MONITOR] ENHANCED MONITORING: {guild_name} - Starting comprehensive detection")

        try:
            # Prioritize activity-based methods that provide real user data

            # Method 2: Channel activity monitoring (PRIORITY - gives real usernames)
            detection_results = await self._method_2_channel_activity_monitoring(guild_id, guild_name, is_problem_server)
            new_members.extend(detection_results)

            # Method 3: Message pattern analysis (PRIORITY - gives real usernames)
            detection_results = await self._method_3_message_pattern_analysis(guild_id, guild_name, is_problem_server)
            new_members.extend(detection_results)

            # Method 5: Deep channel scanning (PRIORITY - gives real usernames)
            detection_results = await self._method_5_deep_channel_scanning(guild_id, guild_name, is_problem_server)
            new_members.extend(detection_results)

            # Only use count-based methods if no activity-based detections found
            if not new_members:
                # Method 1: Multi-field member count tracking (FALLBACK)
                detection_results = await self._method_1_member_count_tracking(guild_id, guild_name, is_problem_server)
                new_members.extend(detection_results)

                # Method 4: Member presence tracking (FALLBACK)
                detection_results = await self._method_4_presence_tracking(guild_id, guild_name, is_problem_server)
                new_members.extend(detection_results)

                # Method 6: Fallback heartbeat monitoring (LAST RESORT)
                detection_results = await self._method_6_fallback_heartbeat(guild_id, guild_name, is_problem_server)
                new_members.extend(detection_results)

            if is_problem_server and new_members:
                self.logger.info(f"[MONITOR] ENHANCED MONITORING: {guild_name} - SUCCESS DETECTED {len(new_members)} new members!")
            elif is_problem_server:
                self.logger.info(f"[MONITOR] ENHANCED MONITORING: {guild_name} - No new members detected this cycle")

        except Exception as e:
            self.logger.error(f"Error in comprehensive monitoring for {guild_name}: {e}")

        return new_members

    async def _method_1_member_count_tracking(self, guild_id: str, guild_name: str, enhanced_logging: bool = False) -> List[Dict[str, Any]]:
        """Method 1: Track member count changes using multiple fields"""
        try:
            guild_info = await self.get_guild_info(guild_id)
            if not guild_info:
                if enhanced_logging:
                    self.logger.info(f"🔍 METHOD 1 ({guild_name}): No guild info available")
                return []

            # Check multiple member count fields
            count_fields = ['approximate_member_count', 'member_count', 'members', 'online_members', 'approximate_presence_count']

            for field in count_fields:
                if field in guild_info and guild_info[field]:
                    current_count = guild_info[field]
                    cache_key = f"{guild_id}_{field}"

                    if cache_key not in self.last_member_check:
                        self.last_member_check[cache_key] = current_count
                        if enhanced_logging:
                            self.logger.info(f"[METHOD1] ({guild_name}): Initial {field} = {current_count}")
                        continue

                    previous_count = self.last_member_check[cache_key]

                    if current_count > previous_count:
                        increase = current_count - previous_count
                        self.last_member_check[cache_key] = current_count

                        if enhanced_logging:
                            self.logger.info(f"[METHOD1] ({guild_name}): SUCCESS {field} increased: {previous_count} -> {current_count} (+{increase})")

                        notification = await self._create_count_based_notification(guild_id, guild_name, increase, field)
                        return [notification]
                    else:
                        self.last_member_check[cache_key] = current_count

            if enhanced_logging:
                available_fields = [f"{k}={v}" for k, v in guild_info.items() if 'member' in k.lower() or 'count' in k.lower()]
                self.logger.debug(f"[METHOD1] ({guild_name}): Available count fields: {available_fields}")

        except Exception as e:
            if enhanced_logging:
                self.logger.warning(f"[METHOD1] ({guild_name}): Error - {e}")

        return []

    async def _method_2_channel_activity_monitoring(self, guild_id: str, guild_name: str, enhanced_logging: bool = False) -> List[Dict[str, Any]]:
        """Method 2: Monitor channel activity for join indicators"""
        try:
            channels = await self.get_guild_channels(guild_id)
            if not channels:
                if enhanced_logging:
                    self.logger.info(f"🔍 METHOD 2 ({guild_name}): No accessible channels")
                return []

            if enhanced_logging:
                self.logger.info(f"[METHOD2] ({guild_name}): Checking {len(channels)} channels")

            # Check multiple channels thoroughly
            for i, channel in enumerate(channels[:15]):  # Check up to 15 channels
                try:
                    channel_name = channel.get('name', 'Unknown')

                    # Get recent messages
                    recent_messages = await self._get_recent_messages(channel['id'], limit=20)

                    if recent_messages:
                        if enhanced_logging:
                            self.logger.debug(f"🔍 METHOD 2 ({guild_name}): Channel '{channel_name}' has {len(recent_messages)} recent messages")

                        for message in recent_messages:
                            # Check for join messages
                            if self._is_member_join_message(message):
                                if enhanced_logging:
                                    self.logger.info(f"🔍 METHOD 2 ({guild_name}): ✅ Join message found in '{channel_name}'")
                                return [await self._create_activity_based_notification(guild_id, guild_name, message, "join_message")]

                            # Check for new user activity
                            if self._is_potential_new_user_activity(message):
                                if enhanced_logging:
                                    self.logger.info(f"🔍 METHOD 2 ({guild_name}): ✅ New user activity in '{channel_name}'")
                                return [await self._create_activity_based_notification(guild_id, guild_name, message, "new_user_activity")]

                    await asyncio.sleep(0.3)  # Rate limiting

                except Exception as e:
                    if enhanced_logging:
                        self.logger.debug(f"🔍 METHOD 2 ({guild_name}): Error checking channel '{channel.get('name', 'Unknown')}': {e}")
                    continue

        except Exception as e:
            if enhanced_logging:
                self.logger.warning(f"🔍 METHOD 2 ({guild_name}): Error - {e}")

        return []

    async def _method_3_message_pattern_analysis(self, guild_id: str, guild_name: str, enhanced_logging: bool = False) -> List[Dict[str, Any]]:
        """Method 3: Analyze message patterns for new member indicators"""
        try:
            channels = await self.get_guild_channels(guild_id)
            if not channels:
                return []

            # Look for welcome channels, general channels, etc.
            priority_channels = []
            for channel in channels:
                channel_name = channel.get('name', '').lower()
                if any(keyword in channel_name for keyword in ['welcome', 'general', 'chat', 'main', 'lobby']):
                    priority_channels.append(channel)

            # If no priority channels, use first few channels
            if not priority_channels:
                priority_channels = channels[:5]

            if enhanced_logging:
                self.logger.info(f"[METHOD3] ({guild_name}): Analyzing {len(priority_channels)} priority channels")

            for channel in priority_channels:
                try:
                    messages = await self._get_recent_messages(channel['id'], limit=30)

                    for message in messages:
                        # Advanced pattern matching
                        if self._analyze_message_for_new_member_patterns(message):
                            if enhanced_logging:
                                self.logger.info(f"🔍 METHOD 3 ({guild_name}): ✅ New member pattern detected")
                            return [await self._create_activity_based_notification(guild_id, guild_name, message, "pattern_analysis")]

                    await asyncio.sleep(0.2)

                except Exception as e:
                    continue

        except Exception as e:
            if enhanced_logging:
                self.logger.warning(f"🔍 METHOD 3 ({guild_name}): Error - {e}")

        return []

    async def _method_4_presence_tracking(self, guild_id: str, guild_name: str, enhanced_logging: bool = False) -> List[Dict[str, Any]]:
        """Method 4: Track presence/activity changes"""
        try:
            # Try to get guild with presence data
            url = f"{self.api_base}/guilds/{guild_id}?with_counts=true"
            async with self.session.get(url) as response:
                if response.status == 200:
                    guild_data = await response.json()

                    presence_count = guild_data.get('approximate_presence_count', 0)
                    cache_key = f"{guild_id}_presence"

                    if cache_key not in self.last_member_check:
                        self.last_member_check[cache_key] = presence_count
                        if enhanced_logging:
                            self.logger.info(f"🔍 METHOD 4 ({guild_name}): Initial presence count = {presence_count}")
                        return []

                    previous_presence = self.last_member_check[cache_key]

                    if presence_count > previous_presence:
                        increase = presence_count - previous_presence
                        self.last_member_check[cache_key] = presence_count

                        if enhanced_logging:
                            self.logger.info(f"[METHOD4] ({guild_name}): SUCCESS Presence increased: {previous_presence} -> {presence_count}")

                        notification = await self._create_presence_based_notification(guild_id, guild_name, increase)
                        return [notification]
                    else:
                        self.last_member_check[cache_key] = presence_count

        except Exception as e:
            if enhanced_logging:
                self.logger.warning(f"🔍 METHOD 4 ({guild_name}): Error - {e}")

        return []

    async def _method_5_deep_channel_scanning(self, guild_id: str, guild_name: str, enhanced_logging: bool = False) -> List[Dict[str, Any]]:
        """Method 5: Deep scan of all accessible channels for any activity"""
        try:
            channels = await self.get_guild_channels(guild_id)
            if not channels:
                return []

            if enhanced_logging:
                self.logger.info(f"🔍 METHOD 5 ({guild_name}): Deep scanning {len(channels)} channels")

            # Check ALL channels, not just a few
            activity_detected = False
            latest_activity = None

            for channel in channels:
                try:
                    messages = await self._get_recent_messages(channel['id'], limit=10)

                    if messages:
                        # Check for very recent activity (last 5 minutes)
                        for message in messages:
                            timestamp = message.get('timestamp', '')
                            if timestamp:
                                try:
                                    msg_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                    time_diff = (datetime.now(timezone.utc) - msg_time).total_seconds()

                                    if time_diff < 300:  # Activity in last 5 minutes
                                        activity_detected = True
                                        if not latest_activity or time_diff < latest_activity['time_diff']:
                                            latest_activity = {
                                                'message': message,
                                                'time_diff': time_diff,
                                                'channel': channel
                                            }
                                except:
                                    pass

                    await asyncio.sleep(0.1)  # Minimal rate limiting

                except Exception as e:
                    continue

            if activity_detected and latest_activity:
                # Check if this activity might indicate a new member
                message = latest_activity['message']
                author = message.get('author', {})

                # If it's a very new account or shows signs of being new
                if self._could_be_new_member_activity(message):
                    if enhanced_logging:
                        self.logger.info(f"🔍 METHOD 5 ({guild_name}): ✅ Potential new member activity detected")
                    return [await self._create_activity_based_notification(guild_id, guild_name, message, "deep_scan")]

        except Exception as e:
            if enhanced_logging:
                self.logger.warning(f"🔍 METHOD 5 ({guild_name}): Error - {e}")

        return []

    async def _method_6_fallback_heartbeat(self, guild_id: str, guild_name: str, enhanced_logging: bool = False) -> List[Dict[str, Any]]:
        """Method 6: Fallback heartbeat monitoring to ensure we don't miss anything"""
        try:
            heartbeat_key = f"{guild_id}_heartbeat"
            current_time = datetime.now(timezone.utc)

            if heartbeat_key not in self.last_member_check:
                self.last_member_check[heartbeat_key] = current_time
                return []

            last_heartbeat = self.last_member_check[heartbeat_key]
            time_since_last = (current_time - last_heartbeat).total_seconds()

            # Every 5 minutes, create a monitoring ping for problematic servers
            if time_since_last > 300:  # 5 minutes
                self.last_member_check[heartbeat_key] = current_time

                # Only for servers that have had issues
                problem_servers = ["abu cartel", "inspiredanalyst", "wizards hub", "no limit trades"]
                if any(server in guild_name.lower() for server in problem_servers):
                    if enhanced_logging:
                        self.logger.info(f"🔍 METHOD 6 ({guild_name}): 💓 Heartbeat monitoring ping")
                    return [await self._create_heartbeat_notification(guild_id, guild_name)]

        except Exception as e:
            if enhanced_logging:
                self.logger.warning(f"🔍 METHOD 6 ({guild_name}): Error - {e}")

        return []

    async def monitor_guild_for_new_members(self, guild_id: str, guild_name: str) -> List[Dict[str, Any]]:
        """Main monitoring function using comprehensive detection"""
        return await self.comprehensive_guild_monitoring(guild_id, guild_name)

    async def start_monitoring(self):
        """Start the enhanced monitoring process"""
        self.is_running = True

        # Discover guilds and cache them for random user notifier
        self.cached_user_guilds = await self.discover_user_guilds()

        # Start the monitoring cycle
        await self.start_monitoring_cycle()

    async def start_monitoring_cycle(self, check_interval: int = 7):
        """Start the enhanced monitoring cycle for user guilds"""
        self.logger.info(f"Starting ENHANCED user guild monitoring cycle (interval: {check_interval}s)")
        self.logger.info("🚀 Multi-method detection active: Member count, Channel activity, Message patterns, Presence tracking, Deep scanning, Heartbeat monitoring")

        cycle_count = 0
        while True:
            try:
                cycle_count += 1
                start_time = datetime.now(timezone.utc)

                # Get all user guilds
                guilds = await self.discover_user_guilds()

                if not guilds:
                    self.logger.warning("No user guilds found - waiting before retry")
                    await asyncio.sleep(30)
                    continue

                self.logger.debug(f"🔄 Cycle {cycle_count}: Monitoring {len(guilds)} guilds with enhanced detection")

                total_detections = 0
                for guild in guilds:
                    guild_id = guild['id']
                    guild_name = guild['name']

                    # Skip if this guild is excluded
                    if int(guild_id) in self.config.get_excluded_servers():
                        self.logger.debug(f"Skipping excluded guild: {guild_name}")
                        continue

                    try:
                        # Use comprehensive monitoring
                        new_members = await self.comprehensive_guild_monitoring(guild_id, guild_name)

                        # Process new members
                        for member_data in new_members:
                            # Check for duplicates
                            is_duplicate = await self.db.check_notification_sent(
                                user_id=member_data['user_id'],
                                server_id=member_data['server_id'],
                                within_hours=24
                            )

                            if is_duplicate:
                                self.logger.debug(f"Already notified for {member_data['username']} in {guild_name} within 24h, skipping")
                                continue

                            if self.formatter.should_notify(member_data):
                                # Call the callback if provided (for notifications)
                                if self.new_member_callback:
                                    try:
                                        await self.new_member_callback(member_data, source="enhanced_user_monitoring")
                                        total_detections += 1
                                    except Exception as e:
                                        self.logger.error(f"Error in new member callback: {e}")

                                self.logger.info(f"✅ NEW MEMBER: {member_data['username']} in {guild_name} (via {member_data.get('monitoring_source', 'unknown')})")

                    except Exception as e:
                        self.logger.error(f"Error monitoring guild {guild_name}: {e}")
                        continue

                    # Minimal rate limiting between guilds
                    await asyncio.sleep(0.2)

                # Log cycle completion
                cycle_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                if total_detections > 0:
                    self.logger.info(f"🎉 Cycle {cycle_count} completed: {total_detections} new members detected in {cycle_duration:.1f}s")

                # Wait before next cycle
                await asyncio.sleep(check_interval)

            except Exception as e:
                self.logger.error(f"Error in enhanced monitoring cycle: {e}")
                await asyncio.sleep(30)

    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get statistics about user monitoring"""
        return {
            'monitored_guilds': len(self.monitored_guilds),
            'last_checks': len(self.last_member_check),
            'user_info': self.user_info,
            'session_active': self.session is not None
        }

    # Helper methods for message detection
    async def _get_recent_messages(self, channel_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages from a channel"""
        try:
            await self._rate_limit_check()
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit={limit}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._get_recent_messages(channel_id, limit)
                return []
        except Exception as e:
            self.logger.debug(f"Error getting messages from channel {channel_id}: {e}")
            return []

    def _is_member_join_message(self, message: Dict[str, Any]) -> bool:
        """Enhanced member join message detection"""
        try:
            message_type = message.get('type', 0)
            content = message.get('content', '').lower()
            author = message.get('author', {})

            # Type 7 is USER_JOIN in Discord API
            if message_type == 7:
                return True

            # Check for join-related system messages
            if message_type == 0:
                join_indicators = [
                    'joined the server', 'joined the guild', 'welcome to',
                    'has joined', 'new member', 'member joined',
                    'just joined', 'welcome @', 'welcome back',
                    'joined us', 'say hello to', 'please welcome'
                ]

                for indicator in join_indicators:
                    if indicator in content:
                        return True

            # Check message timestamp for very recent activity
            timestamp = message.get('timestamp', '')
            if timestamp:
                try:
                    msg_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_diff = (datetime.now(timezone.utc) - msg_time).total_seconds()

                    # If message is very recent (within 2 minutes) and has join patterns
                    if time_diff < 120:
                        quick_join_patterns = ['hi', 'hello', 'hey everyone', 'new here', 'first time']
                        if any(pattern in content for pattern in quick_join_patterns) and len(content) < 30:
                            return True
                except:
                    pass

            return False

        except Exception as e:
            self.logger.debug(f"Error checking join message: {e}")
            return False

    def _is_potential_new_user_activity(self, message: Dict[str, Any]) -> bool:
        """Check if message indicates potential new user activity"""
        try:
            author = message.get('author', {})
            content = message.get('content', '').lower()
            timestamp = message.get('timestamp', '')

            # Check if message is very recent
            if timestamp:
                try:
                    msg_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_diff = (datetime.now(timezone.utc) - msg_time).total_seconds()
                    if time_diff > 180:  # More than 3 minutes old
                        return False
                except:
                    return False

            # Look for new user patterns
            new_user_indicators = [
                'hello', 'hi everyone', 'hey', 'greetings', 'new here',
                'just joined', 'first time', 'nice to meet', 'glad to be here',
                'excited to join', 'thanks for having me', 'happy to be here'
            ]

            for indicator in new_user_indicators:
                if indicator in content and len(content) < 100:  # Short, greeting-like messages
                    return True

            # Check if author has very new account
            if author.get('id'):
                try:
                    user_id = int(author['id'])
                    created_timestamp = ((user_id >> 22) + 1420070400000) / 1000
                    created_at = datetime.fromtimestamp(created_timestamp, tz=timezone.utc)
                    age_hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600

                    # Account less than 24 hours old
                    if age_hours < 24:
                        return True
                except:
                    pass

            return False

        except Exception as e:
            self.logger.debug(f"Error checking new user activity: {e}")
            return False

    def _analyze_message_for_new_member_patterns(self, message: Dict[str, Any]) -> bool:
        """Advanced pattern analysis for new member detection"""
        try:
            content = message.get('content', '').lower()
            author = message.get('author', {})

            # Advanced patterns
            advanced_patterns = [
                'just got here', 'brand new', 'where do i start', 'how does this work',
                'what is this place', 'can someone help', 'im new to this',
                'never been here before', 'first day', 'just found this'
            ]

            for pattern in advanced_patterns:
                if pattern in content:
                    return True

            # Check for very short introductory messages
            if len(content) < 20 and any(word in content for word in ['hi', 'hello', 'hey', 'sup']):
                return True

            return False

        except Exception as e:
            return False

    def _could_be_new_member_activity(self, message: Dict[str, Any]) -> bool:
        """Check if activity could indicate a new member"""
        try:
            # Combine multiple checks
            return (self._is_member_join_message(message) or
                   self._is_potential_new_user_activity(message) or
                   self._analyze_message_for_new_member_patterns(message))
        except:
            return False

    # Notification creation methods
    async def _create_count_based_notification(self, guild_id: str, guild_name: str, member_increase: int, field: str) -> Dict[str, Any]:
        """Create notification based on member count increase - enhanced with recent message scanning"""

        # Try to get actual member details from recent messages first
        recent_member = await self._scan_recent_messages_for_new_members(guild_id, guild_name)
        if recent_member:
            # Update with count information
            recent_member['member_count_change'] = member_increase
            recent_member['monitoring_source'] = f'enhanced_count_tracking_{field}_with_message_details'
            recent_member['raw_data']['detection_field'] = field
            recent_member['raw_data']['member_count_change'] = member_increase
            recent_member['raw_data']['detection_method'] = 'count_tracking_with_message_scan'
            self.logger.info(f"[COUNT_ENHANCED] Found real user from recent messages: {recent_member.get('username', 'Unknown')}")
            return recent_member

        # Try direct API member details (less likely to work due to permissions)
        actual_member = await self._try_get_actual_member_details(guild_id, guild_name)
        if actual_member:
            actual_member['member_count_change'] = member_increase
            actual_member['monitoring_source'] = f'enhanced_count_tracking_{field}_with_api_details'
            actual_member['raw_data']['detection_field'] = field
            actual_member['raw_data']['member_count_change'] = member_increase
            return actual_member

        # Fallback to generic notification only as last resort
        self.logger.warning(f"[COUNT_FALLBACK] Using generic notification for {guild_name} - could not get member details")

        bulk_user_id = int(f"{int(guild_id)}{int(datetime.now(timezone.utc).timestamp())}"[-10:])

        return {
            'user_id': bulk_user_id,
            'username': f"New Member(s) Online (+{member_increase})",
            'display_name': f"New Member(s) Online (+{member_increase})",
            'discriminator': None,
            'global_name': None,
            'server_id': int(guild_id),
            'server_name': guild_name,
            'join_timestamp': datetime.now(timezone.utc).isoformat(),
            'account_created': datetime.now(timezone.utc).isoformat(),
            'account_age_days': 0,
            'account_age_formatted': "Unknown",
            'avatar_url': None,
            'is_bot': False,
            'is_verified': True,
            'is_system': False,
            'member_count_change': member_increase,
            'monitoring_source': f'enhanced_count_tracking_{field}_fallback',
            'raw_data': {
                'mention': f"New member(s) in {guild_name}",
                'detection_field': field,
                'member_count_change': member_increase,
                'detection_method': 'count_tracking_fallback_only'
            }
        }

    async def _try_get_actual_member_details(self, guild_id: str, guild_name: str) -> Optional[Dict[str, Any]]:
        """Try to get actual member details using various methods"""
        try:
            # Method 1: Try to get recent guild members
            await self._rate_limit_check()
            url = f"https://discord.com/api/v9/guilds/{guild_id}/members?limit=10"
            async with self.session.get(url) as response:
                if response.status == 200:
                    members = await response.json()
                    if members:
                        # Get the most recently joined member
                        recent_member = max(members, key=lambda m: m.get('joined_at', ''))
                        user = recent_member.get('user', {})

                        if user.get('id'):
                            return await self._create_member_notification_from_data(
                                user, recent_member, guild_id, guild_name
                            )

                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    await asyncio.sleep(retry_after)
                    return await self._try_get_actual_member_details(guild_id, guild_name)

            # Method 2: Try to get guild audit log for member joins
            await self._rate_limit_check()
            url = f"https://discord.com/api/v9/guilds/{guild_id}/audit-logs?action_type=1&limit=5"
            async with self.session.get(url) as response:
                if response.status == 200:
                    audit_logs = await response.json()
                    entries = audit_logs.get('audit_log_entries', [])

                    if entries:
                        recent_join = entries[0]
                        target_id = recent_join.get('target_id')

                        if target_id:
                            # Try to get user details
                            user_details = await self._get_user_details(target_id)
                            if user_details:
                                return await self._create_member_notification_from_user(
                                    user_details, guild_id, guild_name
                                )

        except Exception as e:
            self.logger.debug(f"Could not get actual member details: {e}")

        return None

    async def _get_user_details(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user details by user ID"""
        try:
            await self._rate_limit_check()
            url = f"https://discord.com/api/v9/users/{user_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    await asyncio.sleep(retry_after)
                    return await self._get_user_details(user_id)
        except Exception as e:
            self.logger.debug(f"Error getting user details for {user_id}: {e}")
        return None

    async def _create_member_notification_from_data(self, user: Dict[str, Any], member: Dict[str, Any], guild_id: str, guild_name: str) -> Dict[str, Any]:
        """Create notification from member data"""
        user_id = user.get('id', 0)
        username = user.get('username', 'Unknown User')

        # Calculate account age
        account_age_days = 0
        account_created = datetime.now(timezone.utc).isoformat()
        account_age_formatted = "Unknown"

        if user_id:
            try:
                user_id_int = int(user_id)
                created_timestamp = ((user_id_int >> 22) + 1420070400000) / 1000
                created_at = datetime.fromtimestamp(created_timestamp, tz=timezone.utc)
                account_created = created_at.isoformat()

                age_delta = datetime.now(timezone.utc) - created_at
                account_age_days = age_delta.days

                years = account_age_days // 365
                months = (account_age_days % 365) // 30
                days = (account_age_days % 365) % 30

                age_parts = []
                if years > 0:
                    age_parts.append(f"{years} year{'s' if years != 1 else ''}")
                if months > 0:
                    age_parts.append(f"{months} month{'s' if months != 1 else ''}")
                if days > 0 or not age_parts:
                    age_parts.append(f"{days} day{'s' if days != 1 else ''}")

                account_age_formatted = " and ".join(age_parts)
            except:
                pass

        return {
            'user_id': int(user_id) if user_id else 0,
            'username': username,
            'display_name': user.get('global_name') or username,
            'discriminator': user.get('discriminator'),
            'global_name': user.get('global_name'),
            'server_id': int(guild_id),
            'server_name': guild_name,
            'join_timestamp': member.get('joined_at', datetime.now(timezone.utc).isoformat()),
            'account_created': account_created,
            'account_age_days': account_age_days,
            'account_age_formatted': account_age_formatted,
            'avatar_url': f"https://cdn.discordapp.com/avatars/{user_id}/{user.get('avatar')}.png" if user.get('avatar') else None,
            'is_bot': user.get('bot', False),
            'is_verified': True,
            'is_system': user.get('system', False),
            'monitoring_source': 'enhanced_member_details',
            'raw_data': {
                'mention': f"<@{user_id}>" if user_id else f"@{username}",
                'detection_method': 'detailed_member_tracking'
            }
        }

    async def _create_member_notification_from_user(self, user: Dict[str, Any], guild_id: str, guild_name: str) -> Dict[str, Any]:
        """Create notification from user data only"""
        return await self._create_member_notification_from_data(user, {}, guild_id, guild_name)

    async def _scan_recent_messages_for_new_members(self, guild_id: str, guild_name: str) -> Optional[Dict[str, Any]]:
        """Scan recent messages across channels to find new member activity with real usernames"""
        try:
            guild_channels = await self.get_guild_channels(guild_id)
            if not guild_channels:
                return None

            # Focus on channels likely to have new member activity
            priority_channels = []
            for channel in guild_channels:
                channel_name = channel.get('name', '').lower()
                channel_type = channel.get('type', 0)

                # Text channels only
                if channel_type == 0:
                    # Prioritize welcome, general, chat channels
                    if any(keyword in channel_name for keyword in
                          ['welcome', 'general', 'chat', 'lobby', 'main', 'join', 'new', 'member']):
                        priority_channels.insert(0, channel)
                    else:
                        priority_channels.append(channel)

            # Check recent messages in priority channels
            for channel in priority_channels[:5]:  # Check top 5 channels
                try:
                    await self._rate_limit_check()
                    recent_messages = await self._get_recent_messages(channel.get('id'), 20)

                    if recent_messages:
                        # Look for very recent messages (last 5 minutes) from new users
                        current_time = datetime.now(timezone.utc)

                        for message in recent_messages:
                            try:
                                message_time = datetime.fromisoformat(message.get('timestamp', '').replace('Z', '+00:00'))
                                time_diff = (current_time - message_time).total_seconds()

                                # Only consider messages from last 5 minutes
                                if time_diff < 300:  # 5 minutes
                                    author = message.get('author', {})
                                    user_id = author.get('id')
                                    username = author.get('username')

                                    if user_id and username and not author.get('bot', False):
                                        # Calculate account age
                                        try:
                                            user_id_int = int(user_id)
                                            created_timestamp = ((user_id_int >> 22) + 1420070400000) / 1000
                                            created_at = datetime.fromtimestamp(created_timestamp, tz=timezone.utc)
                                            age_delta = current_time - created_at
                                            account_age_days = age_delta.days

                                            # Prioritize newer accounts (more likely to be new members)
                                            if account_age_days < 30:  # Focus on accounts less than 30 days old
                                                return await self._create_activity_based_notification(
                                                    guild_id, guild_name, message, 'recent_message_scan'
                                                )
                                        except:
                                            # If we can't calculate age, still return the user if message is very recent
                                            if time_diff < 60:  # Very recent message (1 minute)
                                                return await self._create_activity_based_notification(
                                                    guild_id, guild_name, message, 'recent_message_scan'
                                                )
                            except:
                                continue

                except Exception as e:
                    self.logger.debug(f"Error scanning channel {channel.get('name', 'unknown')}: {e}")
                    continue

        except Exception as e:
            self.logger.debug(f"Error scanning recent messages for {guild_name}: {e}")

        return None

    async def _create_activity_based_notification(self, guild_id: str, guild_name: str, message: Dict[str, Any], detection_type: str) -> Dict[str, Any]:
        """Create notification based on activity detection"""
        try:
            author = message.get('author', {})
            user_id = author.get('id', 0)
            username = author.get('username', 'Unknown User')

            # Calculate account age if user_id is available
            account_age_days = 0
            account_created = datetime.now(timezone.utc).isoformat()
            account_age_formatted = "Unknown"

            if user_id and user_id != "0":
                try:
                    user_id_int = int(user_id)
                    created_timestamp = ((user_id_int >> 22) + 1420070400000) / 1000
                    created_at = datetime.fromtimestamp(created_timestamp, tz=timezone.utc)
                    account_created = created_at.isoformat()

                    age_delta = datetime.now(timezone.utc) - created_at
                    account_age_days = age_delta.days

                    # Format age string
                    years = account_age_days // 365
                    months = (account_age_days % 365) // 30
                    days = (account_age_days % 365) % 30

                    age_parts = []
                    if years > 0:
                        age_parts.append(f"{years} year{'s' if years != 1 else ''}")
                    if months > 0:
                        age_parts.append(f"{months} month{'s' if months != 1 else ''}")
                    if days > 0 or not age_parts:
                        age_parts.append(f"{days} day{'s' if days != 1 else ''}")

                    account_age_formatted = " and ".join(age_parts)
                except Exception as e:
                    self.logger.debug(f"Error calculating account age: {e}")

            return {
                'user_id': int(user_id) if user_id and user_id != "0" else 0,
                'username': username,
                'display_name': author.get('global_name') or username,
                'discriminator': author.get('discriminator'),
                'global_name': author.get('global_name'),
                'server_id': int(guild_id),
                'server_name': guild_name,
                'join_timestamp': message.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'account_created': account_created,
                'account_age_days': account_age_days,
                'account_age_formatted': account_age_formatted,
                'avatar_url': f"https://cdn.discordapp.com/avatars/{user_id}/{author.get('avatar')}.png" if author.get('avatar') else None,
                'is_bot': author.get('bot', False),
                'is_verified': True,
                'is_system': author.get('system', False),
                'monitoring_source': f'enhanced_activity_{detection_type}',
                'raw_data': {
                    'mention': f"<@{user_id}>" if user_id else f"@{username}",
                    'detection_type': detection_type,
                    'message_content': message.get('content', '')[:100],
                    'detection_method': 'activity_monitoring'
                }
            }

        except Exception as e:
            self.logger.error(f"Error creating activity-based notification: {e}")
            return {}

    async def _create_presence_based_notification(self, guild_id: str, guild_name: str, presence_increase: int) -> Dict[str, Any]:
        """Create notification based on presence increase"""
        presence_user_id = int(f"{int(guild_id)}{int(datetime.now(timezone.utc).timestamp())}"[-10:])

        return {
            'user_id': presence_user_id,
            'username': f"New Member(s) Online (+{presence_increase})",
            'display_name': f"New Member(s) Online (+{presence_increase})",
            'discriminator': None,
            'global_name': None,
            'server_id': int(guild_id),
            'server_name': guild_name,
            'join_timestamp': datetime.now(timezone.utc).isoformat(),
            'account_created': datetime.now(timezone.utc).isoformat(),
            'account_age_days': 0,
            'account_age_formatted': "Unknown",
            'avatar_url': None,
            'is_bot': False,
            'is_verified': True,
            'is_system': False,
            'presence_change': presence_increase,
            'monitoring_source': 'enhanced_presence_tracking',
            'raw_data': {
                'mention': f"New online member(s) in {guild_name}",
                'presence_change': presence_increase,
                'detection_method': 'presence_tracking'
            }
        }

    async def _create_heartbeat_notification(self, guild_id: str, guild_name: str) -> Dict[str, Any]:
        """Create heartbeat monitoring notification"""
        heartbeat_user_id = int(f"{int(guild_id)}{int(datetime.now(timezone.utc).timestamp())}"[-10:])

        return {
            'user_id': heartbeat_user_id,
            'username': f"Monitoring Active: {guild_name}",
            'display_name': f"Monitoring Active: {guild_name}",
            'discriminator': None,
            'global_name': None,
            'server_id': int(guild_id),
            'server_name': guild_name,
            'join_timestamp': datetime.now(timezone.utc).isoformat(),
            'account_created': datetime.now(timezone.utc).isoformat(),
            'account_age_days': 0,
            'account_age_formatted': "System Monitor",
            'avatar_url': None,
            'is_bot': False,
            'is_verified': True,
            'is_system': True,
            'monitoring_source': 'enhanced_heartbeat_monitoring',
            'raw_data': {
                'mention': f"Enhanced monitoring active for {guild_name}",
                'heartbeat': True,
                'detection_method': 'heartbeat_monitoring'
            }
        }

    async def close(self):
        """Close the user client session"""
        if self.session:
            await self.session.close()
            self.logger.info("Enhanced user client session closed")
