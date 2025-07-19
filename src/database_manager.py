"""
Database Manager for Discord Monitoring Bot
Handles SQLite database operations for member join tracking
"""

import aiosqlite
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: str = "data/member_joins.db"):
        self.db_path = db_path
        self.ensure_directory()

    def ensure_directory(self):
        """Ensure the database directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create servers table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    member_count INTEGER DEFAULT 0,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)

            # Create member_joins table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS member_joins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    display_name TEXT,
                    discriminator TEXT,
                    server_id INTEGER NOT NULL,
                    server_name TEXT NOT NULL,
                    join_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    account_created TIMESTAMP,
                    account_age_days INTEGER,
                    avatar_url TEXT,
                    is_bot BOOLEAN DEFAULT 0,
                    is_verified BOOLEAN DEFAULT 0,
                    notification_sent BOOLEAN DEFAULT 0,
                    raw_data TEXT,
                    FOREIGN KEY (server_id) REFERENCES servers (id)
                )
            """)

            # Create notifications_sent table for tracking sent notifications
            await db.execute("""
                CREATE TABLE IF NOT EXISTS notifications_sent (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    server_id INTEGER NOT NULL,
                    notification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    join_id INTEGER,
                    UNIQUE(user_id, server_id),
                    FOREIGN KEY (join_id) REFERENCES member_joins (id)
                )
            """)

            # Create indexes for better performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_member_joins_user_id ON member_joins(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_member_joins_server_id ON member_joins(server_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_member_joins_timestamp ON member_joins(join_timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_servers_active ON servers(is_active)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_notifications_sent_user_server ON notifications_sent(user_id, server_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_notifications_sent_timestamp ON notifications_sent(notification_timestamp)")

            await db.commit()

    async def add_or_update_server(self, server_id: int, server_name: str, member_count: int = 0):
        """Add or update server information"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO servers (id, name, member_count, last_updated, is_active)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)
            """, (server_id, server_name, member_count))
            await db.commit()

    async def deactivate_server(self, server_id: int):
        """Mark server as inactive (bot left the server)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE servers SET is_active = 0, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (server_id,))
            await db.commit()

    async def record_member_join(self, member_data: Dict[str, Any]) -> int:
        """Record a new member join event"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO member_joins (
                    user_id, username, display_name, discriminator,
                    server_id, server_name, join_timestamp,
                    account_created, account_age_days, avatar_url,
                    is_bot, is_verified, notification_sent, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                member_data['user_id'],
                member_data['username'],
                member_data.get('display_name'),
                member_data.get('discriminator'),
                member_data['server_id'],
                member_data['server_name'],
                member_data.get('join_timestamp', datetime.now(timezone.utc).isoformat()),
                member_data.get('account_created'),
                member_data.get('account_age_days', 0),
                member_data.get('avatar_url'),
                member_data.get('is_bot', False),
                member_data.get('is_verified', False),
                False,  # notification_sent - default to False
                json.dumps(member_data.get('raw_data', {}))
            ))

            join_id = cursor.lastrowid or 0
            await db.commit()
            return join_id

    async def mark_notification_sent(self, join_id: int):
        """Mark that notification was sent for a member join"""
        async with aiosqlite.connect(self.db_path) as db:
            # Update the member_joins table
            await db.execute("""
                UPDATE member_joins SET notification_sent = 1
                WHERE id = ?
            """, (join_id,))

            # Get user_id and server_id from the join record
            async with db.execute("""
                SELECT user_id, server_id FROM member_joins WHERE id = ?
            """, (join_id,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    user_id, server_id = result
                    # Insert or update notification tracking
                    await db.execute("""
                        INSERT OR REPLACE INTO notifications_sent
                        (user_id, server_id, notification_timestamp, join_id)
                        VALUES (?, ?, CURRENT_TIMESTAMP, ?)
                    """, (user_id, server_id, join_id))

            await db.commit()

    async def get_recent_joins(self, hours: int = 24, server_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent member joins within specified hours"""
        query = """
            SELECT * FROM member_joins
            WHERE join_timestamp >= datetime('now', '-{} hours')
        """.format(hours)

        params = []
        if server_id:
            query += " AND server_id = ?"
            params.append(server_id)

        query += " ORDER BY join_timestamp DESC"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_server_stats(self, server_id: int) -> Dict[str, Any]:
        """Get statistics for a specific server"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get server info
            async with db.execute("SELECT * FROM servers WHERE id = ?", (server_id,)) as cursor:
                server_row = await cursor.fetchone()
                if not server_row:
                    return {}

            server_info = dict(server_row)

            # Get join statistics
            async with db.execute("""
                SELECT
                    COUNT(*) as total_joins,
                    COUNT(CASE WHEN join_timestamp >= datetime('now', '-24 hours') THEN 1 END) as joins_24h,
                    COUNT(CASE WHEN join_timestamp >= datetime('now', '-7 days') THEN 1 END) as joins_7d,
                    COUNT(CASE WHEN join_timestamp >= datetime('now', '-30 days') THEN 1 END) as joins_30d
                FROM member_joins WHERE server_id = ?
            """, (server_id,)) as cursor:
                stats_row = await cursor.fetchone()
                stats = dict(stats_row) if stats_row else {}

            return {**server_info, **stats}

    async def get_all_servers(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all servers from database"""
        query = "SELECT * FROM servers"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY name"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def check_duplicate_join(self, user_id: int, server_id: int, within_minutes: int = 5) -> bool:
        """Check if user already joined this server recently (to avoid duplicate notifications)"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check the notifications_sent table first (most reliable)
            async with db.execute("""
                SELECT COUNT(*) FROM notifications_sent
                WHERE user_id = ? AND server_id = ?
                AND notification_timestamp >= datetime('now', '-{} minutes')
            """.format(within_minutes), (user_id, server_id)) as cursor:
                result = await cursor.fetchone()
                if result and result[0] > 0:
                    return True

            # Fallback to checking member_joins table
            async with db.execute("""
                SELECT COUNT(*) FROM member_joins
                WHERE user_id = ? AND server_id = ? AND notification_sent = 1
                AND join_timestamp >= datetime('now', '-{} minutes')
            """.format(within_minutes), (user_id, server_id)) as cursor:
                result = await cursor.fetchone()
                count = result[0] if result else 0
                return count > 0

    async def check_notification_sent(self, user_id: int, server_id: int, within_hours: int = 24) -> bool:
        """Check if we've already sent a notification for this user joining this server recently"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check the notifications_sent table first (most reliable)
            async with db.execute("""
                SELECT COUNT(*) FROM notifications_sent
                WHERE user_id = ? AND server_id = ?
                AND notification_timestamp >= datetime('now', '-{} hours')
            """.format(within_hours), (user_id, server_id)) as cursor:
                result = await cursor.fetchone()
                if result and result[0] > 0:
                    return True

            # Fallback to checking member_joins table
            async with db.execute("""
                SELECT COUNT(*) FROM member_joins
                WHERE user_id = ? AND server_id = ? AND notification_sent = 1
                AND join_timestamp >= datetime('now', '-{} hours')
            """.format(within_hours), (user_id, server_id)) as cursor:
                result = await cursor.fetchone()
                return (result[0] > 0) if result else False

    async def get_user_join_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Get join history for a specific user across all servers"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM member_joins
                WHERE user_id = ?
                ORDER BY join_timestamp DESC
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def cleanup_old_records(self, days_to_keep: int = 90):
        """Clean up old member join records"""
        async with aiosqlite.connect(self.db_path) as db:
            # Clean up old member_joins records
            result1 = await db.execute("""
                DELETE FROM member_joins
                WHERE join_timestamp < datetime('now', '-{} days')
            """.format(days_to_keep))

            # Clean up old notifications_sent records
            result2 = await db.execute("""
                DELETE FROM notifications_sent
                WHERE notification_timestamp < datetime('now', '-{} days')
            """.format(days_to_keep))

            deleted_count = result1.rowcount + result2.rowcount
            await db.commit()
            return deleted_count

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}

            # Total servers
            async with db.execute("SELECT COUNT(*) FROM servers WHERE is_active = 1") as cursor:
                result = await cursor.fetchone()
                stats['active_servers'] = result[0] if result else 0

            # Total member joins
            async with db.execute("SELECT COUNT(*) FROM member_joins") as cursor:
                result = await cursor.fetchone()
                stats['total_joins'] = result[0] if result else 0

            # Recent joins (24h)
            async with db.execute("""
                SELECT COUNT(*) FROM member_joins
                WHERE join_timestamp >= datetime('now', '-24 hours')
            """) as cursor:
                result = await cursor.fetchone()
                stats['joins_24h'] = result[0] if result else 0

            # Database file size
            if os.path.exists(self.db_path):
                stats['db_size_mb'] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            else:
                stats['db_size_mb'] = 0

            return stats

    async def backup_database(self, backup_path: str):
        """Create a backup of the database"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError("Database file not found")

        # Ensure backup directory exists
        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)

        # Create backup using SQLite backup API
        async with aiosqlite.connect(self.db_path) as source:
            async with aiosqlite.connect(backup_path) as backup:
                await source.backup(backup)

    async def close(self):
        """Close database connections (cleanup method)"""
        # SQLite connections are automatically closed when using context managers
        pass
