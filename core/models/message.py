# Made by Mister 💛
from dataclasses import dataclass
from typing import Optional
from core.models.enums import MessageType

@dataclass
class Message:
    sender_name: str
    content: str
    message_type: MessageType = MessageType.TEXT
    media_url: Optional[str] = None
    delay_before: float = 1.0
    typing_duration: Optional[float] = None
    
    # Media support from the "Nervous System" or "Vault"
    media_file_id: Optional[str] = None
    media_index: Optional[int] = None
    media_category: Optional[str] = None
    media_group: Optional[str] = None
    
    # Telethon metadata for efficient sending
    media_meta: Optional[dict] = None
