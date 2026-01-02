# Made by Mister 💛

import re
import random
import json
from typing import Dict, List, Tuple
from loguru import logger


class DelayRange:
    """Delay range configurations"""
    FAST = (3, 9)
    NORMAL = (10, 26)
    SLOW = (27, 50)
    
    @staticmethod
    def get_range(speed: str) -> Tuple[int, int]:
        """Get delay range tuple for given speed"""
        ranges = {
            "fast": DelayRange.FAST,
            "normal": DelayRange.NORMAL,
            "slow": DelayRange.SLOW
        }
        return ranges.get(speed.lower(), DelayRange.NORMAL)
    
    @staticmethod
    def get_random_delay(speed: str) -> float:
        """Get random delay within the specified range"""
        min_delay, max_delay = DelayRange.get_range(speed)
        return round(random.uniform(min_delay, max_delay), 2)
    
    @staticmethod
    def get_random_typing(speed: str) -> float:
        """Get random typing duration within the specified range"""
        min_delay, max_delay = DelayRange.get_range(speed)
        # Typing duration is usually shorter than delay
        return round(random.uniform(min_delay * 0.5, max_delay * 0.7), 2)


def parse_conversation_text(text: str, delay_speed: str = "normal") -> Dict:
    """
    Parse conversation text into JSON format
    
    Expected format:
    Name1: Message content
    Name2: Another message
    
    Or:
    Name1: Did you see that Bitcoin just jumped 11%?
    Name2: Yeah, it's crazy!
    """
    lines = text.strip().split('\n')
    messages = []
    participants = set()
    
    # Regular expression to match "Name: Message" format
    message_pattern = re.compile(r'^([A-Za-z0-9_\s]+):\s*(.+)$')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        match = message_pattern.match(line)
        if match:
            sender_name = match.group(1).strip()
            content = match.group(2).strip()
            
            # Generate random delay and typing duration
            delay = DelayRange.get_random_delay(delay_speed)
            typing_duration = DelayRange.get_random_typing(delay_speed)
            
            messages.append({
                "sender_name": sender_name,
                "message_type": "text",
                "content": content,
                "delay_before": delay,
                "typing_duration": typing_duration
            })
            
            participants.add(sender_name)
            logger.debug(f"Parsed message from {sender_name}: {content[:30]}...")
    
    if not messages:
        raise ValueError("No valid messages found in the text. Please use format: Name: Message")
    
    # Create conversation JSON
    conversation = {
        "name": "Converted Conversation",
        "description": f"Auto-generated from text with {delay_speed} delay range",
        "mode": "immediate",
        "messages": messages
    }
    
    logger.info(f"Parsed {len(messages)} messages from {len(participants)} participants")
    return conversation


def format_conversation_preview(conversation: Dict) -> str:
    """Format conversation for preview"""
    messages = conversation.get("messages", [])
    participants = set(msg["sender_name"] for msg in messages)
    
    delay_info = ""
    if messages:
        min_delay = min(msg.get("delay_before", 0) for msg in messages)
        max_delay = max(msg.get("delay_before", 0) for msg in messages)
        delay_info = f"Delay Range: {min_delay:.1f}s - {max_delay:.1f}s"
    
    preview = f"""
📊 <b>Conversion Preview</b>

<b>Name:</b> {conversation.get("name", "Unknown")}
<b>Participants:</b> {len(participants)} ({", ".join(list(participants)[:5])}{", ..." if len(participants) > 5 else ""})
<b>Total Messages:</b> {len(messages)}
{delay_info}

<b>First 3 messages:</b>
"""
    
    for i, msg in enumerate(messages[:3], 1):
        preview += f"\n{i}. <b>{msg['sender_name']}</b>: {msg['content'][:50]}{'...' if len(msg['content']) > 50 else ''}"
        preview += f"\n   ⏱️ Delay: {msg.get('delay_before', 0):.1f}s, Typing: {msg.get('typing_duration', 0):.1f}s"
    
    if len(messages) > 3:
        preview += f"\n\n... and {len(messages) - 3} more messages"
    
    return preview


def save_conversation_json(conversation: Dict, filename: str = None) -> str:
    """Save conversation to JSON file and return filepath"""
    if filename is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.json"
    
    filepath = f"data/{filename}"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(conversation, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved conversation to {filepath}")
    return filepath


def parse_txt_batches(text: str, delay_speed: str = "normal") -> Dict:
    """
    Parse TXT file with batch separators into scheduled conversation format.
    
    Expected format:
    ---BATCH: Morning Chat | 09:00 | daily---
    Alice: Good morning everyone!
    Bob: Hey, good morning!
    
    ---BATCH: Lunch Break | 12:30 | weekdays---
    Alice: Lunch time!
    Bob: Let's grab some food.
    
    Batch header format: ---BATCH: Label | HH:MM | repeat_pattern---
    repeat_pattern: daily, weekdays, weekends, or once
    """
    lines = text.strip().split('\n')
    schedule = []
    current_batch = None
    current_messages = []
    
    batch_header_pattern = re.compile(
        r'^---BATCH:\s*(.+?)\s*\|\s*(\d{1,2}:\d{2})\s*\|\s*(daily|weekdays|weekends|once)\s*---$',
        re.IGNORECASE
    )
    message_pattern = re.compile(r'^([A-Za-z0-9_\s]+):\s*(.+)$')
    
    def save_current_batch():
        """Save the current batch if it has messages"""
        nonlocal current_batch, current_messages
        if current_batch and current_messages:
            current_batch["messages"] = current_messages
            schedule.append(current_batch)
            logger.debug(f"Saved batch '{current_batch['label']}' with {len(current_messages)} messages")
        current_batch = None
        current_messages = []
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        batch_match = batch_header_pattern.match(line)
        if batch_match:
            save_current_batch()
            
            label = batch_match.group(1).strip()
            time = batch_match.group(2).strip()
            if len(time.split(':')[0]) == 1:
                time = '0' + time
            repeat = batch_match.group(3).strip().lower()
            
            current_batch = {
                "time": time,
                "label": label,
                "participants": "all",
                "repeat": repeat,
                "enabled": True
            }
            logger.debug(f"Found batch header: {label} at {time} ({repeat})")
            continue
        
        msg_match = message_pattern.match(line)
        if msg_match and current_batch is not None:
            sender_name = msg_match.group(1).strip()
            content = msg_match.group(2).strip()
            
            delay = DelayRange.get_random_delay(delay_speed)
            typing_duration = DelayRange.get_random_typing(delay_speed)
            
            current_messages.append({
                "sender_name": sender_name,
                "message_type": "text",
                "content": content,
                "delay_before": delay,
                "typing_duration": typing_duration
            })
    
    save_current_batch()
    
    if not schedule:
        raise ValueError(
            "No valid batches found. Please use format:\n"
            "---BATCH: Label | HH:MM | daily---\n"
            "Name: Message"
        )
    
    total_messages = sum(len(batch.get("messages", [])) for batch in schedule)
    
    conversation = {
        "name": "TXT Batch Upload",
        "description": f"Auto-generated from TXT file with {len(schedule)} scheduled periods",
        "mode": "scheduled",
        "messages": [],
        "schedule": schedule
    }
    
    logger.info(f"Parsed {len(schedule)} batches with {total_messages} total messages from TXT")
    return conversation


def format_txt_batch_preview(conversation: Dict) -> str:
    """Format TXT batch conversion for preview"""
    schedule = conversation.get("schedule", [])
    
    if not schedule:
        return "No batches found."
    
    preview = f"""
📊 <b>TXT Batch Preview</b>

<b>Name:</b> {conversation.get("name", "Unknown")}
<b>Mode:</b> Scheduled
<b>Total Batches:</b> {len(schedule)}
"""
    
    total_messages = 0
    participants = set()
    
    for batch in schedule:
        msgs = batch.get("messages", [])
        total_messages += len(msgs)
        for msg in msgs:
            participants.add(msg.get("sender_name", "Unknown"))
        
        preview += f"\n⏰ <b>{batch.get('time', '??:??')}</b> — {batch.get('label', 'Unnamed')}\n"
        preview += f"   📧 {len(msgs)} messages | {batch.get('repeat', 'daily')}\n"
        
        for msg in msgs[:2]:
            content = msg.get('content', '')[:40]
            if len(msg.get('content', '')) > 40:
                content += "..."
            preview += f"   • <i>{msg.get('sender_name', '?')}:</i> {content}\n"
        
        if len(msgs) > 2:
            preview += f"   <i>...and {len(msgs) - 2} more</i>\n"
    
    preview += f"\n<b>Summary:</b>\n"
    preview += f"• Total Messages: {total_messages}\n"
    preview += f"• Participants: {len(participants)} ({', '.join(list(participants)[:5])}"
    if len(participants) > 5:
        preview += ", ..."
    preview += ")\n"
    
    return preview
