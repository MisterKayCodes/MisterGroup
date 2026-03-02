# Made by Mister 💛
import json
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger

class BaseRepository:
    """Base class for JSON database handling."""
    def __init__(self, db_path: str = "data/database.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        if not self.db_path.exists():
            default_data = {
                "sessions": {},
                "config": {
                    "typing_speed": "normal",
                    "target_group": None,
                    "admin_id": None,
                    "scheduler_running": False,
                    "automation_interval_hours": 4
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
                "groups": {},
                "conversation_queue": []
            }
            self._write(default_data)

    def _read(self) -> Dict[str, Any]:
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading vault: {e}")
            return {}

    def _write(self, data: Dict[str, Any]):
        try:
            temp_path = self.db_path.with_suffix(".tmp")
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            import os
            os.replace(temp_path, self.db_path)
        except Exception as e:
            logger.error(f"Error writing to vault: {e}")
            if temp_path.exists():
                temp_path.unlink()

    def get(self, key: str, default: Any = None) -> Any:
        data = self._read()
        return data.get(key, default)

    def set(self, key: str, value: Any):
        data = self._read()
        data[key] = value
        self._write(data)
