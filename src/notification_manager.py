"""
Notification Manager for Discord Monitoring Bot
Handles sending notifications via various methods
"""

import discord
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from src.config_manager import ConfigManager
from src.user_formatter import UserFormatter

class NotificationManager:
    def __init__(self, bot: discord.Client, config: ConfigManager, formatter: UserFormatter):
        self.bot = bot
        self.config = config
        self.formatter = formatter
        self.logger = logging.getLogger(__name__)
        self.notification_queue = asyncio.Queue()
        self.is_processing = False

    async def start_processing(self):
        """Start the notification processing loop"""
        if self.is_processing:
            return

        self.is_processing = True
        asyncio.create_task(self._process_notifications())
        self.logger.info("Notification processing started")

    async def stop_processing(self):
        """Stop the notification processing loop"""
        self.is_processing = False
        self.logger.info("Notification processing stopped")

    async def _process_notifications(self):
        """Process notifications from the queue"""
        while self.is_processing:
            try:
                # Wait for notification with timeout
                notification_data = await asyncio.wait_for(
                    self.notification_queue.get(),
                    timeout=1.0
                )

                await self._send_notification(notification_data)

                # Rate limiting
                rate_limit = self.config.get_rate_limit_buffer()
                if rate_limit > 0:
                    await asyncio.sleep(rate_limit)

            except asyncio.TimeoutError:
                # No notifications in queue, continue
                continue
            except Exception as e:
                self.logger.error(f"Error processing notification: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def queue_notification(self, user_data: Dict[str, Any], join_id: Optional[int] = None):
        """Add notification to processing queue"""
        notification_data = {
            'user_data': user_data,
            'join_id': join_id,
            'timestamp': datetime.now(timezone.utc),
            'method': self.config.get_notification_method()
        }

        await self.notification_queue.put(notification_data)
        self.logger.debug(f"Queued notification for user {user_data.get('username', 'Unknown')}")

    async def queue_member_join_notification(self, user_data: Dict[str, Any], source: str = "bot_monitoring", join_id: Optional[int] = None):
        """Add member join notification to processing queue with source information"""
        notification_data = {
            'user_data': user_data,
            'join_id': join_id,
            'source': source,
            'timestamp': datetime.now(timezone.utc),
            'method': self.config.get_notification_method()
        }

        await self.notification_queue.put(notification_data)
        self.logger.debug(f"Queued {source} notification for user {user_data.get('username', 'Unknown')}")

    async def _send_notification(self, notification_data: Dict[str, Any]):
        """Send individual notification"""
        try:
            method = notification_data['method']
            user_data = notification_data['user_data']
            join_id = notification_data.get('join_id')
            source = notification_data.get('source', 'bot_monitoring')

            # Add source information to user_data for formatting
            user_data_with_source = user_data.copy()
            user_data_with_source['monitoring_source'] = source

            # Debug logging
            self.logger.debug(f"Attempting to send {source} notification for {user_data.get('username', 'Unknown')} via {method}")

            success = False

            if method == 'discord_dm':
                success = await self._send_discord_dm(user_data_with_source)
            elif method == 'email':
                success = await self._send_email(user_data_with_source)
            elif method == 'webhook':
                success = await self._send_webhook(user_data_with_source)
            elif method == 'multiple':
                success = await self._send_multiple(user_data_with_source)
            else:
                self.logger.error(f"Unknown notification method: {method}")
                return

            if success:
                source_text = "user monitoring" if source == "user_monitoring" else "bot monitoring"
                self.logger.info(f"Notification sent for {user_data.get('username', 'Unknown')} in {user_data.get('server_name', 'Unknown')} (via {source_text})")

                # Mark notification as sent in database if join_id provided
                if join_id:
                    try:
                        # Import db from bot context (this is a workaround)
                        # The main bot class should handle this marking
                        pass
                    except Exception as db_error:
                        self.logger.error(f"Failed to mark notification as sent in database: {db_error}")
            else:
                self.logger.warning(f"Failed to send notification for {user_data.get('username', 'Unknown')} in {user_data.get('server_name', 'Unknown')} via {source}")

        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            import traceback
            self.logger.error(f"Notification error traceback: {traceback.format_exc()}")

    async def _send_discord_dm(self, user_data: Dict[str, Any]) -> bool:
        """Send notification via Discord DM"""
        try:
            # Validate that we have real member data before sending DM
            if not self._is_valid_member_data(user_data):
                self.logger.info(f"Skipping DM notification - no valid member data for {user_data.get('username', 'Unknown')} in {user_data.get('server_name', 'Unknown')}")
                return False

            user_id = self.config.get_user_id()
            self.logger.debug(f"Attempting to send DM to user ID: {user_id}")

            user = await self.bot.fetch_user(user_id)

            if not user:
                self.logger.error(f"Could not find user with ID {user_id}")
                return False

            self.logger.debug(f"Found user: {user.name}, formatting message...")

            # Format message
            message_content = self.formatter.format_notification_message(user_data)
            
            # Add line break after each message for better readability
            message_content = f"{message_content}\n\n"

            self.logger.debug(f"Formatted message length: {len(message_content)} characters")

            # Check if message is too long for Discord (2000 character limit)
            if len(message_content) > 2000:
                self.logger.debug("Message too long, sending as embed")
                # Try to send as embed instead
                embed = self.formatter.format_embed_notification(user_data)
                await user.send(embed=embed)
            else:
                self.logger.debug("Sending message as text")
                await user.send(message_content)

            self.logger.debug("Discord DM sent successfully")
            return True

        except discord.Forbidden as e:
            self.logger.error(f"Cannot send DM to user - DMs may be disabled or bot blocked: {e}")
            return False
        except discord.HTTPException as e:
            self.logger.error(f"HTTP error sending DM: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending DM: {e}")
            import traceback
            self.logger.error(f"DM error traceback: {traceback.format_exc()}")
            return False

    def _is_valid_member_data(self, user_data: Dict[str, Any]) -> bool:
        """Check if user data contains actual member information (not generated/fake data)"""
        try:
            # Handle None values gracefully by converting to safe defaults
            username = user_data.get('username')
            if username is None:
                username = ''
            else:
                username = str(username)

            account_age_formatted = user_data.get('account_age_formatted')
            if account_age_formatted is None:
                account_age_formatted = ''
            else:
                account_age_formatted = str(account_age_formatted)

            user_id = user_data.get('user_id', 0)
            if user_id is None:
                user_id = 0

            # Check for generic/fake usernames that indicate no real member data
            if (username.startswith('New Member(s) Online') or
                username.startswith('Monitoring Active:') or
                username == 'Unknown User' or
                'New Member(s)' in username):
                return False

            # Check for unknown account age (indicates no real member data)
            if account_age_formatted == 'Unknown':
                return False

            # Check for generated user IDs (they tend to be very large numbers)
            # Real Discord user IDs are typically 17-19 digits, generated ones are often different
            if user_id == 0:
                return False

            # Additional validation: check if we have meaningful user data
            # Real members should have proper usernames and account information
            if len(username.strip()) == 0:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating member data: {e}")
            # Default to False if validation fails
            return False

    async def _send_email(self, user_data: Dict[str, Any]) -> bool:
        """Send notification via email (placeholder for future implementation)"""
        # This would require SMTP configuration
        self.logger.warning("Email notifications not yet implemented")
        return False

    async def _send_webhook(self, user_data: Dict[str, Any]) -> bool:
        """Send notification via webhook (placeholder for future implementation)"""
        # This would require webhook URL configuration
        self.logger.warning("Webhook notifications not yet implemented")
        return False

    async def _send_multiple(self, user_data: Dict[str, Any]) -> bool:
        """Send notification via multiple methods"""
        success_count = 0

        # Try Discord DM first
        if await self._send_discord_dm(user_data):
            success_count += 1

        # Try other methods if configured
        # This would be expanded based on configuration

        return success_count > 0

    async def send_summary_report(self, joins_data: List[Dict[str, Any]], timeframe: str = "24 hours"):
        """Send a summary report of multiple joins"""
        try:
            user_id = self.config.get_user_id()
            user = await self.bot.fetch_user(user_id)

            if not user:
                self.logger.error(f"Could not find user with ID {user_id}")
                return False

            # Format summary message
            summary_message = self.formatter.format_summary_report(joins_data, timeframe)

            # Send summary
            if len(summary_message) > 2000:
                # Split into multiple messages if too long
                chunks = self._split_message(summary_message, 2000)
                for chunk in chunks:
                    await user.send(chunk)
                    await asyncio.sleep(1)  # Rate limiting
            else:
                await user.send(summary_message)

            self.logger.info(f"Summary report sent for {len(joins_data)} joins")
            return True

        except Exception as e:
            self.logger.error(f"Error sending summary report: {e}")
            return False

    def _split_message(self, message: str, max_length: int = 2000) -> List[str]:
        """Split long message into chunks"""
        if len(message) <= max_length:
            return [message]

        chunks = []
        lines = message.split('\n')
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) + 1 <= max_length:
                if current_chunk:
                    current_chunk += '\n' + line
                else:
                    current_chunk = line
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    async def send_test_notification(self) -> bool:
        """Send a test notification to verify configuration"""
        try:
            user_id = self.config.get_user_id()
            user = await self.bot.fetch_user(user_id)

            if not user:
                self.logger.error(f"Could not find user with ID {user_id}")
                return False

            test_message = (
                "🧪 **Discord Member Tracker - Test Notification**\n\n"
                "This is a test notification to verify that your Discord Member Tracker bot is working correctly.\n\n"
                "✅ Bot is online and connected\n"
                "✅ Configuration is loaded\n"
                "✅ Notifications are working\n\n"
                f"**Bot User:** {self.bot.user.name}#{self.bot.user.discriminator}\n"
                f"**Your User ID:** {user_id}\n"
                f"**Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                "The bot is now monitoring your servers for new member joins!"
            )

            await user.send(test_message)
            self.logger.info("Test notification sent successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error sending test notification: {e}")
            return False

    async def send_error_notification(self, error_message: str, context: str = ""):
        """Send error notification to user"""
        try:
            user_id = self.config.get_user_id()
            user = await self.bot.fetch_user(user_id)

            if not user:
                return

            error_msg = (
                "⚠️ **Discord Member Tracker - Error**\n\n"
                f"**Error:** {error_message}\n"
            )

            if context:
                error_msg += f"**Context:** {context}\n"

            error_msg += f"\n**Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"

            await user.send(error_msg)

        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")

    async def send_startup_notification(self, server_count: int):
        """Send notification when bot starts up"""
        try:
            user_id = self.config.get_user_id()
            user = await self.bot.fetch_user(user_id)

            if not user:
                return

            startup_message = (
                "🚀 **Discord Member Tracker - Bot Started**\n\n"
                f"✅ Bot is online and ready\n"
                f"🔔 Notifications: **{self.config.get_notification_method()}**\n"
                f"⚡ Frequency: **{self.config.get_notification_frequency()}**\n\n"
                f"**Started:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                "I'll notify you when new members join your servers!"
            )

            await user.send(startup_message)
            self.logger.info("Startup notification sent")

        except Exception as e:
            self.logger.error(f"Error sending startup notification: {e}")

    async def get_queue_size(self) -> int:
        """Get current notification queue size"""
        return self.notification_queue.qsize()

    async def clear_queue(self):
        """Clear the notification queue"""
        while not self.notification_queue.empty():
            try:
                self.notification_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        self.logger.info("Notification queue cleared")
