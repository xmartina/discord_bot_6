"""
CLI Manager for Discord Monitoring Bot
Provides command-line interface for bot management
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
import json

# Fix Windows encoding issues
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

from src.config_manager import ConfigManager
from src.database_manager import DatabaseManager

class CLIManager:
    def __init__(self):
        self.config = None
        self.db = None
        self.commands = {
            'status': self.show_status,
            'servers': self.list_servers,
            'stats': self.show_stats,
            'recent': self.show_recent_joins,
            'exclude': self.exclude_server,
            'include': self.include_server,
            'config': self.show_config,
            'test': self.test_notification,
            'backup': self.backup_database,
            'cleanup': self.cleanup_database,
            'help': self.show_help
        }
    
    async def initialize(self):
        """Initialize CLI manager"""
        try:
            self.config = ConfigManager()
            self.db = DatabaseManager(self.config.get_database_config()['path'])
            await self.db.initialize()
            return True
        except Exception as e:
            print(f"Error initializing CLI: {e}")
            return False
    
    async def run_interactive(self):
        """Run interactive CLI mode"""
        print("🤖 Discord Member Monitoring Bot - CLI Manager")
        print("=" * 50)
        print("Type 'help' for available commands or 'exit' to quit")
        print()
        
        while True:
            try:
                command_input = input("bot> ").strip().lower()
                
                if command_input in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                
                if not command_input:
                    continue
                
                # Parse command and arguments
                parts = command_input.split()
                command = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                
                if command in self.commands:
                    await self.commands[command](args)
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")
                
                print()  # Add spacing between commands
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error executing command: {e}")
    
    async def run_command(self, command: str, args: List[str] = None):
        """Run a single command"""
        if args is None:
            args = []
        
        if command in self.commands:
            await self.commands[command](args)
        else:
            print(f"Unknown command: {command}")
            await self.show_help([])
    
    async def show_status(self, args: List[str]):
        """Show bot status"""
        print("📊 Bot Status")
        print("-" * 30)
        
        try:
            # Check configuration
            if self.config.is_configured():
                print("✅ Configuration: Valid")
            else:
                print("❌ Configuration: Invalid (missing token or user ID)")
            
            # Database stats
            db_stats = await self.db.get_database_stats()
            print(f"📁 Database: {db_stats.get('db_size_mb', 0):.2f} MB")
            print(f"🏢 Active Servers: {db_stats.get('active_servers', 0)}")
            print(f"👥 Total Joins Recorded: {db_stats.get('total_joins', 0):,}")
            print(f"🆕 Joins (24h): {db_stats.get('joins_24h', 0)}")
            
            # Configuration summary
            print(f"🔔 Notification Method: {self.config.get_notification_method()}")
            print(f"⚡ Frequency: {self.config.get_notification_frequency()}")
            print(f"🎯 Max Servers: {self.config.get_max_servers()}")
            
        except Exception as e:
            print(f"Error getting status: {e}")
    
    async def list_servers(self, args: List[str]):
        """List monitored servers"""
        print("🏢 Monitored Servers")
        print("-" * 40)
        
        try:
            servers = await self.db.get_all_servers(active_only=True)
            
            if not servers:
                print("No servers found in database")
                return
            
            for server in servers:
                stats = await self.db.get_server_stats(server['id'])
                print(f"📋 {server['name']}")
                print(f"   ID: {server['id']}")
                print(f"   Members: {server.get('member_count', 'Unknown'):,}")
                print(f"   Total Joins: {stats.get('total_joins', 0)}")
                print(f"   Recent (24h): {stats.get('joins_24h', 0)}")
                print(f"   Last Updated: {server.get('last_updated', 'Unknown')}")
                print()
            
        except Exception as e:
            print(f"Error listing servers: {e}")
    
    async def show_stats(self, args: List[str]):
        """Show detailed statistics"""
        print("📈 Detailed Statistics")
        print("-" * 40)
        
        try:
            # Overall stats
            db_stats = await self.db.get_database_stats()
            
            print("📊 Overall Statistics:")
            print(f"   Active Servers: {db_stats.get('active_servers', 0)}")
            print(f"   Total Member Joins: {db_stats.get('total_joins', 0):,}")
            print(f"   Joins (24h): {db_stats.get('joins_24h', 0)}")
            print(f"   Database Size: {db_stats.get('db_size_mb', 0):.2f} MB")
            print()
            
            # Top servers by activity
            print("🔥 Most Active Servers (Last 24h):")
            servers = await self.db.get_all_servers(active_only=True)
            server_activity = []
            
            for server in servers:
                stats = await self.db.get_server_stats(server['id'])
                joins_24h = stats.get('joins_24h', 0)
                if joins_24h > 0:
                    server_activity.append((server['name'], joins_24h))
            
            # Sort by activity
            server_activity.sort(key=lambda x: x[1], reverse=True)
            
            if server_activity:
                for i, (server_name, joins) in enumerate(server_activity[:10], 1):
                    print(f"   {i}. {server_name}: {joins} joins")
            else:
                print("   No recent activity")
            
        except Exception as e:
            print(f"Error showing stats: {e}")
    
    async def show_recent_joins(self, args: List[str]):
        """Show recent member joins"""
        hours = 24
        if args and args[0].isdigit():
            hours = int(args[0])
        
        print(f"👥 Recent Member Joins (Last {hours} hours)")
        print("-" * 50)
        
        try:
            recent_joins = await self.db.get_recent_joins(hours=hours)
            
            if not recent_joins:
                print(f"No member joins in the last {hours} hours")
                return
            
            # Group by server
            servers = {}
            for join in recent_joins:
                server_name = join['server_name']
                if server_name not in servers:
                    servers[server_name] = []
                servers[server_name].append(join)
            
            for server_name, joins in servers.items():
                print(f"🏢 {server_name} ({len(joins)} joins):")
                
                for join in joins[:10]:  # Show first 10
                    username = join['username']
                    join_time = join['join_timestamp']
                    account_age = join.get('account_age_days', 0)
                    
                    # Format timestamp
                    try:
                        dt = datetime.fromisoformat(join_time.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m-%d %H:%M')
                    except:
                        time_str = join_time
                    
                    # Age indicator
                    age_indicator = ""
                    if account_age < 1:
                        age_indicator = " 🚨"
                    elif account_age < 7:
                        age_indicator = " ⚠️"
                    elif join.get('is_bot'):
                        age_indicator = " 🤖"
                    
                    print(f"   • {time_str} - {username}{age_indicator}")
                
                if len(joins) > 10:
                    print(f"   ... and {len(joins) - 10} more")
                print()
            
        except Exception as e:
            print(f"Error showing recent joins: {e}")
    
    async def exclude_server(self, args: List[str]):
        """Exclude a server from monitoring"""
        if not args:
            print("Usage: exclude <server_id>")
            return
        
        try:
            server_id = int(args[0])
            excluded_servers = self.config.get_excluded_servers()
            
            if server_id in excluded_servers:
                print(f"Server {server_id} is already excluded")
                return
            
            # Add to excluded list
            excluded_servers.append(server_id)
            self.config.update_config('servers.excluded_servers', excluded_servers)
            
            # Deactivate in database
            await self.db.deactivate_server(server_id)
            
            print(f"✅ Server {server_id} excluded from monitoring")
            
        except ValueError:
            print("Error: Server ID must be a number")
        except Exception as e:
            print(f"Error excluding server: {e}")
    
    async def include_server(self, args: List[str]):
        """Include a previously excluded server"""
        if not args:
            print("Usage: include <server_id>")
            return
        
        try:
            server_id = int(args[0])
            excluded_servers = self.config.get_excluded_servers()
            
            if server_id not in excluded_servers:
                print(f"Server {server_id} is not excluded")
                return
            
            # Remove from excluded list
            excluded_servers.remove(server_id)
            self.config.update_config('servers.excluded_servers', excluded_servers)
            
            print(f"✅ Server {server_id} included in monitoring")
            print("Note: Server will be automatically added when bot restarts or discovers it")
            
        except ValueError:
            print("Error: Server ID must be a number")
        except Exception as e:
            print(f"Error including server: {e}")
    
    async def show_config(self, args: List[str]):
        """Show current configuration"""
        print("⚙️ Current Configuration")
        print("-" * 40)
        
        try:
            print("🔐 Discord Settings:")
            print(f"   Token: {'✅ Configured' if self.config.get_discord_token() else '❌ Missing'}")
            print(f"   User ID: {self.config.get_user_id()}")
            print()
            
            print("🔔 Notification Settings:")
            print(f"   Method: {self.config.get_notification_method()}")
            print(f"   Frequency: {self.config.get_notification_frequency()}")
            print(f"   Detailed Format: {self.config.is_detailed_format()}")
            print()
            
            print("🏢 Server Settings:")
            print(f"   Monitor All: {self.config.should_monitor_all_servers()}")
            print(f"   Auto Discover: {self.config.is_auto_discover_enabled()}")
            print(f"   Max Servers: {self.config.get_max_servers()}")
            excluded = self.config.get_excluded_servers()
            print(f"   Excluded Servers: {len(excluded)} ({excluded if excluded else 'None'})")
            print()
            
            print("🔍 Filter Settings:")
            print(f"   Min Account Age: {self.config.get_minimum_account_age_days()} days")
            print(f"   Ignore Bots: {self.config.should_ignore_bots()}")
            print()
            
            print("💾 Database Settings:")
            db_config = self.config.get_database_config()
            print(f"   Type: {db_config['type']}")
            print(f"   Path: {db_config['path']}")
            print(f"   Backup Enabled: {db_config['backup_enabled']}")
            
        except Exception as e:
            print(f"Error showing config: {e}")
    
    async def test_notification(self, args: List[str]):
        """Test notification system (placeholder)"""
        print("🧪 Test Notification")
        print("-" * 30)
        print("Note: This feature requires the bot to be running.")
        print("To test notifications, start the bot with: python main.py")
        print("The bot will send a test notification on startup if configured.")
    
    async def backup_database(self, args: List[str]):
        """Create database backup"""
        print("💾 Creating Database Backup")
        print("-" * 30)
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"backups/member_joins_backup_{timestamp}.db"
            
            await self.db.backup_database(backup_path)
            
            # Get backup file size
            if os.path.exists(backup_path):
                size_mb = os.path.getsize(backup_path) / (1024 * 1024)
                print(f"✅ Backup created: {backup_path}")
                print(f"📁 Size: {size_mb:.2f} MB")
            else:
                print("❌ Backup failed - file not created")
            
        except Exception as e:
            print(f"Error creating backup: {e}")
    
    async def cleanup_database(self, args: List[str]):
        """Clean up old database records"""
        days = 90
        if args and args[0].isdigit():
            days = int(args[0])
        
        print(f"🧹 Cleaning Database (keeping last {days} days)")
        print("-" * 40)
        
        try:
            deleted_count = await self.db.cleanup_old_records(days_to_keep=days)
            print(f"✅ Cleaned up {deleted_count} old records")
            
            # Show updated stats
            db_stats = await self.db.get_database_stats()
            print(f"📁 Database size after cleanup: {db_stats.get('db_size_mb', 0):.2f} MB")
            
        except Exception as e:
            print(f"Error cleaning database: {e}")
    
    async def show_help(self, args: List[str]):
        """Show help information"""
        print("🤖 Discord Member Monitoring Bot - CLI Help")
        print("=" * 50)
        print()
        print("Available Commands:")
        print("  status          - Show bot status and configuration")
        print("  servers         - List all monitored servers")
        print("  stats           - Show detailed statistics")
        print("  recent [hours]  - Show recent member joins (default: 24 hours)")
        print("  exclude <id>    - Exclude a server from monitoring")
        print("  include <id>    - Include a previously excluded server")
        print("  config          - Show current configuration")
        print("  test            - Information about testing notifications")
        print("  backup          - Create database backup")
        print("  cleanup [days]  - Clean old records (default: keep 90 days)")
        print("  help            - Show this help message")
        print("  exit/quit       - Exit CLI")
        print()
        print("Examples:")
        print("  recent 48       - Show joins from last 48 hours")
        print("  exclude 123456  - Exclude server with ID 123456")
        print("  cleanup 30      - Keep only last 30 days of records")

async def main():
    """Main CLI function"""
    cli = CLIManager()
    
    if not await cli.initialize():
        print("Failed to initialize CLI manager")
        return
    
    # Check if command was provided as argument
    if len(sys.argv) > 1:
        command = sys.argv[1]
        args = sys.argv[2:] if len(sys.argv) > 2 else []
        await cli.run_command(command, args)
    else:
        # Run interactive mode
        await cli.run_interactive()

if __name__ == "__main__":
    asyncio.run(main())