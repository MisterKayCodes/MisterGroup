# Made by Mister 💛

import re
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger


def parse_category_ranges(text: str) -> Dict[str, List[List[int]]]:
    """
    Parse category definitions from text.
    
    Expected format:
        BALANCE: 0-20
        DEPOSIT: 21-40
        WITHDRAW: 41-50, 60-70
    
    Returns:
        Dict mapping category names to list of ranges [[start, end], ...]
    """
    categories = {}
    
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or ':' not in line:
            continue
        
        try:
            name, ranges_str = line.split(':', 1)
            name = name.strip().upper()
            ranges_str = ranges_str.strip()
            
            if not name or not ranges_str:
                continue
            
            ranges = []
            for range_part in ranges_str.split(','):
                range_part = range_part.strip()
                if '-' in range_part:
                    parts = range_part.split('-')
                    if len(parts) == 2:
                        start = int(parts[0].strip())
                        end = int(parts[1].strip())
                        if start <= end:
                            ranges.append([start, end])
                        else:
                            logger.warning(f"Invalid range {start}-{end} in category {name}")
                else:
                    idx = int(range_part)
                    ranges.append([idx, idx])
            
            if ranges:
                categories[name] = ranges
                logger.debug(f"Parsed category {name}: {ranges}")
                
        except ValueError as e:
            logger.warning(f"Error parsing line '{line}': {e}")
            continue
    
    return categories


def extract_media_tags(content: str) -> List[str]:
    """
    Extract media tags from message content.
    
    Tags are in format [TAGNAME], e.g., [BALANCE], [DEPOSIT]
    
    Returns:
        List of tag names (without brackets, uppercase)
    """
    pattern = r'\[([A-Za-z_]+)\]'
    matches = re.findall(pattern, content)
    return [m.upper() for m in matches]


def remove_media_tags(content: str) -> str:
    """
    Remove media tags from message content for caption display.
    
    Returns:
        Content with tags removed and cleaned up
    """
    pattern = r'\s*\[[A-Za-z_]+\]\s*'
    cleaned = re.sub(pattern, ' ', content)
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()


def get_indices_from_ranges(ranges: List[List[int]]) -> List[int]:
    """
    Convert range definitions to flat list of indices.
    
    Example:
        [[0, 2], [5, 6]] -> [0, 1, 2, 5, 6]
    """
    indices = []
    for start, end in ranges:
        indices.extend(range(start, end + 1))
    return sorted(indices)


def format_ranges_display(ranges: List[List[int]]) -> str:
    """
    Format ranges for display.
    
    Example:
        [[0, 20], [25, 30]] -> "0-20, 25-30"
    """
    parts = []
    for start, end in ranges:
        if start == end:
            parts.append(str(start))
        else:
            parts.append(f"{start}-{end}")
    return ", ".join(parts)


def find_media_for_category(media_db, category_name: str) -> Optional[Tuple[Dict, int, int]]:
    """
    Find the next media item for a category and return it with index info.
    
    This does NOT advance the pointer - use get_next_media_and_advance for that.
    
    Returns:
        Tuple of (media_item, current_index, category_id) or None if not found
    """
    category = media_db.get_category(category_name)
    if not category:
        logger.warning(f"Category {category_name} not found")
        return None
    
    channel = media_db.get_media_channel(category['channel_id'])
    if not channel:
        logger.warning(f"Channel for category {category_name} not found")
        return None
    
    media_items = channel['media_items']
    if not media_items:
        logger.warning(f"No media items in channel for category {category_name}")
        return None
    
    indices = get_indices_from_ranges(category['index_ranges'])
    if not indices:
        logger.warning(f"No valid indices for category {category_name}")
        return None
    
    current_pointer = category['current_pointer']
    if current_pointer >= len(indices):
        current_pointer = 0
    
    target_index = indices[current_pointer]
    
    if target_index >= len(media_items):
        logger.warning(f"Index {target_index} out of range for media items (max {len(media_items) - 1})")
        return None
    
    media_item = media_items[target_index]
    
    return (media_item, target_index, category['id'])


async def scan_channel_media_aiogram(bot, channel_identifier: str, limit: int = 100) -> List[Dict]:
    """
    Scan a channel for media using Aiogram Bot API.
    
    Note: Bot API has limited history access. For full history, use Telethon.
    
    Args:
        bot: Aiogram Bot instance
        channel_identifier: Channel username (@channel) or ID
        limit: Maximum messages to fetch
    
    Returns:
        List of media item dictionaries
    """
    from aiogram.exceptions import TelegramBadRequest
    
    media_items = []
    
    try:
        if channel_identifier.startswith('@'):
            chat = await bot.get_chat(channel_identifier)
        else:
            chat = await bot.get_chat(int(channel_identifier))
        
        logger.info(f"Scanning channel: {chat.title or chat.username or chat.id}")
        
    except TelegramBadRequest as e:
        logger.error(f"Cannot access channel {channel_identifier}: {e}")
        raise ValueError(f"Cannot access channel: {e}")
    except Exception as e:
        logger.error(f"Error getting channel {channel_identifier}: {e}")
        raise
    
    return media_items


async def scan_channel_media_telethon(client, channel_identifier: str, limit: int = 500) -> List[Dict]:
    """
    Scan a channel for media using Telethon client.
    
    This provides full access to channel history.
    
    Args:
        client: Connected Telethon client
        channel_identifier: Channel username (@channel) or ID
        limit: Maximum messages to fetch
    
    Returns:
        List of media item dictionaries with file_id, media_type, media_group
    """
    from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
    
    media_items = []
    current_group_id = None
    
    try:
        if channel_identifier.startswith('@'):
            entity = await client.get_entity(channel_identifier)
        else:
            entity = await client.get_entity(int(channel_identifier))
        
        logger.info(f"Scanning channel with Telethon: {getattr(entity, 'title', channel_identifier)}")
        
        async for message in client.iter_messages(entity, limit=limit):
            if not message.media:
                continue
            
            media_item = None
            
            if isinstance(message.media, MessageMediaPhoto):
                if message.photo:
                    file_id = f"photo_{message.photo.id}"
                    media_item = {
                        "file_id": file_id,
                        "media_type": "photo",
                        "media_group": str(message.grouped_id) if message.grouped_id else None,
                        "message_id": message.id,
                        "access_hash": message.photo.access_hash,
                        "file_reference": message.photo.file_reference.hex() if message.photo.file_reference else None
                    }
            
            elif isinstance(message.media, MessageMediaDocument):
                if message.document:
                    mime_type = message.document.mime_type or ""
                    if mime_type.startswith("video/"):
                        media_type = "video"
                    elif mime_type.startswith("image/"):
                        media_type = "photo"
                    else:
                        continue
                    
                    file_id = f"doc_{message.document.id}"
                    media_item = {
                        "file_id": file_id,
                        "media_type": media_type,
                        "media_group": str(message.grouped_id) if message.grouped_id else None,
                        "message_id": message.id,
                        "access_hash": message.document.access_hash,
                        "file_reference": message.document.file_reference.hex() if message.document.file_reference else None
                    }
            
            if media_item:
                media_items.append(media_item)
        
        media_items.reverse()
        
        logger.info(f"Found {len(media_items)} media items in channel")
        
    except Exception as e:
        logger.error(f"Error scanning channel with Telethon: {e}")
        raise
    
    return media_items


def inject_media_into_message(message_data: Dict, media_info: Dict) -> Dict:
    """
    Inject media information into a message data structure.
    
    Args:
        message_data: Original message dict
        media_info: Dict with media_file_id, media_type, media_category, media_index
    
    Returns:
        Updated message dict with media fields
    """
    message_data['media_file_id'] = media_info.get('media_file_id')
    message_data['media_type'] = media_info.get('media_type')
    message_data['media_category'] = media_info.get('media_category')
    message_data['media_index'] = media_info.get('media_index')
    message_data['media_group'] = media_info.get('media_group')
    
    if 'content' in message_data:
        message_data['content'] = remove_media_tags(message_data['content'])
    
    return message_data


def process_message_for_media_tags(message_content: str, media_db) -> Optional[Dict]:
    """
    Process a message for media tags and fetch media if found.
    
    This is the main integration point for the text->JSON conversion layer.
    
    Args:
        message_content: The message text to check
        media_db: MediaDatabase instance
    
    Returns:
        Dict with media info if tag found, None otherwise
    """
    tags = extract_media_tags(message_content)
    
    if not tags:
        return None
    
    tag_name = tags[0]
    
    result = find_media_for_category(media_db, tag_name)
    if not result:
        logger.warning(f"No media found for tag [{tag_name}]")
        return None
    
    media_item, media_index, category_id = result
    
    return {
        'media_category': tag_name,
        'media_index': media_index,
        'media_file_id': media_item.get('file_id'),
        'media_type': media_item.get('media_type'),
        'media_group': media_item.get('media_group'),
        'category_id': category_id,
        'message_id': media_item.get('message_id'),
        'access_hash': media_item.get('access_hash'),
        'file_reference': media_item.get('file_reference')
    }


def validate_media_tags_in_messages(messages: List[Dict], media_db) -> Dict[str, Any]:
    """
    Validate that all media tags in messages have corresponding categories set up.
    
    Scans all messages for [TAG] patterns and checks if each tag has a configured
    category in the media database.
    
    Args:
        messages: List of message dicts with 'content' field
        media_db: MediaDatabase instance
    
    Returns:
        Dict with:
            - 'valid': bool - True if all tags have categories
            - 'tags_found': set of all tags found in messages
            - 'missing_categories': set of tags without categories
            - 'configured_categories': set of tags that have categories
            - 'warning_message': formatted warning string (empty if valid)
    """
    all_tags = set()
    
    for msg in messages:
        content = msg.get('content', '')
        tags = extract_media_tags(content)
        all_tags.update(tags)
    
    if not all_tags:
        return {
            'valid': True,
            'tags_found': set(),
            'missing_categories': set(),
            'configured_categories': set(),
            'warning_message': ''
        }
    
    existing_categories = media_db.get_all_categories()
    configured_names = {cat['category_name'].upper() for cat in existing_categories}
    
    missing = all_tags - configured_names
    configured = all_tags & configured_names
    
    warning = ''
    if missing:
        warning = f"⚠️ <b>Media Tag Warning</b>\n\n"
        warning += f"Found {len(missing)} tag(s) without configured categories:\n"
        for tag in sorted(missing):
            warning += f"• [{tag}] — No category set up\n"
        warning += f"\n✅ {len(configured)} tag(s) are configured correctly\n" if configured else ""
        warning += f"\n<i>Messages with unconfigured tags will skip media attachment.</i>\n"
        warning += f"<i>Use 🎬 Media Setup to configure categories.</i>"
    
    return {
        'valid': len(missing) == 0,
        'tags_found': all_tags,
        'missing_categories': missing,
        'configured_categories': configured,
        'warning_message': warning
    }


def validate_scheduled_media_tags(schedule: List[Dict], media_db) -> Dict[str, Any]:
    """
    Validate media tags across all scheduled periods.
    
    Args:
        schedule: List of scheduled period dicts, each with 'messages' list
        media_db: MediaDatabase instance
    
    Returns:
        Same format as validate_media_tags_in_messages
    """
    all_messages = []
    for period in schedule:
        period_messages = period.get('messages', [])
        all_messages.extend(period_messages)
    
    return validate_media_tags_in_messages(all_messages, media_db)
