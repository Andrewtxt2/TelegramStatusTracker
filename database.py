"""
Database manager for persistent storage of messages and bot state
Uses SQLite for reliability and data persistence
"""

import sqlite3
import json
import asyncio
import aiosqlite
from typing import Dict, List, Optional, Any
from datetime import datetime
from logger import setup_logger

class DatabaseManager:
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = db_path
        self.logger = setup_logger()
        self.lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER UNIQUE,
                    chat_id INTEGER,
                    user_id INTEGER,
                    username TEXT,
                    text TEXT,
                    timestamp TEXT,
                    analysis TEXT,
                    status TEXT DEFAULT 'pending',
                    approved_status TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    value TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT,
                    error_message TEXT,
                    stack_trace TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient_id INTEGER,
                    message TEXT,
                    sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'sent'
                )
            """)
            
            # Create indexes for performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_message_id ON messages(message_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_bot_state_key ON bot_state(key)")
            
            await db.commit()
            
        self.logger.info("Database initialized successfully")
        
    async def store_message(self, message_data: Dict[str, Any]) -> bool:
        """Store message in database"""
        async with self.lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("""
                        INSERT OR REPLACE INTO messages 
                        (message_id, chat_id, user_id, username, text, timestamp, analysis, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        message_data['message_id'],
                        message_data['chat_id'],
                        message_data['user_id'],
                        message_data['username'],
                        message_data['text'],
                        message_data['timestamp'],
                        json.dumps(message_data['analysis']),
                        message_data['status']
                    ))
                    
                    await db.commit()
                    
                self.logger.debug(f"Message {message_data['message_id']} stored successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error storing message: {e}")
                return False
                
    async def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Get message by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT * FROM messages WHERE message_id = ?
                """, (message_id,)) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        columns = [description[0] for description in cursor.description]
                        message_data = dict(zip(columns, row))
                        
                        # Parse JSON fields
                        if message_data.get('analysis'):
                            message_data['analysis'] = json.loads(message_data['analysis'])
                            
                        return message_data
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting message: {e}")
            return None
            
    async def update_message_status(self, message_id: int, status: str, approved_status: str = None) -> bool:
        """Update message status"""
        async with self.lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    if approved_status:
                        await db.execute("""
                            UPDATE messages 
                            SET status = ?, approved_status = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE message_id = ?
                        """, (status, approved_status, message_id))
                    else:
                        await db.execute("""
                            UPDATE messages 
                            SET status = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE message_id = ?
                        """, (status, message_id))
                        
                    await db.commit()
                    
                self.logger.debug(f"Message {message_id} status updated to {status}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error updating message status: {e}")
                return False
                
    async def get_messages_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get messages by status"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT * FROM messages WHERE status = ? ORDER BY timestamp DESC
                """, (status,)) as cursor:
                    rows = await cursor.fetchall()
                    
                    messages = []
                    columns = [description[0] for description in cursor.description]
                    
                    for row in rows:
                        message_data = dict(zip(columns, row))
                        if message_data.get('analysis'):
                            message_data['analysis'] = json.loads(message_data['analysis'])
                        messages.append(message_data)
                        
                    return messages
                    
        except Exception as e:
            self.logger.error(f"Error getting messages by status: {e}")
            return []
            
    async def get_message_count(self) -> int:
        """Get total message count"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT COUNT(*) FROM messages") as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else 0
                    
        except Exception as e:
            self.logger.error(f"Error getting message count: {e}")
            return 0
            
    async def get_recent_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT * FROM messages 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,)) as cursor:
                    rows = await cursor.fetchall()
                    
                    messages = []
                    columns = [description[0] for description in cursor.description]
                    
                    for row in rows:
                        message_data = dict(zip(columns, row))
                        if message_data.get('analysis'):
                            message_data['analysis'] = json.loads(message_data['analysis'])
                        messages.append(message_data)
                        
                    return messages
                    
        except Exception as e:
            self.logger.error(f"Error getting recent messages: {e}")
            return []
            
    async def store_bot_state(self, key: str, value: Any) -> bool:
        """Store bot state"""
        async with self.lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("""
                        INSERT OR REPLACE INTO bot_state (key, value, updated_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    """, (key, json.dumps(value)))
                    
                    await db.commit()
                    
                self.logger.debug(f"Bot state '{key}' stored successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error storing bot state: {e}")
                return False
                
    async def get_bot_state(self, key: str) -> Optional[Any]:
        """Get bot state"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT value FROM bot_state WHERE key = ?
                """, (key,)) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        return json.loads(row[0])
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting bot state: {e}")
            return None
            
    async def log_error(self, error_type: str, error_message: str, stack_trace: str = None) -> bool:
        """Log error to database"""
        async with self.lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("""
                        INSERT INTO error_logs (error_type, error_message, stack_trace)
                        VALUES (?, ?, ?)
                    """, (error_type, error_message, stack_trace))
                    
                    await db.commit()
                    
                return True
                
            except Exception as e:
                self.logger.error(f"Error logging error: {e}")
                return False
                
    async def store_notification(self, recipient_id: int, message: str) -> bool:
        """Store notification"""
        async with self.lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("""
                        INSERT INTO notifications (recipient_id, message)
                        VALUES (?, ?)
                    """, (recipient_id, message))
                    
                    await db.commit()
                    
                return True
                
            except Exception as e:
                self.logger.error(f"Error storing notification: {e}")
                return False
                
    async def cleanup_old_data(self, days: int = 30) -> bool:
        """Clean up old data"""
        async with self.lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    # Clean up old messages
                    await db.execute("""
                        DELETE FROM messages 
                        WHERE datetime(timestamp) < datetime('now', '-{} days')
                    """.format(days))
                    
                    # Clean up old error logs
                    await db.execute("""
                        DELETE FROM error_logs 
                        WHERE datetime(timestamp) < datetime('now', '-{} days')
                    """.format(days))
                    
                    # Clean up old notifications
                    await db.execute("""
                        DELETE FROM notifications 
                        WHERE datetime(sent_at) < datetime('now', '-{} days')
                    """.format(days))
                    
                    await db.commit()
                    
                self.logger.info(f"Cleaned up data older than {days} days")
                return True
                
            except Exception as e:
                self.logger.error(f"Error cleaning up old data: {e}")
                return False
