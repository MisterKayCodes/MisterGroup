# Made by Mister 💛
from typing import Dict, Optional, Any
from data.repositories.base_repo import BaseRepository

class SessionRepository(BaseRepository):
    """Memory of Telethon account sessions."""

    def add_session(self, name: str, session_data: Dict[str, Any]):
        data = self._read()
        if "sessions" not in data:
            data["sessions"] = {}
        data["sessions"][name] = session_data
        self._write(data)

    def get_session(self, name: str) -> Optional[Dict[str, Any]]:
        sessions = self.get("sessions", {})
        return sessions.get(name)

    def get_all_sessions(self) -> Dict[str, Any]:
        return self.get("sessions", {})

    def remove_session(self, name: str) -> bool:
        data = self._read()
        if "sessions" in data and name in data["sessions"]:
            del data["sessions"][name]
            self._write(data)
            return True
        return False

    def update_session_status(self, name: str, status: str):
        session = self.get_session(name)
        if session:
            session["status"] = status
            self.add_session(name, session)
