# Made by Mister 💛

import json
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger
from datetime import datetime


class Database:
    """JSON-based database handler for the bot"""
    
    def __init__(self, db_path: str = "data/database.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure database file exists with default structure"""
        if not self.db_path.exists():
            default_data = {
                "sessions": {},
                "config": {
                    "typing_speed": "normal",
                    "target_group": None,
                    "admin_id": None
                },
                "conversation": None,
                "simulation_state": {
                    "is_running": False,
                    "is_paused": False,
                    "current_index": 0,
                    "target_group": None
                },
                "statistics": {
                    "messages_sent_today": 0,
                    "total_messages_sent": 0,
                    "last_reset": None
                },
                "groups": {}
            }
            self._write(default_data)
            logger.info(f"Created new database at {self.db_path}")
    
    def _read(self) -> Dict[str, Any]:
        """Read entire database"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading database: {e}")
            return {}
    
    def _write(self, data: Dict[str, Any]):
        """Write entire database"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            logger.debug("Database saved successfully")
        except Exception as e:
            logger.error(f"Error writing database: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key from database"""
        data = self._read()
        return data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set value by key in database"""
        data = self._read()
        data[key] = value
        self._write(data)
        logger.debug(f"Set {key} in database")
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple keys in database"""
        data = self._read()
        data.update(updates)
        self._write(data)
        logger.debug(f"Updated database with {len(updates)} keys")
    
    # Session methods
    def add_session(self, name: str, session_data: Dict[str, Any]):
        """Add or update a session"""
        data = self._read()
        if "sessions" not in data:
            data["sessions"] = {}
        data["sessions"][name] = session_data
        self._write(data)
        logger.info(f"Added/updated session: {name}")
    
    def get_session(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a session by name"""
        sessions = self.get("sessions", {})
        return sessions.get(name)
    
    def get_all_sessions(self) -> Dict[str, Any]:
        """Get all sessions"""
        return self.get("sessions", {})
    
    def remove_session(self, name: str) -> bool:
        """Remove a session by name"""
        data = self._read()
        if "sessions" in data and name in data["sessions"]:
            del data["sessions"][name]
            self._write(data)
            logger.info(f"Removed session: {name}")
            return True
        return False
    
    def update_session_status(self, name: str, status: str):
        """Update session status"""
        session = self.get_session(name)
        if session:
            session["status"] = status
            self.add_session(name, session)
    
    # Configuration methods
    def get_config(self) -> Dict[str, Any]:
        """Get bot configuration"""
        return self.get("config", {})
    
    def update_config(self, updates: Dict[str, Any]):
        """Update bot configuration"""
        config = self.get_config()
        config.update(updates)
        self.set("config", config)
        logger.info(f"Updated config: {updates}")
    
    # Conversation methods
    def set_conversation(self, conversation_data: Dict[str, Any]):
        """Set conversation data"""
        self.set("conversation", conversation_data)
        logger.info("Set conversation data")
    
    def get_conversation(self) -> Optional[Dict[str, Any]]:
        """Get conversation data"""
        return self.get("conversation")
    
    # Simulation state methods
    def get_simulation_state(self) -> Dict[str, Any]:
        """Get simulation state"""
        return self.get("simulation_state", {
            "is_running": False,
            "is_paused": False,
            "current_index": 0,
            "target_group": None
        })
    
    def update_simulation_state(self, updates: Dict[str, Any]):
        """Update simulation state"""
        state = self.get_simulation_state()
        state.update(updates)
        self.set("simulation_state", state)
        logger.debug(f"Updated simulation state: {updates}")
    
    # Statistics methods
    def get_statistics(self) -> Dict[str, Any]:
        """Get bot statistics"""
        return self.get("statistics", {
            "messages_sent_today": 0,
            "total_messages_sent": 0,
            "last_reset": None
        })
    
    def increment_messages_sent(self):
        """Increment message count"""
        stats = self.get_statistics()
        stats["messages_sent_today"] = stats.get("messages_sent_today", 0) + 1
        stats["total_messages_sent"] = stats.get("total_messages_sent", 0) + 1
        self.set("statistics", stats)
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        stats = self.get_statistics()
        stats["messages_sent_today"] = 0
        stats["last_reset"] = datetime.now().isoformat()
        self.set("statistics", stats)
        logger.info("Reset daily statistics")
    
    # Group methods
    def get_all_groups(self) -> Dict[str, Any]:
        """Get all tracked groups"""
        data = self._read()
        if "groups" not in data:
            data["groups"] = {}
            self._write(data)
        return data.get("groups", {})
    
    def add_group(self, group_id: str, group_data: Dict[str, Any]):
        """Add or update a group"""
        data = self._read()
        if "groups" not in data:
            data["groups"] = {}
        data["groups"][group_id] = group_data
        self._write(data)
        logger.info(f"Added/updated group: {group_id}")
    
    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get a group by ID"""
        groups = self.get_all_groups()
        return groups.get(group_id)
    
    def update_group(self, group_id: str, updates: Dict[str, Any]):
        """Update a group's data"""
        group = self.get_group(group_id)
        if group:
            group.update(updates)
            self.add_group(group_id, group)
    
    def remove_group(self, group_id: str) -> bool:
        """Remove a group by ID"""
        data = self._read()
        if "groups" in data and group_id in data["groups"]:
            del data["groups"][group_id]
            self._write(data)
            logger.info(f"Removed group: {group_id}")
            return True
        return False
    
    # Queue methods for short JSON conversations
    def add_to_queue(self, conversation_data: Dict[str, Any], queue_reason: str = ""):
        """Add a conversation to the queue"""
        data = self._read()
        if "conversation_queue" not in data:
            data["conversation_queue"] = []
        
        queue_item = {
            "conversation": conversation_data,
            "queued_at": datetime.now().isoformat(),
            "reason": queue_reason
        }
        data["conversation_queue"].append(queue_item)
        self._write(data)
        logger.info(f"Added conversation to queue (reason: {queue_reason})")
    
    def get_queue(self) -> list:
        """Get all queued conversations"""
        data = self._read()
        return data.get("conversation_queue", [])
    
    def pop_from_queue(self) -> Optional[Dict[str, Any]]:
        """Pop the first conversation from queue"""
        data = self._read()
        queue = data.get("conversation_queue", [])
        if queue:
            item = queue.pop(0)
            data["conversation_queue"] = queue
            self._write(data)
            logger.info("Popped conversation from queue")
            return item.get("conversation")
        return None
    
    def clear_queue(self):
        """Clear the entire queue"""
        data = self._read()
        data["conversation_queue"] = []
        self._write(data)
        logger.info("Cleared conversation queue")
    
    def get_queue_count(self) -> int:
        """Get number of items in queue"""
        return len(self.get_queue())
