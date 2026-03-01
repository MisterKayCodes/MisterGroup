# Made by Mister 💛
from typing import List, Dict, Optional
from loguru import logger
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

class MediaScanner:
    """The 'Eyes' (services/media/). Interacts with Outside World (Telegram) to scan channels."""
    
    @staticmethod
    async def scan_channel(client, identifier: str, limit: int = 500) -> List[Dict]:
        """Scan a channel for media history using Telethon."""
        media_items = []
        try:
            entity = await client.get_entity(identifier)
            logger.info(f"Scanning media in: {getattr(entity, 'title', identifier)}")
            
            async for message in client.iter_messages(entity, limit=limit):
                if not message.media: continue
                
                item = None
                if isinstance(message.media, MessageMediaPhoto) and message.photo:
                    item = {
                        "file_id": f"photo_{message.photo.id}",
                        "media_id": message.photo.id,
                        "media_type": "photo",
                        "media_group": str(message.grouped_id) if message.grouped_id else None,
                        "message_id": message.id,
                        "access_hash": message.photo.access_hash,
                        "file_reference": message.photo.file_reference.hex() if message.photo.file_reference else None
                    }
                elif isinstance(message.media, MessageMediaDocument) and message.document:
                    mime = message.document.mime_type or ""
                    type_ = "video" if mime.startswith("video/") else "photo" if mime.startswith("image/") else None
                    if not type_: continue
                    
                    item = {
                        "file_id": f"doc_{message.document.id}",
                        "media_id": message.document.id,
                        "media_type": type_,
                        "media_group": str(message.grouped_id) if message.grouped_id else None,
                        "message_id": message.id,
                        "access_hash": message.document.access_hash,
                        "file_reference": message.document.file_reference.hex() if message.document.file_reference else None
                    }
                
                if item: media_items.append(item)
            
            media_items.reverse()
            return media_items
        except Exception as e:
            logger.error(f"Error scanning {identifier}: {e}")
            raise
