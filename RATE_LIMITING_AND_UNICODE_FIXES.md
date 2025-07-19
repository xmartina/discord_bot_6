# Discord Bot Rate Limiting and Unicode Fixes

## Overview
This document explains the fixes applied to resolve the Discord bot issues where:
1. Bot was getting generic "New Member(s) Online (+X)" instead of actual usernames
2. Unicode encoding errors were occurring in logs (emojis couldn't be displayed)
3. Rate limiting was causing API failures after initial successful calls

## Issues Fixed

### 1. Unicode Encoding Errors
**Problem**: Log messages with emoji characters (🔍, ✅, ❌) were causing UnicodeEncodeError on Windows/AWS servers.

**Solution**:
- Updated logging configuration to use UTF-8 encoding
- Replaced Unicode emojis with ASCII-safe alternatives in logs
- Added proper encoding handlers for both file and console output
- Created encoding environment variables for AWS compatibility

**Files Modified**:
- `src/discord_bot.py` - Updated `setup_logging()` function
- `src/user_client.py` - Replaced emoji characters with ASCII text
- `config.yaml` - Added encoding configuration options

### 2. Rate Limiting Issues
**Problem**: Bot was making too many API calls too quickly, causing Discord to rate limit after the first few successful requests.

**Solution**:
- Implemented proper rate limiting with 2-second delays between API calls
- Added retry logic for 429 (rate limited) responses
- Created `_rate_limit_check()` method to enforce delays
- Increased monitoring interval from 7 to 15 seconds

**Files Modified**:
- `src/user_client.py` - Added rate limiting throughout
- `config.yaml` - Updated performance settings

### 3. Missing User Details
**Problem**: Bot was creating generic notifications instead of fetching actual user information.

**Solution**:
- Created `_try_get_actual_member_details()` method to fetch real user data
- Added fallback methods to get user information via multiple API endpoints
- Implemented proper account age calculation from Discord user IDs
- Enhanced notification creation to use actual usernames when possible

**Files Modified**:
- `src/user_client.py` - Added member detail fetching methods
- Enhanced `_create_count_based_notification()` to use real data

## New Files Created

### 1. `start_bot_aws.sh`
Linux/AWS compatible startup script with proper UTF-8 encoding setup.

**Features**:
- Sets UTF-8 environment variables
- Handles both Linux and Windows virtual environment paths
- Includes proper error handling and cleanup
- Creates necessary directories with proper permissions

### 2. `test_rate_limiting.py`
Comprehensive test script to debug API rate limiting issues.

**Features**:
- Tests user token validity
- Checks API rate limiting behavior
- Verifies guild access permissions
- Tests member data retrieval capabilities
- Saves detailed logs to `logs/rate_limit_test.log`

### 3. `test_rate_limiting.bat`
Windows batch file to run the rate limiting test easily.

## Configuration Changes

### Updated `config.yaml` Settings:
```yaml
user_monitoring:
  check_interval: 15  # Increased from 7 to avoid rate limits
  max_retries: 3
  retry_delay: 5

logging:
  encoding: "utf-8"
  use_ascii_emojis: true
  format: "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"

performance:
  rate_limit_buffer: 2.0  # Increased from 1.0 for AWS stability
  batch_size: 25  # Reduced from 50 to avoid rate limits
  max_concurrent_requests: 5
  request_timeout: 30
  unicode_encoding: "utf-8"
```

## Setup Instructions

### For Windows:
1. Run `setup_windows.bat` (includes all fixes)
2. Configure your tokens in `config.yaml`
3. Test with `test_rate_limiting.bat`
4. Start bot with `start_bot.bat`

### For AWS/Linux:
1. Run `setup_windows.bat` (works on Linux too)
2. Configure your tokens in `config.yaml`
3. Test with `python3 test_rate_limiting.py`
4. Start bot with `./start_bot_aws.sh`

## Troubleshooting

### Still Seeing Generic "New Member(s) Online" Messages?
1. Run the rate limiting test: `test_rate_limiting.bat` or `python3 test_rate_limiting.py`
2. Check if your user token has proper permissions
3. Verify you're not being rate limited by checking logs
4. Ensure the bot has access to guild member information

### Unicode Errors on AWS?
1. Use `./start_bot_aws.sh` instead of the Windows batch files
2. Ensure your terminal supports UTF-8
3. Check that environment variables are properly set

### Rate Limiting Still Occurring?
1. Increase `rate_limit_buffer` in config.yaml to 3.0 or higher
2. Increase `check_interval` to 20-30 seconds
3. Monitor `logs/bot.log` for rate limit warnings

## API Endpoints Used

The bot now uses these Discord API endpoints with proper rate limiting:

1. `/users/@me` - Get user information
2. `/users/@me/guilds` - Get user's guilds
3. `/guilds/{guild_id}?with_counts=true` - Get guild info with member counts
4. `/guilds/{guild_id}/members?limit=X` - Get guild members (when possible)
5. `/guilds/{guild_id}/audit-logs?action_type=1` - Get member join events (when possible)
6. `/channels/{channel_id}/messages?limit=X` - Get channel messages

## Expected Behavior After Fixes

1. **Logs should show**: ASCII-safe messages like `[MONITOR]` instead of emoji errors
2. **Notifications should include**: Actual usernames, account ages, and user details when possible
3. **Rate limiting**: Should see "Rate limiting: waiting X seconds" messages in logs
4. **AWS compatibility**: Should work properly on Linux servers with UTF-8 encoding

## Monitoring Success

Check `logs/bot.log` for these indicators of successful fixes:

```
[INFO] Logging system initialized with UTF-8 encoding support
[INFO] [MONITOR] ENHANCED MONITORING: ServerName - Starting comprehensive detection
[INFO] Rate limiting: waiting 2.00 seconds
[INFO] [METHOD1] (ServerName): SUCCESS approximate_member_count increased: 100 -> 101 (+1)
```

If you see actual usernames in notifications instead of "New Member(s) Online", the member detail fetching is working correctly.

## Contact and Support

If issues persist:
1. Check `logs/bot.log` for detailed error messages
2. Run `test_rate_limiting.py` to verify API access
3. Ensure your user token has appropriate permissions
4. Consider increasing rate limiting delays in config.yaml

The bot now includes comprehensive error handling and should provide clear log messages indicating what's working and what needs attention.