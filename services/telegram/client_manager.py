# Made by Mister 💛
import asyncio
from typing import Dict, Optional, Any
from loguru import logger
from telethon import TelegramClient
from telethon.sessions import StringSession
from data.repositories.session_repo import SessionRepository

class TelegramService:
    """The 'Eyes' and 'Hands'. Interacts with the Outside World (Telegram APIs)."""
    
    def __init__(self, repo: SessionRepository, api_id: int, api_hash: str):
        self.repo = repo
        self.api_id = api_id
        self.api_hash = api_hash
        self.active_clients: Dict[str, TelegramClient] = {}

    async def get_client(self, name: str) -> Optional[TelegramClient]:
        """Get or create connected Telethon client for a session from the Vault."""
        if name in self.active_clients:
            if self.active_clients[name].is_connected():
                return self.active_clients[name]

        session_data = self.repo.get_session(name)
        if not session_data or session_data.get("status") == "paused":
            return None

        try:
            session_str = session_data.get("session_string")
            if not session_str: return None
            
            client = TelegramClient(StringSession(session_str), self.api_id, self.api_hash)
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.error(f"Session {name} is not authorized")
                return None
            
            self.active_clients[name] = client
            return client
        except Exception as e:
            logger.error(f"Error connecting session {name}: {e}")
            return None

    async def test_session(self, name: str) -> Dict[str, Any]:
        """Test if a session is alive and valid. Connection to Outside World."""
        try:
            client = await self.get_client(name)
            if not client:
                return {"success": False, "message": "Failed to connect"}
            
            me = await client.get_me()
            data = {
                "success": True,
                "user_id": me.id,
                "username": me.username,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "phone": me.phone
            }
            return data
        except Exception as e:
            logger.error(f"Error testing session {name}: {e}")
            return {"success": False, "message": str(e)}

    async def disconnect_all(self):
        for name, client in list(self.active_clients.items()):
            try:
                await client.disconnect()
                logger.debug(f"Disconnected client {name}")
            except Exception as e:
                logger.error(f"Error disconnecting client {name}: {e}")
        self.active_clients.clear()
