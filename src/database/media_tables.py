# Made by Mister 💛

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger


class MediaDatabase:
    """SQLite database handler for media simulation features"""
    
    def __init__(self, db_path: str = "data/media.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_tables(self):
        """Initialize database tables"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    channel_username TEXT,
                    media_items JSON NOT NULL,
                    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT NOT NULL,
                    channel_id INTEGER NOT NULL REFERENCES media_channels(id),
                    index_ranges JSON NOT NULL,
                    current_pointer INTEGER DEFAULT 0,
                    UNIQUE(category_name, channel_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
                    media_index INTEGER,
                    status TEXT,
                    attempt_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info(f"Media database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing media database: {e}")
            raise
        finally:
            conn.close()
    
    def add_media_channel(self, channel_id: str, channel_username: Optional[str], 
                          media_items: List[Dict]) -> int:
        """Add a new media channel with scanned items"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO media_channels (channel_id, channel_username, media_items, scanned_at)
                VALUES (?, ?, ?, ?)
            ''', (channel_id, channel_username, json.dumps(media_items), datetime.now().isoformat()))
            conn.commit()
            channel_db_id = cursor.lastrowid
            logger.info(f"Added media channel {channel_username or channel_id} with {len(media_items)} items")
            return channel_db_id
        except Exception as e:
            logger.error(f"Error adding media channel: {e}")
            raise
        finally:
            conn.close()
    
    def get_media_channel(self, channel_db_id: int) -> Optional[Dict]:
        """Get a media channel by database ID"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM media_channels WHERE id = ?', (channel_db_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'channel_id': row['channel_id'],
                    'channel_username': row['channel_username'],
                    'media_items': json.loads(row['media_items']),
                    'scanned_at': row['scanned_at']
                }
            return None
        finally:
            conn.close()
    
    def get_all_media_channels(self) -> List[Dict]:
        """Get all media channels"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM media_channels ORDER BY scanned_at DESC')
            rows = cursor.fetchall()
            return [{
                'id': row['id'],
                'channel_id': row['channel_id'],
                'channel_username': row['channel_username'],
                'media_items': json.loads(row['media_items']),
                'scanned_at': row['scanned_at']
            } for row in rows]
        finally:
            conn.close()
    
    def delete_media_channel(self, channel_db_id: int) -> bool:
        """Delete a media channel and its categories"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM media_categories WHERE channel_id = ?', (channel_db_id,))
            cursor.execute('DELETE FROM media_channels WHERE id = ?', (channel_db_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def add_category(self, category_name: str, channel_id: int, 
                     index_ranges: List[List[int]]) -> int:
        """Add a new media category"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO media_categories 
                (category_name, channel_id, index_ranges, current_pointer)
                VALUES (?, ?, ?, 0)
            ''', (category_name, channel_id, json.dumps(index_ranges)))
            conn.commit()
            category_id = cursor.lastrowid
            logger.info(f"Added category {category_name} with ranges {index_ranges}")
            return category_id
        except Exception as e:
            logger.error(f"Error adding category: {e}")
            raise
        finally:
            conn.close()
    
    def get_category(self, category_name: str, channel_id: int = None) -> Optional[Dict]:
        """Get a category by name (and optionally channel)"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if channel_id:
                cursor.execute('''
                    SELECT * FROM media_categories 
                    WHERE category_name = ? AND channel_id = ?
                ''', (category_name, channel_id))
            else:
                cursor.execute('''
                    SELECT * FROM media_categories WHERE category_name = ?
                ''', (category_name,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'category_name': row['category_name'],
                    'channel_id': row['channel_id'],
                    'index_ranges': json.loads(row['index_ranges']),
                    'current_pointer': row['current_pointer']
                }
            return None
        finally:
            conn.close()
    
    def get_category_by_id(self, category_id: int) -> Optional[Dict]:
        """Get a category by ID"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM media_categories WHERE id = ?', (category_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'category_name': row['category_name'],
                    'channel_id': row['channel_id'],
                    'index_ranges': json.loads(row['index_ranges']),
                    'current_pointer': row['current_pointer']
                }
            return None
        finally:
            conn.close()
    
    def get_all_categories(self, channel_id: int = None) -> List[Dict]:
        """Get all categories, optionally filtered by channel"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if channel_id:
                cursor.execute('''
                    SELECT mc.*, ch.channel_username 
                    FROM media_categories mc
                    JOIN media_channels ch ON mc.channel_id = ch.id
                    WHERE mc.channel_id = ?
                    ORDER BY mc.category_name
                ''', (channel_id,))
            else:
                cursor.execute('''
                    SELECT mc.*, ch.channel_username 
                    FROM media_categories mc
                    JOIN media_channels ch ON mc.channel_id = ch.id
                    ORDER BY mc.category_name
                ''')
            rows = cursor.fetchall()
            return [{
                'id': row['id'],
                'category_name': row['category_name'],
                'channel_id': row['channel_id'],
                'channel_username': row['channel_username'],
                'index_ranges': json.loads(row['index_ranges']),
                'current_pointer': row['current_pointer']
            } for row in rows]
        finally:
            conn.close()
    
    def update_category_pointer(self, category_id: int, new_pointer: int):
        """Update the current pointer for a category"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE media_categories SET current_pointer = ? WHERE id = ?
            ''', (new_pointer, category_id))
            conn.commit()
            logger.debug(f"Updated category {category_id} pointer to {new_pointer}")
        finally:
            conn.close()
    
    def reset_category_pointer(self, category_id: int):
        """Reset the pointer for a category to 0"""
        self.update_category_pointer(category_id, 0)
        logger.info(f"Reset category {category_id} pointer to 0")
    
    def delete_category(self, category_id: int) -> bool:
        """Delete a category"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM media_categories WHERE id = ?', (category_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def log_media_send(self, category_id: int, media_index: int, 
                       status: str, attempt_count: int = 1, 
                       last_error: Optional[str] = None):
        """Log a media send attempt"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO media_logs (category_id, media_index, status, attempt_count, last_error)
                VALUES (?, ?, ?, ?, ?)
            ''', (category_id, media_index, status, attempt_count, last_error))
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging media send: {e}")
        finally:
            conn.close()
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent media logs"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ml.*, mc.category_name 
                FROM media_logs ml
                LEFT JOIN media_categories mc ON ml.category_id = mc.id
                ORDER BY ml.created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [{
                'id': row['id'],
                'category_id': row['category_id'],
                'category_name': row['category_name'],
                'media_index': row['media_index'],
                'status': row['status'],
                'attempt_count': row['attempt_count'],
                'last_error': row['last_error'],
                'created_at': row['created_at']
            } for row in rows]
        finally:
            conn.close()
    
    def get_category_stats(self, category_id: int) -> Dict:
        """Get statistics for a category"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_sends,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped
                FROM media_logs
                WHERE category_id = ?
            ''', (category_id,))
            row = cursor.fetchone()
            return {
                'total_sends': row['total_sends'] or 0,
                'successful': row['successful'] or 0,
                'failed': row['failed'] or 0,
                'skipped': row['skipped'] or 0
            }
        finally:
            conn.close()
