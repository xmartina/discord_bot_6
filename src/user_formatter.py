"""
User Formatter for Discord Monitoring Bot
Handles formatting of user information for notifications
"""

import discord
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from src.config_manager import ConfigManager

class UserFormatter:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.user_details_config = config.get_user_details_config()

    def calculate_account_age(self, created_at: datetime) -> Dict[str, Any]:
        """Calculate account age from creation date"""
        now = datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        age_delta = now - created_at
        age_days = age_delta.days

        # Calculate years, months, days
        years = age_days // 365
        remaining_days = age_days % 365
        months = remaining_days // 30
        days = remaining_days % 30

        return {
            'total_days': age_days,
            'years': years,
            'months': months,
            'days': days,
            'formatted': self._format_age_string(years, months, days)
        }

    def _format_age_string(self, years: int, months: int, days: int) -> str:
        """Format age into human-readable string"""
        parts = []

        if years > 0:
            parts.append(f"{years} year{'s' if years != 1 else ''}")
        if months > 0:
            parts.append(f"{months} month{'s' if months != 1 else ''}")
        if days > 0 or not parts:  # Show days if it's the only unit or if there are no other units
            parts.append(f"{days} day{'s' if days != 1 else ''}")

        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return f"{', '.join(parts[:-1])}, and {parts[-1]}"

    def extract_user_data(self, member: discord.Member) -> Dict[str, Any]:
        """Extract comprehensive user data from Discord member object"""
        # Calculate account age
        account_age = self.calculate_account_age(member.created_at)

        # Get avatar URL
        avatar_url = None
        if member.avatar:
            avatar_url = member.avatar.url
        elif member.default_avatar:
            avatar_url = member.default_avatar.url

        # Determine verification status
        is_verified = False
        if hasattr(member, 'pending'):
            is_verified = not member.pending

        # Get server-specific information
        server = member.guild

        user_data = {
            'user_id': member.id,
            'username': member.name,
            'display_name': member.display_name,
            'discriminator': member.discriminator if member.discriminator != '0' else None,
            'global_name': getattr(member, 'global_name', None),
            'server_id': server.id,
            'server_name': server.name,
            'join_timestamp': datetime.now(timezone.utc).isoformat(),
            'account_created': member.created_at.isoformat(),
            'account_age_days': account_age['total_days'],
            'account_age_formatted': account_age['formatted'],
            'avatar_url': avatar_url,
            'is_bot': member.bot,
            'is_verified': is_verified,
            'is_system': member.system,
            'raw_data': {
                'mention': member.mention,
                'created_at_timestamp': int(member.created_at.timestamp()),
                'joined_at_timestamp': int(datetime.now(timezone.utc).timestamp()),
                'flags': str(member.public_flags) if hasattr(member, 'public_flags') else None,
                'premium_since': member.premium_since.isoformat() if member.premium_since else None,
                'roles': [role.name for role in member.roles if role.name != '@everyone'],
                'top_role': member.top_role.name if member.top_role.name != '@everyone' else None,
                'status': str(member.status) if hasattr(member, 'status') else None,
                'activity': str(member.activity) if hasattr(member, 'activity') and member.activity else None
            }
        }

        return user_data

    def format_notification_message(self, user_data: Dict[str, Any]) -> str:
        """Format user data into notification message"""
        if not self.config.is_detailed_format():
            return self._format_basic_message(user_data)

        return self._format_detailed_message(user_data)

    def _format_basic_message(self, user_data: Dict[str, Any]) -> str:
        """Format basic notification message"""
        username = user_data.get('username', 'Unknown')
        account_age = user_data.get('account_age_formatted', 'Unknown')
        server_name = user_data.get('server_name', 'Unknown Server')
        
        # Get monitoring source and format it
        source = user_data.get('monitoring_source', '')
        source_text = "(User Monitoring)" if source == "user_monitoring" else ""
        
        # Simple message format - each notification is sent as a separate message
        if source_text:
            return f"{source_text} user {username} with account age {account_age} has joined the server {server_name}"
        else:
            return f"user {username} with account age {account_age} has joined the server {server_name}"

    def _format_detailed_message(self, user_data: Dict[str, Any]) -> str:
        """Format detailed notification message"""
        # Determine monitoring source
        source = user_data.get('monitoring_source', 'bot_monitoring')
        source_emoji = "🤖" if source == "bot_monitoring" else "👤"
        source_text = "Bot Monitoring" if source == "bot_monitoring" else "User Monitoring"

        lines = [f"{source_emoji} **New Member Joined** ({source_text})", ""]

        # Server information
        server_name = user_data.get('server_name', 'Unknown Server')
        server_id = user_data.get('server_id', 'Unknown')
        lines.append(f"**Server:** {server_name} (ID: {server_id})")
        lines.append("")

        # User identification
        if self.user_details_config.get('include_username', True):
            username = user_data.get('username', 'Unknown')
            discriminator = user_data.get('discriminator')
            if discriminator:
                lines.append(f"**Username:** {username}#{discriminator}")
            else:
                lines.append(f"**Username:** {username}")

        if self.user_details_config.get('include_display_name', True):
            display_name = user_data.get('display_name')
            global_name = user_data.get('global_name')
            if display_name and display_name != user_data.get('username'):
                lines.append(f"**Display Name:** {display_name}")
            elif global_name:
                lines.append(f"**Global Name:** {global_name}")

        if self.user_details_config.get('include_user_id', True):
            user_id = user_data.get('user_id', 'Unknown')
            lines.append(f"**User ID:** {user_id}")

        # Account information
        if self.user_details_config.get('include_account_age', True):
            account_age = user_data.get('account_age_formatted', 'Unknown')
            account_created = user_data.get('account_created')
            if account_created:
                try:
                    created_date = datetime.fromisoformat(account_created.replace('Z', '+00:00'))
                    formatted_date = created_date.strftime('%Y-%m-%d %H:%M UTC')
                    lines.append(f"**Account Age:** {account_age}")
                    lines.append(f"**Created:** {formatted_date}")
                except:
                    lines.append(f"**Account Age:** {account_age}")

        if self.user_details_config.get('include_join_date', True):
            join_timestamp = user_data.get('join_timestamp')
            if join_timestamp:
                try:
                    join_date = datetime.fromisoformat(join_timestamp.replace('Z', '+00:00'))
                    formatted_join = join_date.strftime('%Y-%m-%d %H:%M UTC')
                    lines.append(f"**Joined Server:** {formatted_join}")
                except:
                    lines.append(f"**Joined Server:** Just now")

        # Status indicators
        status_indicators = []

        if user_data.get('is_bot', False):
            status_indicators.append("🤖 Bot")

        if user_data.get('is_system', False):
            status_indicators.append("⚙️ System")

        if self.user_details_config.get('include_verification_status', True):
            if user_data.get('is_verified', False):
                status_indicators.append("✅ Verified")
            else:
                status_indicators.append("❌ Unverified")

        # Account age warnings
        account_age_days = user_data.get('account_age_days', 0)
        if account_age_days < 1:
            status_indicators.append("🚨 Brand New Account")
        elif account_age_days < 7:
            status_indicators.append("⚠️ Very New Account")
        elif account_age_days < 30:
            status_indicators.append("🔸 New Account")

        if status_indicators:
            lines.append("")
            lines.append(f"**Status:** {' | '.join(status_indicators)}")

        # Avatar
        if self.user_details_config.get('include_avatar', True):
            avatar_url = user_data.get('avatar_url')
            if avatar_url:
                lines.append("")
                lines.append(f"**Avatar:** {avatar_url}")

        # Additional information
        raw_data = user_data.get('raw_data', {})
        roles = raw_data.get('roles', [])
        if roles:
            lines.append("")
            lines.append(f"**Roles:** {', '.join(roles[:5])}")  # Show first 5 roles
            if len(roles) > 5:
                lines.append(f"*... and {len(roles) - 5} more*")

        # Footer
        lines.append("")
        lines.append("─" * 40)
        lines.append(f"*Monitored by Discord Member Tracker*")

        return "\n".join(lines)

    def format_embed_notification(self, user_data: Dict[str, Any]) -> discord.Embed:
        """Format user data into Discord embed"""
        username = user_data.get('username', 'Unknown')
        display_name = user_data.get('display_name', username)
        server_name = user_data.get('server_name', 'Unknown Server')

        # Determine monitoring source
        source = user_data.get('monitoring_source', 'bot_monitoring')
        source_emoji = "🤖" if source == "bot_monitoring" else "👤"
        source_text = "Bot Monitoring" if source == "bot_monitoring" else "User Monitoring"

        # Create embed
        embed = discord.Embed(
            title=f"{source_emoji} New Member Joined ({source_text})",
            description=f"**{display_name}** joined **{server_name}**",
            color=0x00ff00 if source == "bot_monitoring" else 0x0099ff,  # Green for bot, blue for user
            timestamp=datetime.now(timezone.utc)
        )

        # Add user information
        if self.user_details_config.get('include_username', True):
            discriminator = user_data.get('discriminator')
            if discriminator:
                embed.add_field(name="Username", value=f"{username}#{discriminator}", inline=True)
            else:
                embed.add_field(name="Username", value=username, inline=True)

        if self.user_details_config.get('include_user_id', True):
            user_id = user_data.get('user_id', 'Unknown')
            embed.add_field(name="User ID", value=str(user_id), inline=True)

        if self.user_details_config.get('include_account_age', True):
            account_age = user_data.get('account_age_formatted', 'Unknown')
            embed.add_field(name="Account Age", value=account_age, inline=True)

        # Add status indicators
        status_parts = []
        if user_data.get('is_bot', False):
            status_parts.append("🤖 Bot")
        if user_data.get('is_verified', False):
            status_parts.append("✅ Verified")
        else:
            status_parts.append("❌ Unverified")

        account_age_days = user_data.get('account_age_days', 0)
        if account_age_days < 7:
            status_parts.append("⚠️ New Account")

        if status_parts:
            embed.add_field(name="Status", value=" | ".join(status_parts), inline=False)

        # Add avatar
        avatar_url = user_data.get('avatar_url')
        if avatar_url and self.user_details_config.get('include_avatar', True):
            embed.set_thumbnail(url=avatar_url)

        # Add footer
        embed.set_footer(text=f"Server ID: {user_data.get('server_id', 'Unknown')}")

        return embed

    def should_notify(self, user_data: Dict[str, Any]) -> bool:
        """Check if user should trigger a notification based on filters"""
        try:
            # Check if bots should be ignored
            if self.config.should_ignore_bots() and user_data.get('is_bot', False):
                return False

            # Check minimum account age requirement
            min_age_days = self.config.get_minimum_account_age_days()
            if min_age_days > 0:
                account_age_days = user_data.get('account_age_days', 0)
                if account_age_days < min_age_days:
                    return False

            # Check if system accounts should be ignored
            if self.config.get('filters.ignore_system_messages', True) and user_data.get('is_system', False):
                return False

            # Additional filtering can be added here

            return True

        except Exception as e:
            # If there's an error in filtering, default to notifying
            return True

    def format_summary_report(self, joins_data: list, timeframe: str = "24 hours") -> str:
        """Format multiple joins into a summary report"""
        if not joins_data:
            return f"📊 **Member Join Summary ({timeframe})**\n\nNo new members joined in the last {timeframe}."

        # Group by server
        servers = {}
        for join in joins_data:
            server_name = join.get('server_name', 'Unknown Server')
            if server_name not in servers:
                servers[server_name] = []
            servers[server_name].append(join)

        lines = [f"📊 **Member Join Summary ({timeframe})**", ""]
        lines.append(f"**Total New Members:** {len(joins_data)}")
        lines.append(f"**Servers Affected:** {len(servers)}")
        lines.append("")

        # Add server breakdown
        for server_name, server_joins in servers.items():
            lines.append(f"**{server_name}** ({len(server_joins)} new members)")

            for join in server_joins[:10]:  # Show first 10 members per server
                username = join.get('username', 'Unknown')
                account_age = join.get('account_age_days', 0)
                age_indicator = ""

                if account_age < 1:
                    age_indicator = " 🚨"
                elif account_age < 7:
                    age_indicator = " ⚠️"
                elif join.get('is_bot', False):
                    age_indicator = " 🤖"

                lines.append(f"  • {username}{age_indicator}")

            if len(server_joins) > 10:
                lines.append(f"  *... and {len(server_joins) - 10} more*")

            lines.append("")

        lines.append("─" * 40)
        lines.append("*Generated by Discord Member Tracker*")

        return "\n".join(lines)
