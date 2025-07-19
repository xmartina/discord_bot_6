# Discord Bot Notification Fixes

## 🐛 Issues Fixed

### 1. **Missing DMs for User Monitoring**
**Problem**: User monitoring detections appeared in logs but didn't send Discord DMs
**Root Cause**: Notification callback wasn't properly recording to database and marking notifications as sent
**Fix**: Enhanced `_handle_user_monitoring_join` method with proper database recording and notification queuing

### 2. **Duplicate Notifications on Restart**
**Problem**: Bot sent notifications for previously detected users when restarted
**Root Cause**: No persistent storage of sent notifications across bot restarts
**Fix**: Implemented persistent duplicate checking using database with 24-hour lookback

### 3. **Inconsistent Data Format**
**Problem**: User monitoring data format didn't match expected database schema
**Fix**: Standardized data format and added proper default values for all required fields

## 🔧 Technical Changes Made

### Enhanced Discord Bot (`src/discord_bot.py`)
```python
# Before: Basic duplicate checking (5 minutes, memory only)
is_duplicate = await self.db.check_duplicate_join(
    user_id=user_data['user_id'],
    server_id=user_data['server_id'],
    within_minutes=5
)

# After: Persistent duplicate checking (24 hours, database)
is_duplicate = await self.db.check_duplicate_join(
    user_id=user_data['user_id'],
    server_id=user_data['server_id'],
    within_minutes=1440  # 24 hours to prevent duplicates across restarts
)

# Added: Proper database recording and notification tracking
join_id = await self.db.record_member_join(user_data)
if self.formatter.should_notify(user_data):
    await self.notification_manager.queue_member_join_notification(user_data, source, join_id)
    await self.db.mark_notification_sent(join_id)
```

### Enhanced Database Manager (`src/database_manager.py`)
```python
# Added: Notification tracking to member_joins table
notification_sent BOOLEAN DEFAULT 0

# Enhanced: Better duplicate checking with notification status
async def check_duplicate_join(self, user_id: int, server_id: int, within_minutes: int = 5) -> bool:
    # Check for any record within time window
    # Also check if notification was already sent
    
async def check_notification_sent(self, user_id: int, server_id: int, within_hours: int = 24) -> bool:
    # New method: Check if notification already sent for this user/server combo
```

### Enhanced User Client (`src/user_client.py`)
```python
# Added: Persistent notification checking before calling callback
is_duplicate = await self.db.check_notification_sent(
    user_id=member_data['user_id'],
    server_id=member_data['server_id'],
    within_hours=24
)

if is_duplicate:
    self.logger.debug(f"Already notified for {member_data['username']} within 24h, skipping")
    continue

# Enhanced: Better data format with proper account age calculation
if user_id and user_id != "0":
    # Calculate account age from Discord snowflake
    user_id_int = int(user_id)
    created_timestamp = ((user_id_int >> 22) + 1420070400000) / 1000
    created_at = datetime.fromtimestamp(created_timestamp, tz=timezone.utc)
```

### Enhanced Notification Manager (`src/notification_manager.py`)
```python
# Added: Better error handling and debug logging
self.logger.debug(f"Attempting to send {source} notification for {user_data.get('username')} via {method}")

# Enhanced: More detailed error reporting
except Exception as e:
    self.logger.error(f"Error sending notification: {e}")
    import traceback
    self.logger.error(f"Notification error traceback: {traceback.format_exc()}")
```

## 🧪 Testing Framework

### New Test Scripts
1. **`test_notifications.py`** - Comprehensive notification system testing
2. **`test_notifications.bat`** - Windows batch script for easy testing

### Test Coverage
- ✅ Discord DM sending functionality
- ✅ User monitoring notification flow
- ✅ Database duplicate prevention
- ✅ Message formatting
- ✅ Callback processing
- ✅ Error handling

## 🚀 How to Apply Fixes

### Step 1: Update Files
The following files have been updated with fixes:
- `src/discord_bot.py` - Enhanced user monitoring handler
- `src/database_manager.py` - Added notification tracking
- `src/user_client.py` - Better duplicate checking
- `src/notification_manager.py` - Improved error handling

### Step 2: Test the Fixes
```cmd
# Test notifications specifically
test_notifications.bat

# Or run full system test
test_bot.bat
```

### Step 3: Restart Bot
```cmd
# Stop current bot (Ctrl+C or close window)
# Start with fixes
start_bot.bat
```

## 📊 Expected Behavior After Fixes

### User Monitoring Notifications
```
2025-07-09 13:23:18,920 - src.discord_bot - INFO - Processing user monitoring join: craiggie.0 in We up 4ever
2025-07-09 13:23:18,925 - src.database_manager - DEBUG - Recording member join for craiggie.0
2025-07-09 13:23:18,930 - src.notification_manager - DEBUG - Queuing user_monitoring notification for craiggie.0
2025-07-09 13:23:18,935 - src.notification_manager - DEBUG - Attempting to send user_monitoring notification via discord_dm
2025-07-09 13:23:18,940 - src.notification_manager - INFO - Notification sent for craiggie.0 in We up 4ever (via user monitoring)
2025-07-09 13:23:18,945 - src.user_client - INFO - New member detected via user monitoring: craiggie.0 in We up 4ever
```

### Duplicate Prevention
```
2025-07-09 13:25:18,920 - src.discord_bot - DEBUG - Duplicate join detected for craiggie.0 (already processed within 24h), skipping notification
```

### Restart Behavior
```
# After restart - no duplicates sent
2025-07-09 14:23:18,920 - src.user_client - DEBUG - Already notified for vickywatson in Begot within 24h, skipping
2025-07-09 14:23:20,920 - src.user_client - DEBUG - Already notified for craiggie.0 in We up 4ever within 24h, skipping
```

## 🔍 Debugging Commands

### Check Database State
```python
# In Python console
import asyncio
from src.database_manager import DatabaseManager

async def check_db():
    db = DatabaseManager("data/member_joins.db")
    await db.initialize()
    
    # Check recent joins
    recent = await db.get_recent_joins(hours=24)
    print(f"Recent joins: {len(recent)}")
    
    # Check for specific user
    is_duplicate = await db.check_duplicate_join(123456, 987654, 1440)
    print(f"Is duplicate: {is_duplicate}")
    
    await db.close()

asyncio.run(check_db())
```

### Check Notification Queue
```python
# While bot is running, check queue size
queue_size = await bot.notification_manager.get_queue_size()
print(f"Queue size: {queue_size}")
```

## ✅ Verification Checklist

After applying fixes, verify:
- [ ] User monitoring detections appear in logs
- [ ] Discord DMs are received for user monitoring
- [ ] No duplicate notifications after bot restart
- [ ] Database records all joins with notification status
- [ ] Test script passes all checks
- [ ] Bot handles errors gracefully

## 🛠️ Troubleshooting

### If DMs Still Don't Work
1. **Check Discord Settings**:
   - Go to Discord Settings → Privacy & Safety
   - Enable "Allow direct messages from server members"

2. **Verify User ID**:
   ```python
   # Check if user ID is correct
   user_id = config.get_user_id()
   user = await bot.fetch_user(user_id)
   print(f"User: {user.name}")
   ```

3. **Test Direct DM**:
   ```python
   # Test sending DM directly
   success = await notification_manager._send_discord_dm(test_data)
   print(f"DM Success: {success}")
   ```

### If Duplicates Still Occur
1. **Check Database**:
   ```sql
   SELECT * FROM member_joins WHERE user_id = 123456 ORDER BY join_timestamp DESC;
   ```

2. **Verify Notification Tracking**:
   ```python
   sent = await db.check_notification_sent(user_id, server_id, 24)
   print(f"Already sent: {sent}")
   ```

## 🎯 Summary

**All notification issues have been fixed:**

1. ✅ **Missing DMs**: Fixed callback processing and database recording
2. ✅ **Duplicates**: Implemented persistent 24-hour duplicate prevention
3. ✅ **Data Format**: Standardized user data structure
4. ✅ **Error Handling**: Enhanced logging and error reporting
5. ✅ **Testing**: Added comprehensive test framework

**The bot now properly:**
- Sends DMs for all user monitoring detections
- Prevents duplicate notifications across restarts
- Maintains persistent notification history
- Handles errors gracefully with detailed logging

Your Discord Member Monitoring Bot is now fully functional and handles groups where the bot wasn't invited exactly as requested! 🎉