# Made by Mister 💛
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

class MediaRepository:
    """The 'Librarian' for the Media Vault (SQLite). Handles media indexing."""
    
    def __init__(self, db_path: str = "data/media.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_tables()
        self._migrate_schema()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _migrate_schema(self):
        """Automatically heals the Vault's structure (Guards against schema mismatch)."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(media_channels)")
            res = cursor.fetchall()
            cols = [c[1] for c in res]
            if 'invite_link' not in cols:
                cursor.execute('ALTER TABLE media_channels ADD COLUMN invite_link TEXT')
                conn.commit()
                logger.info("Migrated Vault: Added invite_link to media_channels")
        except Exception as e: logger.error(f"Migration error: {e}")
        finally: conn.close()
    
    def _init_tables(self):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    channel_username TEXT,
                    invite_link TEXT,
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
            conn.commit()
        except Exception as e:
            logger.error(f"Error initializing media vault: {e}")
            raise
        finally:
            conn.close()

    def add_media_channel(self, channel_id: str, channel_username: Optional[str], items: List[Dict], invite_link: Optional[str] = None) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO media_channels (channel_id, channel_username, media_items, invite_link)
                VALUES (?, ?, ?, ?)
            ''', (channel_id, channel_username, json.dumps(items), invite_link))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_all_channels(self) -> List[Dict]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM media_channels ORDER BY scanned_at DESC')
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def delete_channel(self, channel_db_id: int):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM media_categories WHERE channel_id = ?', (channel_db_id,))
            cursor.execute('DELETE FROM media_channels WHERE id = ?', (channel_db_id,))
            conn.commit()
        finally:
            conn.close()

    def add_category(self, name: str, channel_id: int, ranges: List[List[int]]) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO media_categories (category_name, channel_id, index_ranges, current_pointer)
                VALUES (?, ?, ?, 0)
            ''', (name, channel_id, json.dumps(ranges)))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def delete_category(self, cat_id: int):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM media_categories WHERE id = ?', (cat_id,))
            conn.commit()
        finally:
            conn.close()

    def get_all_categories(self, channel_id: Optional[int] = None) -> List[Dict]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            q = 'SELECT mc.*, ch.channel_username FROM media_categories mc JOIN media_channels ch ON mc.channel_id = ch.id'
            if channel_id: cursor.execute(f"{q} WHERE mc.channel_id = ?", (channel_id,))
            else: cursor.execute(q)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_category_by_tag(self, tag_name: str) -> Optional[Dict]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT mc.*, ch.channel_id AS source_channel_id, ch.invite_link, ch.media_items 
                FROM media_categories mc
                JOIN media_channels ch ON mc.channel_id = ch.id
                WHERE mc.category_name = ?
            ''', (tag_name,))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res["index_ranges"] = json.loads(res["index_ranges"])
                res["media_items"] = json.loads(res["media_items"])
                return res
            return None
        finally:
            conn.close()

    def update_pointer(self, category_id: int, pointer: int):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('UPDATE media_categories SET current_pointer = ? WHERE id = ?', (pointer, category_id))
            conn.commit()
        finally:
            conn.close()
