# Made by Mister 💛

import asyncio
from typing import Optional, Dict, Any, Tuple
from loguru import logger
from telethon import TelegramClient
from telethon.tl.types import InputPhoto, InputDocument

from config import get_config
from src.database.media_tables import MediaDatabase
from src.utils.media_parser import extract_media_tags, remove_media_tags
from src.utils.media_circular_queue import get_next_media_and_advance, get_album_items


class MediaSender:
    """Handles sending media from registered channels during simulation"""
    
    def __init__(self, media_db: MediaDatabase, session_manager=None):
        self.media_db = media_db
        self.session_manager = session_manager
        cfg = get_config()
        self.max_retries = cfg.media.max_retries
        self.retry_delay = cfg.media.retry_delay
    
    def has_media_tags(self, content: str) -> bool:
        """Check if message content contains media tags"""
        tags = extract_media_tags(content)
        return len(tags) > 0
    
    def get_media_tags(self, content: str) -> list:
        """Get all media tags from content"""
        return extract_media_tags(content)
    
    def clean_content(self, content: str) -> str:
        """Remove media tags from content for display as caption"""
        return remove_media_tags(content)
    
    async def get_media_for_tag(self, tag_name: str) -> Optional[Tuple[Dict, int, int]]:
        """
        Get the next media item for a tag/category and advance pointer.
        
        Returns:
            Tuple of (media_item, media_index, category_id) or None
        """
        category = self.media_db.get_category(tag_name)
        if not category:
            logger.warning(f"Category not found for tag: {tag_name}")
            return None
        
        result = get_next_media_and_advance(
            self.media_db, 
            category['id'], 
            self.max_retries
        )
        
        if result:
            media_item, media_index = result
            return (media_item, media_index, category['id'])
        
        return None
    
    async def forward_media_from_channel(
        self,
        client: TelegramClient,
        target_chat_id: int,
        media_item: Dict,
        caption: Optional[str] = None
    ) -> bool:
        """
        Forward/send media from source channel to target chat.
        
        Args:
            client: Telethon client to send with
            target_chat_id: Target chat/group ID
            media_item: Media item dict from database
            caption: Optional caption text
        
        Returns:
            True if successful
        """
        attempt = 0
        last_error = None
        
        while attempt < self.max_retries:
            try:
                message_id = media_item.get('message_id')
                
                if message_id and self.session_manager:
                    source_channel = await self._get_source_channel(media_item)
                    if source_channel:
                        await client.forward_messages(
                            target_chat_id,
                            message_id,
                            source_channel
                        )
                        logger.info(f"Forwarded media message {message_id} to {target_chat_id}")
                        return True
                
                file_id = media_item.get('file_id')
                if file_id:
                    await client.send_message(
                        target_chat_id,
                        caption or "",
                        file=file_id
                    )
                    logger.info(f"Sent media with file_id to {target_chat_id}")
                    return True
                
                logger.error(f"No valid media reference in item: {media_item}")
                return False
                
            except Exception as e:
                attempt += 1
                last_error = str(e)
                logger.warning(f"Media send attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
        
        logger.error(f"All media send attempts failed: {last_error}")
        return False
    
    async def _get_source_channel(self, media_item: Dict) -> Optional[Any]:
        """Get the source channel entity for forwarding"""
        return None
    
    async def send_media_for_message(
        self,
        client: TelegramClient,
        target_chat_id: int,
        message_content: str,
        source_client: Optional[TelegramClient] = None
    ) -> Tuple[bool, str]:
        """
        Process a message for media tags and send media if found.
        
        Args:
            client: Telethon client for sending
            target_chat_id: Target chat ID
            message_content: Original message content with potential tags
            source_client: Optional separate client for fetching from source
        
        Returns:
            Tuple of (media_sent, cleaned_content)
        """
        tags = self.get_media_tags(message_content)
        cleaned_content = self.clean_content(message_content)
        
        if not tags:
            return (False, message_content)
        
        tag_name = tags[0]
        
        media_result = await self.get_media_for_tag(tag_name)
        if not media_result:
            logger.warning(f"No media available for tag [{tag_name}], sending text only")
            return (False, cleaned_content)
        
        media_item, media_index, category_id = media_result
        
        fetch_client = source_client or client
        
        success = await self.send_media_with_caption(
            client,
            fetch_client,
            target_chat_id,
            media_item,
            cleaned_content,
            category_id,
            media_index
        )
        
        return (success, cleaned_content)
    
    async def send_media_with_caption(
        self,
        send_client: TelegramClient,
        fetch_client: TelegramClient,
        target_chat_id: int,
        media_item: Dict,
        caption: str,
        category_id: int,
        media_index: int
    ) -> bool:
        """
        Send media with caption to target chat.
        
        Args:
            send_client: Client to send the message
            fetch_client: Client to fetch media from source
            target_chat_id: Target chat ID
            media_item: Media item dict
            caption: Caption text
            category_id: Category ID for logging
            media_index: Media index for logging
        
        Returns:
            True if successful
        """
        attempt = 0
        
        while attempt < self.max_retries:
            try:
                message_id = media_item.get('message_id')
                category = self.media_db.get_category_by_id(category_id)
                
                if category and message_id:
                    channel = self.media_db.get_media_channel(category['channel_id'])
                    if channel:
                        channel_id = channel['channel_id']
                        channel_name = channel.get('channel_name', '')
                        
                        try:
                            source_entity = None
                            
                            if channel_name and channel_name.startswith('@'):
                                try:
                                    source_entity = await fetch_client.get_entity(channel_name)
                                    logger.debug(f"Resolved channel via username: {channel_name}")
                                except Exception:
                                    pass
                            
                            if not source_entity and channel_name and not channel_name.startswith('@'):
                                try:
                                    source_entity = await fetch_client.get_entity(f"@{channel_name}")
                                    logger.debug(f"Resolved channel via @username: @{channel_name}")
                                except Exception:
                                    pass
                            
                            if not source_entity:
                                try:
                                    full_channel_id = int(f"-100{channel_id}")
                                    source_entity = await fetch_client.get_entity(full_channel_id)
                                    logger.debug(f"Resolved channel via -100 prefix: {full_channel_id}")
                                except Exception:
                                    pass
                            
                            if not source_entity:
                                try:
                                    source_entity = await fetch_client.get_entity(int(channel_id))
                                    logger.debug(f"Resolved channel via raw ID: {channel_id}")
                                except Exception:
                                    pass
                            
                            if not source_entity:
                                logger.warning(f"Could not resolve channel entity for {channel_name or channel_id}")
                                raise Exception(f"Could not resolve channel: {channel_name or channel_id}")
                            
                            source_msg = await fetch_client.get_messages(source_entity, ids=message_id)
                            
                            if source_msg and source_msg.media:
                                await send_client.send_file(
                                    target_chat_id,
                                    source_msg.media,
                                    caption=caption if caption else None
                                )
                                
                                self.media_db.log_media_send(
                                    category_id, media_index, "success", attempt + 1
                                )
                                logger.info(f"Sent media from [{category['category_name']}] index {media_index}")
                                return True
                        except Exception as e:
                            logger.warning(f"Could not fetch from source channel: {e}")
                
                self.media_db.log_media_send(
                    category_id, media_index, "failed", attempt + 1, "No valid media source"
                )
                return False
                
            except Exception as e:
                attempt += 1
                logger.warning(f"Media send attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
        
        self.media_db.log_media_send(
            category_id, media_index, "failed", self.max_retries, "Max retries exceeded"
        )
        return False


def create_media_sender(media_db: MediaDatabase, session_manager=None) -> MediaSender:
    """Factory function to create MediaSender instance"""
    return MediaSender(media_db, session_manager)
