#!/usr/bin/env python3
"""
Fix Duplicate Notifications in Discord Bot Database
This script identifies and removes duplicate notification entries
"""

import asyncio
import sqlite3
import sys
import os
import shutil
from datetime import datetime
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def backup_database(db_path="data/member_joins.db"):
    """Create a backup of the database before making changes"""
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    # Create backups directory if it doesn't exist
    backups_dir = Path("backups")
    backups_dir.mkdir(exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/member_joins_backup_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

async def find_duplicates():
    """Find duplicate notification entries in the database"""
    print("\n🔍 Scanning for duplicate notifications...")
    
    try:
        with sqlite3.connect("data/member_joins.db") as conn:
            # Find duplicates in notifications_sent table
            cursor = conn.execute("""
                SELECT user_id, server_id, COUNT(*) as count
                FROM notifications_sent
                GROUP BY user_id, server_id
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
            """)
            
            notification_duplicates = cursor.fetchall()
            
            # Find duplicates in member_joins table where notification_sent=1
            cursor = conn.execute("""
                SELECT user_id, server_id, COUNT(*) as count
                FROM member_joins
                WHERE notification_sent = 1
                GROUP BY user_id, server_id
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
            """)
            
            join_duplicates = cursor.fetchall()
            
            return notification_duplicates, join_duplicates
            
    except Exception as e:
        print(f"❌ Error scanning for duplicates: {e}")
        return [], []

async def fix_notification_duplicates(duplicates):
    """Fix duplicate entries in notifications_sent table"""
    if not duplicates:
        print("✅ No duplicates found in notifications_sent table")
        return 0
    
    print(f"\n🛠️ Fixing {len(duplicates)} duplicate entries in notifications_sent table...")
    fixed_count = 0
    
    try:
        with sqlite3.connect("data/member_joins.db") as conn:
            for user_id, server_id, count in duplicates:
                print(f"  - User {user_id} in Server {server_id}: {count} duplicates")
                
                # Get all notification IDs for this user/server
                cursor = conn.execute("""
                    SELECT id, notification_timestamp
                    FROM notifications_sent
                    WHERE user_id = ? AND server_id = ?
                    ORDER BY notification_timestamp DESC
                """, (user_id, server_id))
                
                notifications = cursor.fetchall()
                
                # Keep only the most recent notification
                if len(notifications) > 1:
                    # Keep the first one (most recent by our ORDER BY)
                    keep_id = notifications[0][0]
                    
                    # Delete all others
                    delete_ids = [n[0] for n in notifications[1:]]
                    placeholders = ','.join(['?'] * len(delete_ids))
                    conn.execute(f"""
                        DELETE FROM notifications_sent
                        WHERE id IN ({placeholders})
                    """, delete_ids)
                    
                    print(f"    ✅ Kept notification {keep_id}, deleted {len(delete_ids)} duplicates")
                    fixed_count += len(delete_ids)
            
            conn.commit()
        
        return fixed_count
    
    except Exception as e:
        print(f"❌ Error fixing notification duplicates: {e}")
        return 0

async def fix_join_duplicates(duplicates):
    """Fix duplicate entries in member_joins table"""
    if not duplicates:
        print("✅ No duplicates found in member_joins table")
        return 0
    
    print(f"\n🛠️ Fixing {len(duplicates)} duplicate entries in member_joins table...")
    fixed_count = 0
    
    try:
        with sqlite3.connect("data/member_joins.db") as conn:
            for user_id, server_id, count in duplicates:
                print(f"  - User {user_id} in Server {server_id}: {count} duplicates")
                
                # Get all join entries for this user/server where notification_sent=1
                cursor = conn.execute("""
                    SELECT id, join_timestamp
                    FROM member_joins
                    WHERE user_id = ? AND server_id = ? AND notification_sent = 1
                    ORDER BY join_timestamp DESC
                """, (user_id, server_id))
                
                joins = cursor.fetchall()
                
                # Keep only the most recent notification
                if len(joins) > 1:
                    # Keep the first one (most recent by our ORDER BY)
                    keep_id = joins[0][0]
                    
                    # Set notification_sent=0 for all others
                    update_ids = [j[0] for j in joins[1:]]
                    placeholders = ','.join(['?'] * len(update_ids))
                    conn.execute(f"""
                        UPDATE member_joins
                        SET notification_sent = 0
                        WHERE id IN ({placeholders})
                    """, update_ids)
                    
                    print(f"    ✅ Kept join {keep_id}, updated {len(update_ids)} duplicates")
                    fixed_count += len(update_ids)
            
            conn.commit()
        
        return fixed_count
    
    except Exception as e:
        print(f"❌ Error fixing join duplicates: {e}")
        return 0

async def verify_fixes():
    """Verify that all duplicates have been fixed"""
    print("\n🔍 Verifying fixes...")
    
    try:
        with sqlite3.connect("data/member_joins.db") as conn:
            # Check notifications_sent table
            cursor = conn.execute("""
                SELECT COUNT(*) FROM (
                    SELECT user_id, server_id, COUNT(*) as count
                    FROM notifications_sent
                    GROUP BY user_id, server_id
                    HAVING COUNT(*) > 1
                )
            """)
            notification_duplicates = cursor.fetchone()[0]
            
            # Check member_joins table
            cursor = conn.execute("""
                SELECT COUNT(*) FROM (
                    SELECT user_id, server_id, COUNT(*) as count
                    FROM member_joins
                    WHERE notification_sent = 1
                    GROUP BY user_id, server_id
                    HAVING COUNT(*) > 1
                )
            """)
            join_duplicates = cursor.fetchone()[0]
            
            if notification_duplicates == 0 and join_duplicates == 0:
                print("✅ All duplicates have been fixed!")
                return True
            else:
                print(f"⚠️ There are still duplicates: {notification_duplicates} in notifications_sent, {join_duplicates} in member_joins")
                return False
            
    except Exception as e:
        print(f"❌ Error verifying fixes: {e}")
        return False

async def optimize_database():
    """Optimize the database after making changes"""
    print("\n🔧 Optimizing database...")
    
    try:
        with sqlite3.connect("data/member_joins.db") as conn:
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
            print("✅ Database optimized")
            return True
    except Exception as e:
        print(f"❌ Error optimizing database: {e}")
        return False

async def main():
    """Main function to fix duplicate notifications"""
    print("🔧 Discord Bot Database Duplicate Fixer")
    print("=" * 50)
    
    # Backup database first
    if not await backup_database():
        print("❌ Aborting due to backup failure")
        return False
    
    # Find duplicates
    notification_duplicates, join_duplicates = await find_duplicates()
    
    total_duplicates = len(notification_duplicates) + len(join_duplicates)
    if total_duplicates == 0:
        print("\n✅ No duplicates found! Database is already clean.")
    else:
        print(f"\n⚠️ Found {total_duplicates} total duplicate entries")
        
        # Fix duplicates
        fixed_notifications = await fix_notification_duplicates(notification_duplicates)
        fixed_joins = await fix_join_duplicates(join_duplicates)
        
        # Verify fixes
        success = await verify_fixes()
        
        if success:
            # Optimize database
            await optimize_database()
            
            print(f"\n🎉 Successfully fixed {fixed_notifications + fixed_joins} duplicate entries!")
        else:
            print("\n⚠️ Some duplicates could not be fixed. Manual intervention may be required.")
    
    print("\n" + "=" * 50)
    print("✅ Database duplicate fixing process completed!")
    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
