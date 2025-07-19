"""
Setup script for Discord Member Monitoring Bot
Handles initial configuration and setup
"""

import os
import sys
import asyncio
from pathlib import Path
import yaml

def create_directories():
    """Create necessary directories"""
    directories = [
        'data',
        'logs',
        'backups',
        'src'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'discord.py',
        'python-dotenv',
        'aiofiles',
        'aiosqlite',
        'pyyaml',
        'colorama'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_').split('.')[0])
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nPlease install them using:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def setup_configuration():
    """Interactive configuration setup"""
    print("\n🔧 Configuration Setup")
    print("=" * 40)
    
    config_file = "config.yaml"
    
    # Load existing config or create new one
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        print("📄 Found existing configuration file")
    else:
        print("📄 Creating new configuration file")
        # Load default config template
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    
    # Get Discord bot token
    current_token = config.get('discord', {}).get('token', '')
    if current_token == "YOUR_BOT_TOKEN_HERE" or not current_token:
        print("\n🤖 Discord Bot Token Setup")
        print("Please follow the guide in DISCORD_BOT_SETUP_GUIDE.md to create your bot")
        token = input("Enter your Discord bot token: ").strip()
        
        if token:
            config['discord']['token'] = token
            print("✅ Bot token configured")
        else:
            print("⚠️ Bot token not provided - you'll need to update config.yaml manually")
    else:
        print("✅ Bot token already configured")
    
    # Get Discord user ID
    current_user_id = config.get('discord', {}).get('user_id', '')
    if current_user_id == "YOUR_USER_ID_HERE" or not current_user_id:
        print("\n👤 Discord User ID Setup")
        print("To find your Discord User ID:")
        print("1. Enable Developer Mode in Discord Settings > Advanced")
        print("2. Right-click your username and select 'Copy User ID'")
        user_id = input("Enter your Discord user ID: ").strip()
        
        if user_id and user_id.isdigit():
            config['discord']['user_id'] = user_id
            print("✅ User ID configured")
        else:
            print("⚠️ Invalid user ID - you'll need to update config.yaml manually")
    else:
        print("✅ User ID already configured")
    
    # Ask about notification preferences
    print("\n🔔 Notification Preferences")
    current_method = config.get('notifications', {}).get('method', 'discord_dm')
    print(f"Current notification method: {current_method}")
    
    change_notifications = input("Change notification settings? (y/N): ").strip().lower()
    if change_notifications == 'y':
        print("Available notification methods:")
        print("1. discord_dm (recommended)")
        print("2. email (not yet implemented)")
        print("3. webhook (not yet implemented)")
        
        choice = input("Choose method (1-3) [1]: ").strip()
        if choice == '2':
            config['notifications']['method'] = 'email'
        elif choice == '3':
            config['notifications']['method'] = 'webhook'
        else:
            config['notifications']['method'] = 'discord_dm'
        
        # Notification frequency
        print("\nNotification frequency:")
        print("1. instant (recommended)")
        print("2. hourly")
        print("3. daily")
        
        freq_choice = input("Choose frequency (1-3) [1]: ").strip()
        if freq_choice == '2':
            config['notifications']['frequency'] = 'hourly'
        elif freq_choice == '3':
            config['notifications']['frequency'] = 'daily'
        else:
            config['notifications']['frequency'] = 'instant'
    
    # Server monitoring settings
    print("\n🏢 Server Monitoring Settings")
    current_monitor_all = config.get('servers', {}).get('monitor_all', True)
    print(f"Currently monitoring all servers: {current_monitor_all}")
    
    change_servers = input("Change server monitoring settings? (y/N): ").strip().lower()
    if change_servers == 'y':
        monitor_all = input("Monitor all servers you're in? (Y/n): ").strip().lower()
        config['servers']['monitor_all'] = monitor_all != 'n'
        
        if not config['servers']['monitor_all']:
            print("You can exclude specific servers later using the CLI")
        
        max_servers = input(f"Maximum servers to monitor [{config['servers']['max_servers']}]: ").strip()
        if max_servers.isdigit():
            config['servers']['max_servers'] = int(max_servers)
    
    # Filtering options
    print("\n🔍 Filtering Options")
    current_min_age = config.get('filters', {}).get('minimum_account_age_days', 0)
    print(f"Current minimum account age filter: {current_min_age} days")
    
    change_filters = input("Change filtering settings? (y/N): ").strip().lower()
    if change_filters == 'y':
        min_age = input(f"Minimum account age in days (0 = no filter) [{current_min_age}]: ").strip()
        if min_age.isdigit():
            config['filters']['minimum_account_age_days'] = int(min_age)
        
        ignore_bots = input("Ignore bot accounts? (Y/n): ").strip().lower()
        config['filters']['ignore_bots'] = ignore_bots != 'n'
    
    # Save configuration
    try:
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        print(f"\n✅ Configuration saved to {config_file}")
        return True
    except Exception as e:
        print(f"\n❌ Error saving configuration: {e}")
        return False

def test_configuration():
    """Test the configuration"""
    print("\n🧪 Testing Configuration")
    print("=" * 30)
    
    try:
        # Add src to path
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))
        
        from src.config_manager import ConfigManager
        
        config = ConfigManager()
        
        # Test basic configuration
        if config.is_configured():
            print("✅ Configuration is valid")
            print(f"✅ Bot token: Configured")
            print(f"✅ User ID: {config.get_user_id()}")
            print(f"✅ Notification method: {config.get_notification_method()}")
            print(f"✅ Max servers: {config.get_max_servers()}")
            return True
        else:
            print("❌ Configuration is invalid")
            print("Please check your bot token and user ID in config.yaml")
            return False
            
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        return False

def show_next_steps():
    """Show next steps after setup"""
    print("\n🚀 Setup Complete!")
    print("=" * 30)
    print("Next steps:")
    print("1. Make sure your bot is added to all Discord servers you want to monitor")
    print("2. Ensure the bot has the 'SERVER MEMBERS INTENT' enabled in Discord Developer Portal")
    print("3. Start the bot: python main.py")
    print("4. Use the CLI for management: python cli.py")
    print("\nImportant files:")
    print("- main.py: Start the monitoring bot")
    print("- cli.py: Command-line interface for management")
    print("- config.yaml: Configuration file")
    print("- DISCORD_BOT_SETUP_GUIDE.md: Bot setup instructions")
    print("\nFor help and troubleshooting, check the README.md file")

def main():
    """Main setup function"""
    print("🤖 Discord Member Monitoring Bot - Setup")
    print("=" * 50)
    
    # Step 1: Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Step 2: Check requirements
    print("\n📦 Checking requirements...")
    if not check_requirements():
        print("\nSetup cannot continue without required packages.")
        print("Please install requirements and run setup again.")
        return False
    
    # Step 3: Setup configuration
    if not setup_configuration():
        print("\nSetup failed during configuration.")
        return False
    
    # Step 4: Test configuration
    if not test_configuration():
        print("\nConfiguration test failed.")
        print("Please check your settings in config.yaml")
        return False
    
    # Step 5: Show next steps
    show_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nSetup error: {e}")
        sys.exit(1)