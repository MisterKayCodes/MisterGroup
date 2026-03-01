# Made by Mister 💛
import re
from typing import Dict, List, Tuple, Any
from core.models.enums import TypingSpeed
from core.calculators.typing_speed import TypingCalculator

class TextParser:
    """The 'Brain' for text conversion. Pure logic."""
    
    @staticmethod
    def parse_conversation_text(text: str, speed: TypingSpeed = TypingSpeed.NORMAL) -> Dict[str, Any]:
        """Parse raw text (Name: Msg) into a conversation structure."""
        lines = text.strip().split('\n')
        messages = []
        
        # Regex: Character Name: Message
        pattern = re.compile(r'^([A-Za-z0-9_\s]+):\s*(.+)$')
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            match = pattern.match(line)
            if match:
                sender_name = match.group(1).strip()
                content = match.group(2).strip()
                
                # Brain calculates delays/typing durations
                delay = TypingCalculator.get_random_delay(speed)
                typing = TypingCalculator.get_random_typing(speed)
                
                messages.append({
                    "sender_name": sender_name,
                    "message_type": "text",
                    "content": content,
                    "delay_before": delay,
                    "typing_duration": typing
                })
        
        if not messages:
            raise ValueError("No valid messages found. Use format: Name: Message")
            
        return {
            "name": f"Converted_{TypingSpeed(speed).name}",
            "mode": "immediate",
            "messages": messages
        }

    @staticmethod
    def parse_txt_batches(text: str, speed: TypingSpeed = TypingSpeed.NORMAL) -> Dict[str, Any]:
        """Parse TXT file with batch separators ---BATCH: Name | HH:MM | repeat--- into scheduled format."""
        lines = text.strip().split('\n')
        schedule = []
        current_batch = None
        current_messages = []
        
        header_pattern = re.compile(
            r'^---BATCH:\s*(.+?)\s*\|\s*(\d{1,2}:\d{2})\s*\|\s*(daily|weekdays|weekends|once)\s*---$',
            re.IGNORECASE
        )
        msg_pattern = re.compile(r'^([A-Za-z0-9_\s]+):\s*(.+)$')
        
        def save_current_batch():
            nonlocal current_batch, current_messages
            if current_batch and current_messages:
                current_batch["messages"] = current_messages
                schedule.append(current_batch)
            current_batch = None
            current_messages = []
            
        for line in lines:
            line = line.strip()
            if not line: continue
            
            batch_match = header_pattern.match(line)
            if batch_match:
                save_current_batch()
                time_str = batch_match.group(2).strip()
                if len(time_str.split(':')[0]) == 1: time_str = '0' + time_str
                
                current_batch = {
                    "time": time_str,
                    "label": batch_match.group(1).strip(),
                    "participants": "all",
                    "repeat": batch_match.group(3).strip().lower(),
                    "enabled": True
                }
                continue
            
            msg_match = msg_pattern.match(line)
            if msg_match and current_batch is not None:
                delay = TypingCalculator.get_random_delay(speed)
                typing = TypingCalculator.get_random_typing(speed)
                current_messages.append({
                    "sender_name": msg_match.group(1).strip(),
                    "content": msg_match.group(2).strip(),
                    "message_type": "text",
                    "delay_before": delay,
                    "typing_duration": typing
                })
        
        save_current_batch()
        if not schedule: raise ValueError("No valid batches found.")
        
        return {
            "name": "TXT_Batch_Import",
            "mode": "scheduled",
            "schedule": schedule
        }
