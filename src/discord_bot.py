"""
Main Discord Bot for Member Monitoring
Handles Discord events and coordinates all components
"""

import discord
from discord.ext import commands, tasks
import asyncio
import logging
import sys
import aiohttp
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Fix Windows encoding issues
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

from src.config_manager import ConfigManager
from src.database_manager import DatabaseManager
from src.user_formatter import UserFormatter
from src.notification_manager import NotificationManager
from src.server_manager import ServerManager
from src.user_client import DiscordUserClient
from src.random_user_notifier import RandomUserNotifier

class DiscordMemberBot(discord.Client):
    def __init__(self, config: ConfigManager):
        # Set up intents
        intents = discord.Intents.default()
        intents.members = True  # Required for member join events
        intents.guilds = True   # Required for guild events
        intents.message_content = True  # Optional, for commands

        # Set up HTTP parameters with SSL verification disabled
        http_params = {
            'connector': aiohttp.TCPConnector(ssl=False)
        }

        super().__init__(intents=intents, http_params=http_params)

        # Initialize components
        self.config = config
        self.db = DatabaseManager(config.get_database_config()['path'])
        self.formatter = UserFormatter(config)
        self.notification_manager = NotificationManager(self, config, self.formatter)
        self.server_manager = ServerManager(self, config, self.db)
        self.user_client = DiscordUserClient(config, self.db, self.formatter, self._handle_user_monitoring_join)

        # Bot state
        self.is_ready = False
        self.start_time = None
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.stats = {
            'member_joins_processed': 0,
            'notifications_sent': 0,
            'errors_encountered': 0,
            'uptime_start': None
        }

    async def setup_hook(self):
        """Called when the bot is starting up"""
        self.logger.info("Setting up Discord Member Bot...")

        try:
            # Initialize database
            await self.db.initialize()
            self.logger.info("Database initialized")

            # Create necessary directories
            self.config.create_directories()
            self.logger.info("Directories created")

            # Start background tasks
            self.cleanup_task.start()
            self.stats_update_task.start()

            self.logger.info("Bot setup completed")

        except Exception as e:
            self.logger.error(f"Error during bot setup: {e}")
            raise

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord"""
        self.logger.info(f"Bot logged in as {self.user.name}#{self.user.discriminator}")
        self.logger.info(f"Bot ID: {self.user.id}")

        try:
            # Initialize components
            await self.server_manager.initialize()
            await self.notification_manager.start_processing()

            # Initialize random user notifier
            self.random_user_notifier = RandomUserNotifier(self, self.config, self.db, self.formatter)
            await self.random_user_notifier.start()
            self.logger.info("Random user notifier started")

            # Initialize user monitoring if enabled and token available
            user_token = self.config.get_user_token()
            if self.config.is_user_monitoring_enabled() and user_token:
                if await self.user_client.initialize(user_token):
                    self.logger.info("User monitoring initialized successfully")
                    # Start user monitoring in background
                    asyncio.create_task(self._start_user_monitoring())
                else:
                    self.logger.warning("Failed to initialize user monitoring")
            elif not user_token:
                self.logger.info("User monitoring disabled - no user token provided")
            else:
                self.logger.info("User monitoring disabled in configuration")

            # Set bot state
            self.is_ready = True
            self.start_time = datetime.now(timezone.utc)
            self.stats['uptime_start'] = self.start_time

            # Get server count
            server_count = len(self.server_manager.get_monitored_servers())

            self.logger.info(f"Bot is ready! Monitoring {server_count} servers")

            # Send startup notification
            await self.notification_manager.send_startup_notification(server_count)

            # Send test notification if configured
            if self.config.get('notifications.send_test_on_startup', False):
                await asyncio.sleep(2)  # Brief delay
                await self.notification_manager.send_test_notification()

        except Exception as e:
            self.logger.error(f"Error during bot ready event: {e}")
            await self.notification_manager.send_error_notification(
                f"Bot startup error: {str(e)}",
                "on_ready event"
            )

    async def _start_user_monitoring(self):
        """Start the user monitoring background task"""
        try:
            await self.user_client.start_monitoring()
        except Exception as e:
            self.logger.error(f"Error in user monitoring: {e}")
            # Send error notification
            await self.notification_manager.send_error_notification(
                f"User monitoring failed: {str(e)}",
                "User monitoring system"
            )
            # Retry after delay
            await asyncio.sleep(60)
            self.logger.info("Retrying user monitoring initialization...")
            try:
                if await self.user_client.initialize(self.config.get_user_token()):
                    asyncio.create_task(self._start_user_monitoring())
            except Exception as retry_error:
                self.logger.error(f"User monitoring retry failed: {retry_error}")

    async def _handle_user_monitoring_join(self, user_data: dict, source: str = "user_monitoring"):
        """Handle new member joins detected through user monitoring"""
        try:
            self.logger.info(f"Processing user monitoring join: {user_data['username']} in {user_data['server_name']}")
            
            # Explicitly filter out Begot server
            if user_data['server_name'] == "Begot":
                self.logger.info(f"Skipping notification for server Begot: {user_data['username']}")
                return

            # Check for duplicate notifications using database (persistent across restarts)
            notification_already_sent = await self.db.check_notification_sent(
                user_id=user_data['user_id'],
                server_id=user_data['server_id'],
                within_hours=24
            )

            if notification_already_sent:
                self.logger.debug(f"Notification already sent for {user_data['username']} within 24h, skipping")
                return

            # Record in database first to prevent future duplicates
            join_id = await self.db.record_member_join(user_data)

            # Check if notification should be sent
            if self.formatter.should_notify(user_data):
                try:
                    # Queue notification with join_id for tracking
                    await self.notification_manager.queue_member_join_notification(user_data, source, join_id)

                    # Mark notification as queued/sent in database ONLY after successful queuing
                    await self.db.mark_notification_sent(join_id)

                    self.stats['notifications_sent'] += 1
                    self.logger.info(f"User monitoring notification sent for {user_data['username']} in {user_data['server_name']}")
                except Exception as notification_error:
                    self.logger.error(f"Failed to send notification for {user_data['username']}: {notification_error}")
                    # Don't mark as sent if notification failed
                    raise notification_error
            else:
                self.logger.debug(f"Notification filtered for {user_data['username']} (filters applied)")

            # Update statistics
            self.stats['member_joins_processed'] += 1

            self.logger.info(f"User monitoring join processed: {user_data['username']} in {user_data['server_name']}")

        except Exception as e:
            self.logger.error(f"Error processing user monitoring join: {e}")
            self.stats['errors_encountered'] += 1

            # Send error notification for critical errors
            await self.notification_manager.send_error_notification(
                f"Error processing user monitoring join: {str(e)}",
                f"User: {user_data.get('username', 'Unknown')} in {user_data.get('server_name', 'Unknown')}"
            )

    async def on_member_join(self, member: discord.Member):
        """Called when a member joins a server"""
        try:
            # Check if we should monitor this server
            if not self.server_manager.is_server_monitored(member.guild.id):
                self.logger.debug(f"Ignoring member join in unmonitored server: {member.guild.name}")
                return

            # Extract user data
            user_data = self.formatter.extract_user_data(member)

            self.logger.info(f"Member joined: {user_data['username']} in {user_data['server_name']}")

            # Check for duplicate notifications (avoid spam)
            notification_already_sent = await self.db.check_notification_sent(
                user_id=member.id,
                server_id=member.guild.id,
                within_hours=24
            )

            if notification_already_sent:
                self.logger.debug(f"Notification already sent for {user_data['username']} within 24h, skipping")
                return

            # Record in database
            join_id = await self.db.record_member_join(user_data)

            # Check if notification should be sent
            if self.formatter.should_notify(user_data):
                try:
                    # Queue notification with source information
                    await self.notification_manager.queue_member_join_notification(user_data, "bot_monitoring", join_id)

                    # Mark notification as sent in database ONLY after successful queuing
                    await self.db.mark_notification_sent(join_id)

                    self.stats['notifications_sent'] += 1
                    self.logger.info(f"Notification sent for {user_data['username']} in {user_data['server_name']}")
                except Exception as notification_error:
                    self.logger.error(f"Failed to send notification for {user_data['username']}: {notification_error}")
                    # Don't mark as sent if notification failed
                    raise notification_error
            else:
                self.logger.debug(f"Notification filtered for {user_data['username']} (filters applied)")

            self.stats['member_joins_processed'] += 1

        except Exception as e:
            self.logger.error(f"Error processing member join for {member.name}: {e}")
            self.stats['errors_encountered'] += 1

            # Send error notification for critical errors
            if "database" in str(e).lower() or "notification" in str(e).lower():
                await self.notification_manager.send_error_notification(
                    f"Error processing member join: {str(e)}",
                    f"Member: {member.name} in {member.guild.name}"
                )

    async def on_guild_join(self, guild: discord.Guild):
        """Called when the bot joins a new server"""
        try:
            self.logger.info(f"Bot joined new server: {guild.name} ({guild.id})")

            # Check if server should be monitored
            if not self.server_manager.is_server_excluded(guild.id):
                # Register the new server
                server_info = await self.server_manager._register_server(guild)
                if server_info:
                    self.server_manager.monitored_servers.add(guild.id)

                    # Send notification about new server
                    user_id = self.config.get_user_id()
                    user = await self.fetch_user(user_id)
                    if user:
                        message = (
                            f"🆕 **New Server Added to Monitoring**\n\n"
                            f"**Server:** {guild.name}\n"
                            f"**Server ID:** {guild.id}\n"
                            f"**Members:** {guild.member_count:,}\n"
                            f"**Added:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                            f"I'm now monitoring member joins in this server!"
                        )
                        await user.send(message)

                    self.logger.info(f"Added new server to monitoring: {guild.name}")
            else:
                self.logger.info(f"New server is excluded from monitoring: {guild.name}")

        except Exception as e:
            self.logger.error(f"Error handling guild join for {guild.name}: {e}")

    async def on_guild_remove(self, guild: discord.Guild):
        """Called when the bot leaves a server"""
        try:
            self.logger.info(f"Bot left server: {guild.name} ({guild.id})")

            # Remove from monitoring
            if guild.id in self.server_manager.monitored_servers:
                await self.server_manager._unregister_server(guild.id)
                self.server_manager.monitored_servers.discard(guild.id)

                # Send notification about removed server
                user_id = self.config.get_user_id()
                user = await self.fetch_user(user_id)
                if user:
                    message = (
                        f"❌ **Server Removed from Monitoring**\n\n"
                        f"**Server:** {guild.name}\n"
                        f"**Server ID:** {guild.id}\n"
                        f"**Removed:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                        f"No longer monitoring member joins in this server."
                    )
                    await user.send(message)

                self.logger.info(f"Removed server from monitoring: {guild.name}")

        except Exception as e:
            self.logger.error(f"Error handling guild remove for {guild.name}: {e}")

    async def on_error(self, event: str, *args, **kwargs):
        """Called when an error occurs"""
        self.logger.error(f"Discord error in event {event}: {sys.exc_info()}")
        self.stats['errors_encountered'] += 1

        # Send error notification for critical events
        if event in ['on_member_join', 'on_ready', 'on_guild_join']:
            await self.notification_manager.send_error_notification(
                f"Discord event error in {event}",
                f"Args: {args[:2]}"  # Limit args to avoid spam
            )

    async def on_disconnect(self):
        """Called when the bot disconnects"""
        self.logger.warning("Bot disconnected from Discord")
        self.is_ready = False

    async def on_resumed(self):
        """Called when the bot resumes connection"""
        self.logger.info("Bot resumed connection to Discord")
        self.is_ready = True

    @tasks.loop(hours=24)
    async def cleanup_task(self):
        """Daily cleanup task"""
        try:
            self.logger.info("Running daily cleanup...")

            # Clean up old database records
            deleted_count = await self.db.cleanup_old_records(days_to_keep=90)
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old database records")

            # Clean up inactive servers
            inactive_count = await self.server_manager.cleanup_inactive_servers()
            if inactive_count > 0:
                self.logger.info(f"Cleaned up {inactive_count} inactive servers")

            # Backup database if enabled
            db_config = self.config.get_database_config()
            if db_config.get('backup_enabled', True):
                backup_path = f"backups/member_joins_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                await self.db.backup_database(backup_path)
                self.logger.info(f"Database backed up to {backup_path}")

        except Exception as e:
            self.logger.error(f"Error in cleanup task: {e}")

    @tasks.loop(hours=1)
    async def stats_update_task(self):
        """Hourly statistics update"""
        try:
            # Update server member counts
            for guild_id in self.server_manager.monitored_servers:
                guild = self.get_guild(guild_id)
                if guild:
                    await self.db.add_or_update_server(
                        server_id=guild.id,
                        server_name=guild.name,
                        member_count=guild.member_count
                    )

            # Log current statistics
            self.logger.debug(f"Stats: {self.stats['member_joins_processed']} joins processed, "
                            f"{self.stats['notifications_sent']} notifications sent, "
                            f"{self.stats['errors_encountered']} errors")

        except Exception as e:
            self.logger.error(f"Error in stats update task: {e}")

    @cleanup_task.before_loop
    async def before_cleanup_task(self):
        """Wait for bot to be ready before starting cleanup task"""
        await self.wait_until_ready()

    @stats_update_task.before_loop
    async def before_stats_update_task(self):
        """Wait for bot to be ready before starting stats task"""
        await self.wait_until_ready()

    async def get_bot_stats(self) -> Dict[str, Any]:
        """Get comprehensive bot statistics"""
        uptime = None
        if self.stats['uptime_start']:
            uptime_delta = datetime.now(timezone.utc) - self.stats['uptime_start']
            uptime = str(uptime_delta).split('.')[0]  # Remove microseconds

        db_stats = await self.db.get_database_stats()
        discovery_status = await self.server_manager.get_discovery_status()

        return {
            'bot_info': {
                'name': self.user.name if self.user else 'Unknown',
                'id': self.user.id if self.user else 'Unknown',
                'is_ready': self.is_ready,
                'uptime': uptime,
                'start_time': self.start_time.isoformat() if self.start_time else None
            },
            'processing_stats': self.stats,
            'database_stats': db_stats,
            'server_discovery': discovery_status,
            'notification_queue_size': await self.notification_manager.get_queue_size()
        }

    async def shutdown(self):
        """Safely shut down the bot and its components"""
        try:
            self.logger.info("Shutting down bot...")

            # Stop background tasks
            self.cleanup_task.cancel()
            self.stats_update_task.cancel()

            # Stop components
            if hasattr(self, 'notification_manager'):
                await self.notification_manager.stop_processing()
                await self.notification_manager.clear_queue()
                self.logger.info("Notification manager stopped")

            # Stop random user notifier if running
            if hasattr(self, 'random_user_notifier'):
                await self.random_user_notifier.stop()
                self.logger.info("Random user notifier stopped")

            # Stop user client if running
            if hasattr(self, 'user_client') and self.user_client.is_running:
                await self.user_client.close()

            # Close database connections
            await self.db.close()

            # Close Discord connection
            await self.close()

            self.logger.info("Bot shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

def setup_logging(config: ConfigManager):
    """Set up logging configuration with UTF-8 encoding support"""
    log_config = config.get_logging_config()

    # Create logs directory
    import os
    os.makedirs(os.path.dirname(log_config['file']), exist_ok=True)

    # Force UTF-8 encoding for all handlers
    file_handler = logging.FileHandler(log_config['file'], encoding='utf-8')

    # Create console handler with UTF-8 support
    console_handler = logging.StreamHandler(sys.stdout)
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    # Set formatting for both handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configure logging with UTF-8 handlers
    logging.basicConfig(
        level=getattr(logging, log_config['level']),
        handlers=[file_handler, console_handler],
        force=True  # Override any existing configuration
    )

    # Set discord.py logging level to WARNING to reduce noise
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)

    # Log encoding fix confirmation
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized with UTF-8 encoding support")

async def main():
    """Main entry point for the bot"""
    try:
        # Load configuration
        config = ConfigManager()

        # Set up logging
        setup_logging(config)

        logger = logging.getLogger(__name__)
        logger.info("Starting Discord Member Monitoring Bot...")

        # Create bot instance
        bot = DiscordMemberBot(config)

        # Disable SSL verification for Discord.py
        import discord.http
        import aiohttp
        discord.http.HTTPClient.DEFAULT_CONNECTOR = aiohttp.TCPConnector(ssl=False)

        # Run the bot
        token = config.get_discord_token()
        logger.info("Attempting to start bot with token...")

        try:
            await bot.start(token)
        except Exception as e:
            logger.error(f"Error starting bot: {e}", exc_info=True)
            raise

    except aiohttp.ClientConnectorError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Bot error: {e}", exc_info=True)
        # If there's a bot instance, try to shut it down gracefully
        if 'bot' in locals():
            logger.info("Shutting down bot...")
            await bot.shutdown()
            logger.info("Bot shutdown completed")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Bot error: {e}", exc_info=True)
        # If there's a bot instance, try to shut it down gracefully
        if 'bot' in locals():
            logger.info("Shutting down bot...")
            await bot.shutdown()
            logger.info("Bot shutdown completed")

if __name__ == "__main__":
    asyncio.run(main())
