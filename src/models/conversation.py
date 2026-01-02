# Made by Mister 💛

from enum import Enum
from typing import Optional, List, Union
from pydantic import BaseModel, Field, field_validator


class MessageType(str, Enum):
    """Type of message in conversation"""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    VOICE = "voice"
    DOCUMENT = "document"
    STICKER = "sticker"


class Message(BaseModel):
    """Model for a single message in conversation"""
    sender_name: str = Field(..., description="Name of the sender (matches session name)")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Type of message")
    content: str = Field(..., description="Message text content")
    media_url: Optional[str] = Field(None, description="URL or path to media file")
    delay_before: float = Field(default=1.0, description="Delay in seconds before sending this message")
    typing_duration: Optional[float] = Field(None, description="Custom typing duration for this message")
    
    class Config:
        use_enum_values = True


class ScheduledPeriod(BaseModel):
    """Model for a scheduled conversation period"""
    time: str = Field(..., description="Time in HH:MM format (24-hour)")
    label: str = Field(..., description="Label for this period (e.g., 'Morning Crew', 'Evening Chat')")
    participants: Union[List[str], str] = Field(..., description="List of participant names or 'all' for everyone")
    messages: List[Message] = Field(default_factory=list, description="Messages for this period")
    repeat: str = Field(default="daily", description="Repeat pattern: 'daily', 'weekdays', 'weekends', or 'once'")
    enabled: bool = Field(default=True, description="Whether this scheduled period is active")
    
    @field_validator('time')
    @classmethod
    def validate_time_format(cls, v):
        """Validate time is in HH:MM format"""
        try:
            parts = v.split(':')
            if len(parts) != 2:
                raise ValueError("Time must be in HH:MM format")
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid hour or minute")
            return v
        except (ValueError, AttributeError):
            raise ValueError("Time must be in HH:MM format (e.g., '08:00', '14:30')")
    
    class Config:
        use_enum_values = True


class ConversationData(BaseModel):
    """Model for conversation data - supports both flat and scheduled formats"""
    name: str = Field(..., description="Name of the conversation")
    description: Optional[str] = Field(None, description="Description of the conversation")
    
    # Flat format (original) - list of messages run immediately
    messages: List[Message] = Field(default_factory=list, description="List of messages (flat/immediate mode)")
    
    # Scheduled format - list of time periods with their own messages
    schedule: List[ScheduledPeriod] = Field(default_factory=list, description="Scheduled periods with times")
    
    # Mode indicator
    mode: str = Field(default="immediate", description="Mode: 'immediate' for flat messages, 'scheduled' for time-based")
    
    def is_scheduled(self) -> bool:
        """Check if this conversation uses scheduled mode"""
        return len(self.schedule) > 0 or self.mode == "scheduled"
    
    def get_all_messages(self) -> List[Message]:
        """Get all messages regardless of mode (for preview)"""
        if self.schedule:
            all_msgs = []
            for period in self.schedule:
                all_msgs.extend(period.messages)
            return all_msgs
        return self.messages
    
    def get_total_message_count(self) -> int:
        """Get total message count across all periods"""
        if self.schedule:
            return sum(len(p.messages) for p in self.schedule)
        return len(self.messages)
    
    def get_participants(self) -> set:
        """Get all unique participants"""
        participants = set()
        for msg in self.get_all_messages():
            participants.add(msg.sender_name)
        return participants
    
    class Config:
        use_enum_values = True
