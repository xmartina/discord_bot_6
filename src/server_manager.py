"""
Server Manager for Discord Monitoring Bot
Handles server discovery, management, and monitoring
"""

import discord
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional, Any
from src.config_manager import ConfigManager
from src.database_manager import DatabaseManager

class ServerManager:
    def __init__(self, bot: discord.Client, config: ConfigManager, db: DatabaseManager):
        self.bot = bot
        self.config = config
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Track monitored servers
        self.monitored_servers: Set[int] = set()
        self.excluded_servers: Set[int] = set(self.config.get_excluded_servers())
        self.server_info: Dict[int, Dict[str, Any]] = {}
        
        # Auto-discovery settings
        self.auto_discover = config.is_auto_discover_enabled()
        self.max_servers = config.get_max_servers()
        
        # Last update tracking
        self.last_discovery_update = None
        self.discovery_interval = 300  # 5 minutes
    
    async def initialize(self):
        """Initialize server manager and discover servers"""
        self.logger.info("Initializing Server Manager...")
        
        # Load excluded servers from config
        self.excluded_servers = set(self.config.get_excluded_servers())
        
        # Discover and register all servers
        await self.discover_servers()
        
        # Start periodic discovery if enabled
        if self.auto_discover:
            asyncio.create_task(self._periodic_discovery())
        
        self.logger.info(f"Server Manager initialized - monitoring {len(self.monitored_servers)} servers")
    
    async def discover_servers(self) -> List[Dict[str, Any]]:
        """Discover all servers the bot is a member of"""
        discovered_servers = []
        
        try:
            # Get all guilds the bot is in
            guilds = self.bot.guilds
            
            self.logger.info(f"Discovering servers... Found {len(guilds)} total guilds")
            
            for guild in guilds:
                try:
                    # Skip if server is excluded
                    if guild.id in self.excluded_servers:
                        self.logger.debug(f"Skipping excluded server: {guild.name} ({guild.id})")
                        continue
                    
                    # Check server limits
                    if len(self.monitored_servers) >= self.max_servers:
                        self.logger.warning(f"Reached maximum server limit ({self.max_servers})")
                        break
                    
                    # Check if bot has necessary permissions
                    if not await self._check_server_permissions(guild):
                        self.logger.warning(f"Insufficient permissions in server: {guild.name} ({guild.id})")
                        continue
                    
                    # Add server to monitoring
                    server_info = await self._register_server(guild)
                    if server_info:
                        discovered_servers.append(server_info)
                        self.monitored_servers.add(guild.id)
                        
                        self.logger.info(f"Added server to monitoring: {guild.name} ({guild.id}) - {guild.member_count} members")
                
                except Exception as e:
                    self.logger.error(f"Error processing server {guild.name} ({guild.id}): {e}")
                    continue
            
            self.last_discovery_update = datetime.now(timezone.utc)
            
            self.logger.info(f"Server discovery complete - monitoring {len(self.monitored_servers)} servers")
            return discovered_servers
            
        except Exception as e:
            self.logger.error(f"Error during server discovery: {e}")
            return []
    
    async def _check_server_permissions(self, guild: discord.Guild) -> bool:
        """Check if bot has necessary permissions in the server"""
        try:
            # Get bot member in the guild
            bot_member = guild.get_member(self.bot.user.id)
            if not bot_member:
                return False
            
            # Check required permissions
            permissions = bot_member.guild_permissions
            
            required_permissions = [
                permissions.view_channel,
                permissions.read_message_history,
            ]
            
            # Optional but recommended permissions
            if not all(required_permissions):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking permissions for {guild.name}: {e}")
            return False
    
    async def _register_server(self, guild: discord.Guild) -> Optional[Dict[str, Any]]:
        """Register a server for monitoring"""
        try:
            # Prepare server information
            server_info = {
                'id': guild.id,
                'name': guild.name,
                'member_count': guild.member_count,
                'owner_id': guild.owner_id,
                'created_at': guild.created_at,
                'features': list(guild.features),
                'verification_level': str(guild.verification_level),
                'explicit_content_filter': str(guild.explicit_content_filter),
                'mfa_level': guild.mfa_level,
                'premium_tier': guild.premium_tier,
                'premium_subscription_count': guild.premium_subscription_count or 0,
                'preferred_locale': str(guild.preferred_locale),
                'nsfw_level': str(guild.nsfw_level) if hasattr(guild, 'nsfw_level') else 'unknown',
                'icon_url': guild.icon.url if guild.icon else None,
                'banner_url': guild.banner.url if guild.banner else None,
                'discovery_splash_url': guild.discovery_splash.url if guild.discovery_splash else None
            }
            
            # Store in database
            await self.db.add_or_update_server(
                server_id=guild.id,
                server_name=guild.name,
                member_count=guild.member_count
            )
            
            # Store in memory
            self.server_info[guild.id] = server_info
            
            return server_info
            
        except Exception as e:
            self.logger.error(f"Error registering server {guild.name}: {e}")
            return None
    
    async def _periodic_discovery(self):
        """Periodically check for new servers"""
        while True:
            try:
                await asyncio.sleep(self.discovery_interval)
                
                if not self.auto_discover:
                    continue
                
                # Check for new servers
                current_guilds = {guild.id for guild in self.bot.guilds}
                known_servers = set(self.monitored_servers) | self.excluded_servers
                
                new_servers = current_guilds - known_servers
                left_servers = self.monitored_servers - current_guilds
                
                # Handle new servers
                if new_servers:
                    self.logger.info(f"Discovered {len(new_servers)} new servers")
                    for guild_id in new_servers:
                        guild = self.bot.get_guild(guild_id)
                        if guild and guild_id not in self.excluded_servers:
                            if len(self.monitored_servers) < self.max_servers:
                                server_info = await self._register_server(guild)
                                if server_info:
                                    self.monitored_servers.add(guild_id)
                                    self.logger.info(f"Auto-added new server: {guild.name} ({guild_id})")
                
                # Handle left servers
                if left_servers:
                    self.logger.info(f"Bot left {len(left_servers)} servers")
                    for guild_id in left_servers:
                        await self._unregister_server(guild_id)
                        self.monitored_servers.discard(guild_id)
                        self.logger.info(f"Removed server from monitoring: {guild_id}")
                
                self.last_discovery_update = datetime.now(timezone.utc)
                
            except Exception as e:
                self.logger.error(f"Error in periodic discovery: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _unregister_server(self, guild_id: int):
        """Unregister a server from monitoring"""
        try:
            # Mark server as inactive in database
            await self.db.deactivate_server(guild_id)
            
            # Remove from memory
            self.server_info.pop(guild_id, None)
            
        except Exception as e:
            self.logger.error(f"Error unregistering server {guild_id}: {e}")
    
    def is_server_monitored(self, guild_id: int) -> bool:
        """Check if a server is being monitored"""
        return guild_id in self.monitored_servers
    
    def is_server_excluded(self, guild_id: int) -> bool:
        """Check if a server is excluded from monitoring"""
        return guild_id in self.excluded_servers
    
    async def add_excluded_server(self, guild_id: int) -> bool:
        """Add a server to the exclusion list"""
        try:
            self.excluded_servers.add(guild_id)
            
            # Remove from monitoring if currently monitored
            if guild_id in self.monitored_servers:
                await self._unregister_server(guild_id)
                self.monitored_servers.discard(guild_id)
            
            # Update config
            excluded_list = list(self.excluded_servers)
            self.config.update_config('servers.excluded_servers', excluded_list)
            
            self.logger.info(f"Added server {guild_id} to exclusion list")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding server {guild_id} to exclusion list: {e}")
            return False
    
    async def remove_excluded_server(self, guild_id: int) -> bool:
        """Remove a server from the exclusion list"""
        try:
            self.excluded_servers.discard(guild_id)
            
            # Update config
            excluded_list = list(self.excluded_servers)
            self.config.update_config('servers.excluded_servers', excluded_list)
            
            # Try to add back to monitoring if bot is still in the server
            guild = self.bot.get_guild(guild_id)
            if guild and len(self.monitored_servers) < self.max_servers:
                server_info = await self._register_server(guild)
                if server_info:
                    self.monitored_servers.add(guild_id)
                    self.logger.info(f"Re-added server {guild.name} ({guild_id}) to monitoring")
            
            self.logger.info(f"Removed server {guild_id} from exclusion list")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing server {guild_id} from exclusion list: {e}")
            return False
    
    def get_monitored_servers(self) -> List[Dict[str, Any]]:
        """Get list of all monitored servers"""
        return [
            self.server_info.get(guild_id, {'id': guild_id, 'name': 'Unknown'})
            for guild_id in self.monitored_servers
        ]
    
    def get_excluded_servers(self) -> List[int]:
        """Get list of excluded server IDs"""
        return list(self.excluded_servers)
    
    async def get_server_stats(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a server"""
        if guild_id not in self.monitored_servers:
            return None
        
        try:
            # Get stats from database
            db_stats = await self.db.get_server_stats(guild_id)
            
            # Get current guild info
            guild = self.bot.get_guild(guild_id)
            if guild:
                current_info = {
                    'current_member_count': guild.member_count,
                    'online_members': sum(1 for member in guild.members if member.status != discord.Status.offline),
                    'bot_count': sum(1 for member in guild.members if member.bot),
                    'human_count': sum(1 for member in guild.members if not member.bot),
                }
                
                return {**db_stats, **current_info}
            
            return db_stats
            
        except Exception as e:
            self.logger.error(f"Error getting server stats for {guild_id}: {e}")
            return None
    
    async def refresh_server_info(self, guild_id: int) -> bool:
        """Refresh information for a specific server"""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return False
            
            server_info = await self._register_server(guild)
            return server_info is not None
            
        except Exception as e:
            self.logger.error(f"Error refreshing server info for {guild_id}: {e}")
            return False
    
    async def get_discovery_status(self) -> Dict[str, Any]:
        """Get status of server discovery"""
        return {
            'auto_discover_enabled': self.auto_discover,
            'monitored_servers_count': len(self.monitored_servers),
            'excluded_servers_count': len(self.excluded_servers),
            'max_servers': self.max_servers,
            'last_discovery_update': self.last_discovery_update,
            'discovery_interval_seconds': self.discovery_interval
        }
    
    async def force_discovery_update(self) -> List[Dict[str, Any]]:
        """Force an immediate server discovery update"""
        self.logger.info("Forcing server discovery update...")
        return await self.discover_servers()
    
    def get_server_info(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get cached server information"""
        return self.server_info.get(guild_id)
    
    async def cleanup_inactive_servers(self, days: int = 30):
        """Clean up servers that have been inactive for specified days"""
        try:
            # This would involve checking database for servers not seen recently
            # and removing them from monitoring
            
            current_guild_ids = {guild.id for guild in self.bot.guilds}
            inactive_servers = self.monitored_servers - current_guild_ids
            
            for guild_id in inactive_servers:
                await self._unregister_server(guild_id)
                self.monitored_servers.discard(guild_id)
                self.logger.info(f"Cleaned up inactive server: {guild_id}")
            
            return len(inactive_servers)
            
        except Exception as e:
            self.logger.error(f"Error cleaning up inactive servers: {e}")
            return 0