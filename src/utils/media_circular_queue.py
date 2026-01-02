# Made by Mister 💛

from typing import Dict, Any, Optional, Tuple, List
from loguru import logger

from src.database.media_tables import MediaDatabase
from src.utils.media_parser import get_indices_from_ranges


def get_next_media_and_advance(
    media_db: MediaDatabase, 
    category_id: int,
    max_retries: int = 2
) -> Optional[Tuple[Dict, int]]:
    """
    Get the next media item for a category and atomically advance the pointer.
    
    This implements the circular queue behavior:
    - Returns the current media item
    - Advances pointer to next position
    - Wraps around to start when reaching end
    
    Args:
        media_db: MediaDatabase instance
        category_id: ID of the category to fetch from
        max_retries: Max retry attempts on failure
    
    Returns:
        Tuple of (media_item, current_index) or None if not found
    """
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        try:
            category = media_db.get_category_by_id(category_id)
            if not category:
                logger.error(f"Category {category_id} not found")
                return None
            
            channel = media_db.get_media_channel(category['channel_id'])
            if not channel:
                logger.error(f"Channel for category {category_id} not found")
                return None
            
            media_items = channel['media_items']
            if not media_items:
                logger.error(f"No media items in channel for category {category_id}")
                return None
            
            indices = get_indices_from_ranges(category['index_ranges'])
            if not indices:
                logger.error(f"No valid indices for category {category_id}")
                return None
            
            current_pointer = category['current_pointer']
            
            if current_pointer >= len(indices):
                current_pointer = 0
            
            target_index = indices[current_pointer]
            
            if target_index >= len(media_items):
                logger.warning(f"Index {target_index} out of range, resetting pointer")
                current_pointer = 0
                target_index = indices[0]
            
            media_item = media_items[target_index]
            
            next_pointer = current_pointer + 1
            if next_pointer >= len(indices):
                next_pointer = 0
                logger.debug(f"Category {category['category_name']} pointer wrapped to start")
            
            media_db.update_category_pointer(category_id, next_pointer)
            
            logger.debug(f"Category {category['category_name']}: returned index {target_index}, pointer now {next_pointer}")
            
            return (media_item, target_index)
            
        except Exception as e:
            attempt += 1
            last_error = str(e)
            logger.warning(f"Attempt {attempt}/{max_retries} failed for category {category_id}: {e}")
    
    logger.error(f"All {max_retries} attempts failed for category {category_id}: {last_error}")
    media_db.log_media_send(category_id, -1, "failed", max_retries, last_error)
    return None


def get_album_items(
    media_db: MediaDatabase,
    channel_id: int,
    start_index: int,
    media_group_id: str
) -> List[Dict]:
    """
    Get all media items that belong to the same album/media group.
    
    Args:
        media_db: MediaDatabase instance
        channel_id: Channel database ID
        start_index: Starting index of the album
        media_group_id: The media group ID to match
    
    Returns:
        List of media items belonging to the album
    """
    channel = media_db.get_media_channel(channel_id)
    if not channel:
        return []
    
    media_items = channel['media_items']
    album_items = []
    
    i = start_index
    while i < len(media_items):
        item = media_items[i]
        if item.get('media_group') == media_group_id:
            album_items.append(item)
            i += 1
        else:
            break
    
    if len(album_items) == 1 and start_index > 0:
        j = start_index - 1
        while j >= 0:
            item = media_items[j]
            if item.get('media_group') == media_group_id:
                album_items.insert(0, item)
                j -= 1
            else:
                break
    
    return album_items


def advance_pointer_for_album(
    media_db: MediaDatabase,
    category_id: int,
    album_size: int
) -> bool:
    """
    Advance the category pointer by album_size (for album sends).
    
    Args:
        media_db: MediaDatabase instance
        category_id: Category ID
        album_size: Number of positions to advance
    
    Returns:
        True if successful
    """
    try:
        category = media_db.get_category_by_id(category_id)
        if not category:
            return False
        
        indices = get_indices_from_ranges(category['index_ranges'])
        current_pointer = category['current_pointer']
        
        new_pointer = current_pointer + album_size
        if new_pointer >= len(indices):
            new_pointer = new_pointer % len(indices)
        
        media_db.update_category_pointer(category_id, new_pointer)
        logger.debug(f"Advanced category {category_id} pointer by {album_size} to {new_pointer}")
        return True
        
    except Exception as e:
        logger.error(f"Error advancing pointer for album: {e}")
        return False


def reset_all_pointers(media_db: MediaDatabase, channel_id: int = None):
    """
    Reset pointers for all categories (optionally filtered by channel).
    
    Args:
        media_db: MediaDatabase instance
        channel_id: Optional channel ID to filter categories
    """
    categories = media_db.get_all_categories(channel_id)
    for cat in categories:
        media_db.reset_category_pointer(cat['id'])
    
    logger.info(f"Reset pointers for {len(categories)} categories")


def get_category_status(media_db: MediaDatabase, category_id: int) -> Dict[str, Any]:
    """
    Get detailed status for a category including pointer position.
    
    Returns:
        Dict with status information
    """
    category = media_db.get_category_by_id(category_id)
    if not category:
        return {"error": "Category not found"}
    
    indices = get_indices_from_ranges(category['index_ranges'])
    current_pointer = category['current_pointer']
    
    stats = media_db.get_category_stats(category_id)
    
    return {
        "category_name": category['category_name'],
        "channel_id": category['channel_id'],
        "total_indices": len(indices),
        "current_pointer": current_pointer,
        "current_index": indices[current_pointer] if current_pointer < len(indices) else 0,
        "is_at_start": current_pointer == 0,
        "is_at_end": current_pointer >= len(indices) - 1,
        "stats": stats
    }
