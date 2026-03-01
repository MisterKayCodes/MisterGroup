# Made by Mister 💛
from typing import Dict, Any, Optional
from data.repositories.base_repo import BaseRepository

class ConfigRepository(BaseRepository):
    """The 'Blueprint' of the bot's configuration."""

    def get_config(self) -> Dict[str, Any]:
        return self.get("config", {})

    def update_config(self, updates: Dict[str, Any]):
        config = self.get_config()
        config.update(updates)
        self.set("config", config)

    def get_conversation(self) -> Optional[Dict[str, Any]]:
        return self.get("conversation")

    def set_conversation(self, conversation_data: Optional[Dict[str, Any]]):
        self.set("conversation", conversation_data)

    def get_queue(self) -> list:
        return self.get("conversation_queue", [])

    def add_to_queue(self, conversation_data: Dict[str, Any], reason: str = ""):
        data = self._read()
        if "conversation_queue" not in data:
            data["conversation_queue"] = []
        
        from datetime import datetime
        queue_item = {
            "conversation": conversation_data,
            "queued_at": datetime.now().isoformat(),
            "reason": reason
        }
        data["conversation_queue"].append(queue_item)
        self._write(data)

    def pop_from_queue(self) -> Optional[Dict[str, Any]]:
        data = self._read()
        queue = data.get("conversation_queue", [])
        if queue:
            item = queue.pop(0)
            data["conversation_queue"] = queue
            self._write(data)
            return item.get("conversation")
        return None

    def is_user_authenticated(self, user_id: int) -> bool:
        """Check if a specific user has passed the PIN guard (Persistent)."""
        data = self._read()
        auth_list = data.get("authenticated_users", [])
        return user_id in auth_list

    def set_user_authenticated(self, user_id: int, status: bool = True):
        """Authorize or de-authorize a user."""
        data = self._read()
        if "authenticated_users" not in data:
            data["authenticated_users"] = []
        
        if status and user_id not in data["authenticated_users"]:
            data["authenticated_users"].append(user_id)
        elif not status and user_id in data["authenticated_users"]:
            data["authenticated_users"].remove(user_id)
        
        self._write(data)

    def get_last_automation_hour(self) -> int:
        """Fetch the hour of the last successful news automation run."""
        conf = self.get_config()
        return conf.get("last_automation_hour", -1)

    def set_last_automation_hour(self, hour: int):
        """Record the hour of a successful news automation run."""
        self.update_config({"last_automation_hour": hour})
